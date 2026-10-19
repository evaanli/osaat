# efficient sorted index finder for locating replay samples
from bisect import bisect_right
from time import perf_counter

import projectile

class ReplaySystem:
    def __init__(
        self,
        player1_positions,
        player2_positions,
        projectile_events=None,
        round_end_times=None,
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
        # round boundaries stop damage areas without stopping flying potions
        self.round_end_times = sorted(round_end_times or [self.duration])
        # safe set start time value
        self.start_time = None
        # projectile replay variables
        self.projectile_index = 0
        self.active_projectiles = []
        self.active_areas = []
        self.last_time = 0.0
        # next replay time each player is allowed to take area damage
        self.area_damage_cooldowns = {1: 0.0, 2: 0.0}
        # remembers if each player was touching any area last frame
        self.players_touching_area = {1: False, 2: False}
        # used to reset damage cooldowns between saved rounds
        self.current_round_index = 0

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

    # initiates the recording clock
    def restart(self):
        self.start_time = perf_counter()
        # reset projectile replay
        self.projectile_index = 0
        self.active_projectiles = []
        self.active_areas = []
        self.last_time = 0.0
        # reset replay-only potion damage state
        self.area_damage_cooldowns = {1: 0.0, 2: 0.0}
        self.players_touching_area = {1: False, 2: False}
        self.current_round_index = 0

    # update projectile function
    def update_projectiles(self, current_time):
        # reset if the replay time moves backwards
        if current_time < self.last_time:
            self.projectile_index = 0
            self.active_projectiles = []
            self.active_areas = []
            # reset damage state when replay is moved backwards
            self.area_damage_cooldowns = {1: 0.0, 2: 0.0}
            self.players_touching_area = {1: False, 2: False}
            self.current_round_index = 0

        # count how many saved round boundaries replay has passed
        round_index = bisect_right(self.round_end_times[:-1], current_time)
        # reset cooldowns when replay enters the next recorded round
        if round_index > self.current_round_index:
            self.area_damage_cooldowns = {1: 0.0, 2: 0.0}
            self.players_touching_area = {1: False, 2: False}
            self.current_round_index = round_index

        # create projectiles once their timestamp is reached
        while (self.projectile_index < len(self.projectile_events) and self.projectile_events[self.projectile_index]["timestamp"] <= current_time):
            event = self.projectile_events[self.projectile_index]
            potion_obj = projectile.Potion(
                event["original"],
                event["target"],
                event["potion_type"],
            )
            # negative throw times restore time spent flying in older rounds
            # store throw time, owner, and potion object
            self.active_projectiles.append(
                (
                    event["timestamp"],
                    event["player_number"],
                    potion_obj,
                )
            )
            self.projectile_index += 1

        # update projectiles and create areas when they break
        still_active = []
        for throw_time, owner, potion_obj in self.active_projectiles:
            # calculate potion position from replay time
            potion_obj.set_elapsed(current_time - throw_time)
            if potion_obj.alive:
                # keep unfinished flights so game can save them at replay end
                still_active.append((throw_time, owner, potion_obj))
            else:
                landing_time = throw_time + potion_obj.travel_time
                area_end_time = self.get_area_end_time(landing_time)
                # create the damage area if the potion landed before cutoff
                if landing_time < area_end_time:
                    self.active_areas.append(
                        projectile.PotionArea(
                            potion_obj.target,
                            owner,
                            landing_time,
                            area_end_time,
                        )
                    )
        self.active_projectiles = still_active

    # get the end of the round where a potion lands
    def get_area_end_time(self, landing_time):
        # find the first round boundary after the landing time
        round_index = bisect_right(self.round_end_times, landing_time)
        if round_index < len(self.round_end_times):
            return self.round_end_times[round_index]
        # the final replay boundary is the last possible cutoff
        return self.duration

    # convert unfinished flights into events for the next replay
    def get_carried_projectile_events(self):
        carried_events = []
        for throw_time, owner, potion_obj in self.active_projectiles:
            # a negative timestamp makes replay start at the saved elapsed time
            carried_events.append(
                {
                    "timestamp": -potion_obj.elapsed,
                    "player_number": owner,
                    "original": tuple(potion_obj.original),
                    "target": tuple(potion_obj.target),
                    "potion_type": potion_obj.type,
                }
            )
        return carried_events

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
            if area.alive:
                # check the opponent of the player who threw the potion
                opponent_number = 2 if area.owner == 1 else 1
                opponent = player2 if opponent_number == 2 else player1
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
                for a, b in zip(states[left], states[right])
            ]

        # apply the states
        (
            player_obj.x,
            player_obj.y,
            player_obj.x_vel,
            player_obj.y_vel,
        ) = state

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
        self.update_projectiles(current_time)
        # update damage areas during replay
        self.update_areas(current_time, player1, player2)
        self.last_time = current_time

        # return if done
        return replay_finished
