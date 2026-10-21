# efficient sorted index finder for locating replay samples
from bisect import bisect_right
from time import perf_counter

import pygame
import projectile
import walls

class ReplaySystem:
    def __init__(
        self,
        player1_positions,
        player2_positions,
        projectile_events=None,
        round_end_times=None,
        area_events=None,
        area_damage_state=None,
        walls=None,
    ):
        # format the track
        # player tracks
        self.tracks = [
            self.prepare_track(player1_positions),
            self.prepare_track(player2_positions),
        ]
        # sort projectile events based on timestamp
        self.projectile_events = sorted(
            projectile_events or [],
            key=lambda event: event["timestamp"],
        )
        # get duration from the player recordings
        self.duration = max(
            [times[-1] for times, states in self.tracks if times],
            default=0.0,
        )
        # round boundaries are metadata because effects continue through them
        self.round_end_times = sorted(round_end_times or [self.duration])
        self.walls = walls or []
        # carried areas use negative start times to restore elapsed lifetime
        self.area_events = area_events or []
        area_damage_state = area_damage_state or {}
        self.initial_area_damage_cooldowns = {
            1: area_damage_state.get("cooldowns", {}).get(1, 0.0),
            2: area_damage_state.get("cooldowns", {}).get(2, 0.0),
        }
        self.initial_players_touching_area = {
            1: area_damage_state.get("touching", {}).get(1, False),
            2: area_damage_state.get("touching", {}).get(2, False),
        }
        # safe set start time value
        self.start_time = None
        # replay effect variables
        self.last_time = 0.0
        self.reset_effects()

    # formats the track into two different elements of times and states
    def prepare_track(self, positions):
        # retrieve position entries
        samples = sorted(positions.items())
        # separate the times and states
        times = [timestamp for timestamp, state in samples]
        states = [tuple(state) for timestamp, state in samples]
        return times, states

    # simple linear interpolation function
    def lerp(self, start, end, alpha):
        # simple linear interpolate function
        return start + (end - start) * alpha

    # reset projectiles, carried areas, and their damage state
    def reset_effects(self):
        self.projectile_index = 0
        self.active_projectiles = []
        self.active_areas = []

        for event in self.area_events:
            area = projectile.create_area(
                event.get("area_type", projectile.PotionArea.TYPE),
                event["position"],
                event["owner"],
                event["start_time"],
                event.get("damage_applied", False),
                event.get("visual_variant"),
            )
            area.set_time(0.0)
            if area.alive:
                self.active_areas.append(area)

        # next replay time each player is allowed to take area damage
        self.area_damage_cooldowns = (
            self.initial_area_damage_cooldowns.copy()
        )
        # remember if each player was touching an area at the prior cutoff
        self.players_touching_area = (
            self.initial_players_touching_area.copy()
        )
        self.last_time = 0.0

    # initiates the recording clock
    def restart(self):
        self.start_time = perf_counter()
        # reset replay effects
        self.reset_effects()

    # update projectile function
    def update_projectiles(self, current_time, player1, player2):
        # reset if the replay time moves backwards
        if current_time < self.last_time:
            self.reset_effects()

        # create projectiles once their timestamp is reached
        while (self.projectile_index < len(self.projectile_events) and self.projectile_events[self.projectile_index]["timestamp"] <= current_time):
            event = self.projectile_events[self.projectile_index]
            potion_obj = projectile.create_projectile(
                event["potion_type"],
                event["original"],
                event["target"],
                event["player_number"],
                event.get("visual_variant"),
            )
            potion_obj.aim_target = pygame.Vector2(
                event.get("aim_target", event["target"])
            )
            # explicit elapsed time preserves partial charges across rounds
            event_time = event["timestamp"]
            potion_obj.replay_elapsed_offset = event.get(
                "elapsed",
                max(0.0, -event_time),
            )
            throw_time = max(0.0, event_time)
            # store throw time, owner, and potion object
            self.active_projectiles.append(
                (
                    throw_time,
                    event["player_number"],
                    potion_obj,
                )
            )
            self.projectile_index += 1

        # update projectiles and create areas when they break
        still_active = []
        for throw_time, owner, potion_obj in self.active_projectiles:
            # add saved progress before advancing through the new round
            projectile_elapsed = (
                potion_obj.replay_elapsed_offset
                + current_time
                - throw_time
            )
            if projectile_elapsed < potion_obj.charge_time:
                # keep the real launch origin on the nozzle while charging
                firing_player = player1 if owner == 1 else player2
                new_original = firing_player.get_projectile_origin()
                clearance = (
                    projectile.CannonBall.RADIUS
                    if potion_obj.type == "cannon"
                    else 0
                )
                potion_obj.target.update(
                    walls.get_blocked_target(
                        new_original,
                        potion_obj.aim_target,
                        self.walls,
                        clearance,
                    )
                )
                potion_obj.set_original(
                    new_original
                )
            potion_obj.set_elapsed(projectile_elapsed)
            if potion_obj.alive:
                # keep unfinished flights so game can save them at replay end
                still_active.append((throw_time, owner, potion_obj))
            else:
                landing_time = (
                    throw_time
                    + potion_obj.travel_time
                    - potion_obj.replay_elapsed_offset
                )
                if potion_obj.type == "cannon":
                    # cannonballs create one short impact with distance falloff
                    impact = projectile.CannonImpact(
                        potion_obj.target,
                        owner,
                        landing_time,
                    )
                    impact.set_time(current_time)
                    self.active_areas.append(impact)
                else:
                    # potion areas keep their full lifetime across rounds
                    self.active_areas.append(
                        projectile.PotionArea(
                            potion_obj.target,
                            owner,
                            landing_time,
                            visual_variant=potion_obj.visual_variant,
                        )
                    )
        self.active_projectiles = still_active

    # convert unfinished flights into events for the next replay
    def get_carried_projectile_events(self):
        carried_events = []
        for throw_time, owner, potion_obj in self.active_projectiles:
            # zero starts this round while elapsed restores exact prior progress
            carried_events.append(
                {
                    "timestamp": 0.0,
                    "elapsed": potion_obj.elapsed,
                    "player_number": owner,
                    "original": tuple(potion_obj.original),
                    "target": tuple(potion_obj.target),
                    "potion_type": potion_obj.type,
                    "visual_variant": potion_obj.visual_variant,
                    "aim_target": tuple(potion_obj.aim_target),
                }
            )
        return carried_events

    # convert active areas into events with their elapsed lifetime restored
    def get_carried_area_events(self):
        return [
            {
                "position": tuple(area.position),
                "owner": area.owner,
                "start_time": -area.elapsed,
                "area_type": area.TYPE,
                "damage_applied": getattr(area, "damage_applied", False),
                "visual_variant": getattr(area, "visual_variant", None),
            }
            for area in self.active_areas
            if area.alive
        ]

    # preserve cooldown time and contact state across replay cutoffs
    def get_carried_area_damage_state(self):
        return {
            "cooldowns": {
                player_number: max(0.0, next_damage_time - self.last_time)
                for player_number, next_damage_time
                in self.area_damage_cooldowns.items()
            },
            "touching": self.players_touching_area.copy(),
        }

    # draw active projectiles
    def draw_projectiles(self, screen):
        for throw_time, owner, potion_obj in self.active_projectiles:
            potion_obj.draw(screen)

    # damage player immediately and then apply the cooldown
    def apply_area_damage(self, player_obj, player_number, touching, current_time):
        # retrieve the previous touch state and next allowed hit time
        was_touching = self.players_touching_area[player_number]
        next_damage_time = self.area_damage_cooldowns[player_number]

        # first contact deals damage immediately when cooldown is ready
        if touching and not was_touching and current_time >= next_damage_time:
            player_obj.take_damage(projectile.PotionArea.DAMAGE)
            next_damage_time = current_time + projectile.PotionArea.DAMAGE_INTERVAL
        # continued contact deals another hit every 0.75 seconds
        elif touching and was_touching:
            while current_time >= next_damage_time and player_obj.hp > 0:
                player_obj.take_damage(projectile.PotionArea.DAMAGE)
                next_damage_time += projectile.PotionArea.DAMAGE_INTERVAL

        # save damage state for the next replay frame
        self.area_damage_cooldowns[player_number] = next_damage_time
        self.players_touching_area[player_number] = touching

    # update active damage areas
    def update_areas(self, current_time, player1, player2):
        still_active = []
        # one value per player prevents overlapping areas from stacking
        touching_area = {1: False, 2: False}

        for area in self.active_areas:
            # update lifetime and remove expired areas
            area.set_time(current_time)
            opponent_number = 2 if area.owner == 1 else 1
            opponent = player2 if opponent_number == 2 else player1

            if isinstance(area, projectile.CannonImpact):
                # a cannon impact can damage its opponent only once
                if not area.damage_applied:
                    damage = area.get_damage(opponent)
                    if damage > 0:
                        opponent.take_damage(damage)
                    area.damage_applied = True
                if area.alive:
                    still_active.append(area)
                continue

            if area.alive:
                # check the opponent of the player who threw the potion
                if area.contains_player(opponent):
                    touching_area[opponent_number] = True
                still_active.append(area)

        self.active_areas = still_active
        # apply at most one shared potion area hit to each player
        self.apply_area_damage(player1, 1, touching_area[1], current_time)
        self.apply_area_damage(player2, 2, touching_area[2], current_time)

    # draw active damage areas
    def draw_areas(self, screen):
        for area in self.active_areas:
            area.draw(screen)

    # actually run the replay by changing the player properties
    def apply_track(self, player_obj, track, current_time):
        times, states = track

        # safe handling if the player track is empty
        if not times:
            return

        # in case the current time is outside the range we just set current state to first or last
        if current_time <= times[0]:
            state = states[0]
        elif current_time >= times[-1]:
            state = states[-1]
        else:
            # get the index of the bisect right of current_time
            right = bisect_right(times, current_time)
            # previous element
            left = right - 1

            # calculate the distance between the two times
            alpha = (
                (current_time - times[left])
                / (times[right] - times[left])
            )

            # interpolate the states
            state = [
                self.lerp(a, b, alpha)
                for a, b in zip(states[left][:4], states[right][:4])
            ]
            if len(states[left]) > 4 and len(states[right]) > 4:
                state.append(
                    states[left][4]
                    if alpha < 0.5
                    else states[right][4]
                )

        # apply the states
        (
            player_obj.x,
            player_obj.y,
            player_obj.x_vel,
            player_obj.y_vel,
        ) = state[:4]
        if len(state) > 4:
            direction = "left" if state[4] < 0 else "right"
            player_obj.set_facing_direction(direction)

    # gameplay function for replay
    def play_out(self, player1, player2, current_time=None):
        # if it isn't declared then initiate
        if current_time is None:
            if self.start_time is None:
                self.restart()
            current_time = perf_counter() - self.start_time

        # prevent it from going below 0
        current_time = max(0.0, current_time)
        replay_finished = current_time >= self.duration
        # stop movement and damage at the player recording cutoff
        current_time = min(current_time, self.duration)

        # apply both tracks at the same time
        self.apply_track(player1, self.tracks[0], current_time)
        self.apply_track(player2, self.tracks[1], current_time)
        # update projectile timeline
        self.update_projectiles(current_time, player1, player2)
        # update damage areas during replay
        self.update_areas(current_time, player1, player2)
        self.last_time = current_time

        # return if done
        return replay_finished
