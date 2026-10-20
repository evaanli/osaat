import controls
import projectile
import pygame
import record
import replay


GAME_WIDTH = 1280
GAME_HEIGHT = 720
GAME_SIZE = (GAME_WIDTH, GAME_HEIGHT)


# game class
class Game:
    # ----setup----
    def __init__(self, fps=60):
        # management variables
        self.fps = fps
        self.show_hitboxes = False
        # fixed rectangle containing all gameplay coordinates
        self.game_area = pygame.Rect(0, 0, GAME_WIDTH, GAME_HEIGHT)

        # player variables/properties
        self.player1_speed = 2
        self.player2_speed = 1

        # recording and replay system
        self.recording_system = record.RecordSystem()
        self.replay_system = None

        # full match recording and replay system
        self.match_recording_system = record.RecordSystem()
        self.match_replay_system = None
        self.match_recording = False
        self.match_recording_time = 0
        # end time of every round in the full match timeline
        self.match_round_end_times = []

        # live projectiles
        self.projectiles = []
        # remaining active-turn cooldown for each player's next throw
        self.projectile_cooldowns = {1: 0.0, 2: 0.0}
        # unfinished replay projectiles waiting for the next round
        # events rebuild flight state when the next replay starts
        self.carried_projectile_events = []
        # objects draw the same frozen position between replays
        self.paused_projectiles = []
        # active areas and damage timing also carry between rounds
        self.carried_area_events = []
        self.carried_area_damage_state = None
        self.paused_areas = []

        # player 1 state before recording
        self.player1_original_state = None
        self.player1_original_sprite_state = None

        # death animation variables
        self.dead_player_number = None
        self.winner_player_number = None
        self.death_animation_elapsed = 0.0
        self.winner_font = None

    # ----helper----

    # fit the gameplay rectangle inside any window without stretching it
    def get_game_viewport(self, window_size):
        window_width = max(1, round(window_size[0]))
        window_height = max(1, round(window_size[1]))
        scale = min(
            window_width / self.game_area.width,
            window_height / self.game_area.height,
        )
        viewport_width = max(1, round(self.game_area.width * scale))
        viewport_height = max(1, round(self.game_area.height * scale))
        return pygame.Rect(
            (window_width - viewport_width) // 2,
            (window_height - viewport_height) // 2,
            viewport_width,
            viewport_height,
        )

    # convert a window click into the fixed gameplay coordinates
    def window_to_game(self, position, window_size):
        viewport = self.get_game_viewport(window_size)
        if not viewport.collidepoint(position):
            return None

        game_x = (
            (position[0] - viewport.left)
            * self.game_area.width
            / viewport.width
        )
        game_y = (
            (position[1] - viewport.top)
            * self.game_area.height
            / viewport.height
        )
        return (
            min(self.game_area.right - 1, max(self.game_area.left, game_x)),
            min(self.game_area.bottom - 1, max(self.game_area.top, game_y)),
        )

    # scale the gameplay canvas and leave unused window space black
    def draw_game_to_window(self, window, game_surface):
        viewport = self.get_game_viewport(window.get_size())
        window.fill((0, 0, 0))

        if viewport.size == game_surface.get_size():
            scaled_game = game_surface
        else:
            scaled_game = pygame.transform.smoothscale(
                game_surface,
                viewport.size,
            )
        window.blit(scaled_game, viewport)

    # draw player function
    def draw_players(self, screen, player1, player2):
        # draw based on layers
        if player1.y > player2.y:
            player1.draw(screen)
            player2.draw(screen)
        else:
            player2.draw(screen)
            player1.draw(screen)

        # hitboxes stay above both players so they are easy to compare
        if self.show_hitboxes:
            player1.draw_hitbox(screen)
            player2.draw_hitbox(screen)

    # update active players and freeze everyone else on their current frame
    def update_sprites(
        self,
        dt,
        player1,
        player2,
        player1_active=False,
        player2_active=False,
    ):
        if player1_active:
            player1.update_sprite(dt)
        else:
            player1.pause_sprite()

        if player2_active:
            player2.update_sprite(dt)
        else:
            player2.pause_sprite()

    # switch collision debugging on or off
    def toggle_hitboxes(self):
        self.show_hitboxes = not self.show_hitboxes

    def draw_scene(
        self,
        screen,
        player1,
        player2,
        live_projectile_owner=None,
        throw_preview=None,
    ):
        # carried areas stay visible but do not update outside replay
        for area in self.paused_areas:
            area.draw(screen)

        if throw_preview is not None:
            player_obj, mouse_position = throw_preview
            self.draw_potion_preview(screen, player_obj, mouse_position)

        self.draw_players(screen, player1, player2)

        # only show new throws belonging to the player taking this turn
        for potion_obj in self.projectiles:
            if potion_obj.owner == live_projectile_owner:
                potion_obj.draw(screen)

        # carried projectiles are public results from the last replay
        for potion_obj in self.paused_projectiles:
            potion_obj.draw(screen)

    # draw dory's curved aiming guide and highlighted landing area
    def draw_potion_preview(self, screen, player_obj, mouse_position):
        if mouse_position is None:
            return

        original = pygame.Vector2(player_obj.get_projectile_origin())
        target = projectile.Potion.get_limited_target(
            original,
            mouse_position,
        )
        arc_height = projectile.Potion.get_arc_height(original, target)

        preview = pygame.Surface(screen.get_size(), pygame.SRCALPHA)
        points = []
        for step in range(25):
            progress = step / 24
            ground_position = original.lerp(target, progress)
            height = 4.0 * arc_height * progress * (1.0 - progress)
            points.append(
                (
                    round(ground_position.x),
                    round(ground_position.y - height),
                )
            )

        pygame.draw.lines(preview, (255, 255, 255, 150), False, points, 4)
        landing_center = round(target.x), round(target.y)
        pygame.draw.circle(
            preview,
            (255, 255, 255, 35),
            landing_center,
            projectile.PotionArea.PREVIEW_RADIUS,
        )
        pygame.draw.circle(
            preview,
            (255, 255, 255, 190),
            landing_center,
            projectile.PotionArea.PREVIEW_RADIUS,
            3,
        )
        screen.blit(preview, (0, 0))

    # draw a health bar above a player
    def draw_health_bar(self, screen, player_obj):
        bar_x = round(player_obj.x)
        # taller sprites still keep the bar above their visible image
        bar_y = player_obj.get_sprite_position()[1] - 14
        bar_width = player_obj.width
        health_width = round(bar_width * player_obj.hp / player_obj.max_hp)
        pygame.draw.rect(screen, (45, 45, 45), (bar_x, bar_y, bar_width, 8))
        pygame.draw.rect(screen, (50, 210, 80), (bar_x, bar_y, health_width, 8))

    # start this player's configured projectile from its firing point
    def throw_projectile(self, player_obj, target, player_number):
        projectile_type = player_obj.projectile_type

        # reject another throw until this player's active-time cooldown ends
        if self.projectile_cooldowns.get(player_number, 0.0) > 0.0:
            return None

        # only one cannonball can charge at a time for this player
        if projectile_type == "cannon" and any(
            projectile_obj.owner == player_number
            and projectile_obj.type == "cannon"
            and projectile_obj.charging
            for projectile_obj in self.projectiles
        ):
            return None

        if player_obj.direction_follows_mouse:
            player_obj.face_towards_x(target[0])

        original = player_obj.get_projectile_origin()
        projectile_obj = projectile.create_projectile(
            projectile_type,
            original,
            target,
            player_number,
        )

        if projectile_obj.alive:
            self.projectiles.append(projectile_obj)

        projectile_obj.recording_event = self.recording_system.record_projectile(
            original,
            projectile_obj.target,
            player_number,
            projectile_obj.type,
            projectile_obj.visual_variant,
        )
        self.projectile_cooldowns[player_number] = (
            player_obj.projectile_cooldown
        )
        return projectile_obj

    # keep the old method name for potion callers
    def throw_potion(self, player_obj, target, player_number):
        return self.throw_projectile(player_obj, target, player_number)

    def update_projectiles(
        self,
        dt,
        active_player_number=None,
        active_player=None,
    ):
        # cooldown time moves only during its owner's active recording turn
        if active_player_number is not None:
            self.projectile_cooldowns[active_player_number] = max(
                0.0,
                self.projectile_cooldowns.get(active_player_number, 0.0)
                - max(0.0, dt),
            )

        for potion_obj in self.projectiles:
            # only the player currently recording can advance their throws
            if (
                active_player_number is None
                or potion_obj.owner == active_player_number
            ):
                # keep a cannon charge attached until its firing frame
                if potion_obj.charging and active_player is not None:
                    potion_obj.set_original(
                        active_player.get_projectile_origin()
                    )
                    potion_obj.recording_event["original"] = tuple(
                        potion_obj.original
                    )
                potion_obj.update(dt)
        self.projectiles = [
            potion_obj for potion_obj in self.projectiles if potion_obj.alive
        ]

    # check if a player died during replay
    def update_dead_player(self, player1, player2):
        if player1.hp <= 0 and player2.hp <= 0:
            self.dead_player_number = 1
            self.winner_player_number = 0
        elif player1.hp <= 0:
            self.dead_player_number = 1
            self.winner_player_number = 2
        elif player2.hp <= 0:
            self.dead_player_number = 2
            self.winner_player_number = 1

    # recording function
    def record_player(
        self,
        player_obj,
        player_number,
        speed,
        dt,
        aim_x=None,
    ):
        # collects movements from player object
        player_movements = controls.return_movements()
        # apply movements from movement vector
        player_obj.x_vel += player_movements[1] * speed * dt * self.fps # with deltatime
        player_obj.y_vel += player_movements[0] * speed * dt * self.fps

        # update player object
        player_obj.update(dt, self.game_area)
        if player_obj.direction_follows_mouse and aim_x is not None:
            player_obj.face_towards_x(aim_x)
        else:
            player_obj.update_facing_from_velocity()
        # update player timeline
        self.recording_system.record(player_obj, player_number)

    # ----recording----

    # initialize recording function
    def initialize_recording(self):
        # resets the recording system
        self.recording_system.clear()
        self.recording_system.timer_system.restart()
        self.projectiles = []
        self.player1_original_state = None
        self.player1_original_sprite_state = None

    # start recording the full match
    def initialize_match_recording(self):
        self.match_recording_system.clear()
        self.match_replay_system = None
        self.match_recording = True
        self.match_recording_time = 0
        # clear old boundaries and carried effects for a new match
        self.match_round_end_times = []
        self.carried_projectile_events = []
        self.paused_projectiles = []
        self.carried_area_events = []
        self.carried_area_damage_state = None
        self.paused_areas = []
        self.projectile_cooldowns = {1: 0.0, 2: 0.0}
        self.dead_player_number = None
        self.winner_player_number = None

    # add the merged turn recordings to the full match
    def record_round(self):
        if not self.match_recording:
            return

        player1_positions = self.recording_system.player1_positions
        player2_positions = self.recording_system.player2_positions

        for timestamp, state in player1_positions.items():
            match_timestamp = self.match_recording_time + timestamp
            self.match_recording_system.player1_positions[match_timestamp] = state.copy()

        for timestamp, state in player2_positions.items():
            match_timestamp = self.match_recording_time + timestamp
            self.match_recording_system.player2_positions[match_timestamp] = state.copy()

        # use player recording length as the round cutoff
        round_duration = max(
            max(player1_positions, default=0),
            max(player2_positions, default=0),
        )

        for event in self.recording_system.projectile_events:
            match_event = event.copy()
            # move the local throw time into the full match timeline
            match_event["timestamp"] = self.match_recording_time + event["timestamp"]
            self.match_recording_system.projectile_events.append(match_event)

        self.match_recording_time += round_duration
        # effects continue through this boundary in the full replay
        self.match_round_end_times.append(self.match_recording_time)

    # stop recording and prepare the full match replay
    def finish_match_recording(self):
        self.match_recording = False
        # keep round boundaries as full match timeline metadata
        self.match_replay_system = replay.ReplaySystem(
            self.match_recording_system.player1_positions,
            self.match_recording_system.player2_positions,
            self.match_recording_system.projectile_events,
            self.match_round_end_times,
        )
        self.match_replay_system.restart()

    # start the full match replay from full health
    def start_match_replay(self, player1, player2):
        player1.reset_health()
        player2.reset_health()
        self.dead_player_number = None
        self.winner_player_number = None
        self.match_replay_system.restart()

    # record player 1 phase
    def record1(
        self,
        screen,
        dt,
        player1,
        player2,
        recording_time,
        mouse_position=None,
    ):
        # save player 1 state before their turn
        if self.player1_original_state is None:
            self.player1_original_state = (
                player1.x,
                player1.y,
                player1.x_vel,
                player1.y_vel,
            )
            # save the public pose before player 1 starts moving privately
            self.player1_original_sprite_state = player1.get_sprite_state()

        # records the player
        self.record_player(player1, 1, self.player1_speed, dt)
        # draw
        throw_preview = (
            (player1, mouse_position)
            if mouse_position is not None
            else None
        )
        self.draw_scene(
            screen,
            player1,
            player2,
            live_projectile_owner=1,
            throw_preview=throw_preview,
        )
        # return if overtime
        return self.recording_system.timer_system.get_timestamp() >= recording_time / 1000

    # initialize for second player
    def start_record2(self, player1=None):
        # reset player 1 so player 2 cannot see their final position
        if player1 is not None and self.player1_original_state is not None:
            (
                player1.x,
                player1.y,
                player1.x_vel,
                player1.y_vel,
            ) = self.player1_original_state
            # hide player 1's private walking pose from player 2
            player1.set_sprite_state(self.player1_original_sprite_state)

        # restarts recording timer
        self.recording_system.timer_system.restart()

    # record player 2 phase
    def record2(
        self,
        screen,
        dt,
        player1,
        player2,
        recording_time,
        mouse_position=None,
    ):
        # records second player
        aim_x = mouse_position[0] if mouse_position is not None else None
        self.record_player(player2, 2, self.player2_speed, dt, aim_x)
        self.draw_scene(screen, player1, player2, live_projectile_owner=2)

        # return if overtime
        return self.recording_system.timer_system.get_timestamp() >= recording_time / 1000

    # ----phases----

    # ready phase (draws both players)
    def ready(self, screen, player1, player2):
        self.draw_scene(screen, player1, player2)

    # pause phase
    def pause1(self, screen, player1, player2):
        self.draw_scene(screen, player1, player2, live_projectile_owner=1)

    # pause phase
    def pause2(self, screen, player1, player2):
        self.draw_scene(screen, player1, player2, live_projectile_owner=2)

    # done phase
    def done(self, screen, player1, player2):
        self.draw_scene(screen, player1, player2)

    # ----replay----

    # initiate replay
    def start_replay(self):
        # add this round directly to the continuous match recording
        self.record_round()

        # carried events include saved charge or flight progress
        replay_events = (
            self.carried_projectile_events
            + self.recording_system.projectile_events
        )
        # assign player data to replay system
        self.replay_system = replay.ReplaySystem(
            self.recording_system.player1_positions,
            self.recording_system.player2_positions,
            replay_events,
            area_events=self.carried_area_events,
            area_damage_state=self.carried_area_damage_state,
        )
        # carried effects are now controlled by the replay system
        self.paused_projectiles = []
        self.paused_areas = []
        # initialize replay_system
        self.replay_system.restart()

    # save unfinished projectiles and areas for the next round
    def carry_projectiles(self):
        # save data needed to rebuild each potion in the next replay
        self.carried_projectile_events = (
            self.replay_system.get_carried_projectile_events()
        )
        # keep current objects only for drawing while replay is paused
        self.paused_projectiles = [
            potion_obj
            for throw_time, owner, potion_obj
            in self.replay_system.active_projectiles
        ]
        # save remaining area lifetime and shared damage timing
        self.carried_area_events = (
            self.replay_system.get_carried_area_events()
        )
        self.carried_area_damage_state = (
            self.replay_system.get_carried_area_damage_state()
        )
        # keep areas visible while every replay-only effect is frozen
        self.paused_areas = list(self.replay_system.active_areas)

    # replay phase
    def replay(self, screen, player1, player2):
        # play out the replay
        finished = self.replay_system.play_out(player1, player2)

        self.replay_system.draw_areas(screen)
        self.draw_players(screen, player1, player2)
        self.replay_system.draw_projectiles(screen)
        self.draw_health_bar(screen, player1)
        self.draw_health_bar(screen, player2)
        self.update_dead_player(player1, player2)

        if finished and self.dead_player_number is None:
            self.carry_projectiles()

        # return if done
        return finished

    # replay the full match
    def replay_match(self, screen, player1, player2):
        finished = self.match_replay_system.play_out(player1, player2)
        self.match_replay_system.draw_areas(screen)
        self.draw_players(screen, player1, player2)
        self.match_replay_system.draw_projectiles(screen)
        self.draw_health_bar(screen, player1)
        self.draw_health_bar(screen, player2)
        self.update_dead_player(player1, player2)

        return finished

    # start the death animation
    def start_death_animation(self, player_number):
        self.dead_player_number = player_number
        if self.winner_player_number is None:
            self.winner_player_number = 2 if player_number == 1 else 1
        self.death_animation_elapsed = 0.0

    # draw the player dissolving from top to bottom
    def draw_dissolving_player(self, screen, player_obj, progress):
        block_size = 6
        sprite_image = (
            player_obj.sprite.get_image()
            if player_obj.sprite is not None
            else None
        )

        if sprite_image is not None:
            player_x, player_y = player_obj.get_sprite_position()
            draw_width, draw_height = player_obj.sprite.size
        else:
            player_x = round(player_obj.x)
            player_y = round(player_obj.y)
            draw_width, draw_height = player_obj.width, player_obj.height

        dissolve_line = draw_height * progress

        for block_y in range(0, draw_height, block_size):
            row = block_y // block_size
            for block_x in range(0, draw_width, block_size):
                column = block_x // block_size
                pattern = ((row * 17 + column * 37) % 100) / 100
                dissolve_offset = (pattern - 0.5) * 20

                if block_y + dissolve_offset > dissolve_line:
                    block_rect = pygame.Rect(
                        block_x,
                        block_y,
                        min(block_size, draw_width - block_x),
                        min(block_size, draw_height - block_y),
                    )
                    if sprite_image is not None:
                        screen.blit(
                            sprite_image,
                            (player_x + block_x, player_y + block_y),
                            block_rect,
                        )
                    else:
                        pygame.draw.rect(
                            screen,
                            player_obj.color,
                            block_rect.move(player_x, player_y),
                        )

    # draw the current player shape using one solid color
    def draw_player_silhouette(self, screen, player_obj, color):
        if player_obj.sprite is None:
            pygame.draw.rect(screen, color, player_obj.get_rect())
            return

        # the sprite mask keeps transparent pixels transparent
        sprite_mask = pygame.mask.from_surface(player_obj.sprite.get_image())
        silhouette = sprite_mask.to_surface(
            setcolor=(*color[:3], 255),
            unsetcolor=(0, 0, 0, 0),
        )
        screen.blit(silhouette, player_obj.get_sprite_position())

    # draw the stored winner after the animation
    def draw_winner(self, screen, player1, player2):
        if self.winner_player_number is None:
            return

        if self.winner_font is None:
            if not pygame.font.get_init():
                pygame.font.init()
            self.winner_font = pygame.font.Font(None, 72)

        if self.winner_player_number == 0:
            winner_text = "Draw"
            winner_color = (255, 255, 255)
        else:
            winner_text = f"Player {self.winner_player_number} Wins"
            winner = player1 if self.winner_player_number == 1 else player2
            winner_color = winner.color

        text_surface = self.winner_font.render(winner_text, True, winner_color)
        text_rect = text_surface.get_rect(center=screen.get_rect().center)
        screen.blit(text_surface, text_rect)

    # draw the death animation on a black background
    def death_animation(self, screen, dt, player1, player2):
        self.death_animation_elapsed += dt
        dead_player = player1 if self.dead_player_number == 1 else player2

        # flash the player three times
        flash_duration = 1.5
        if self.death_animation_elapsed < flash_duration:
            flash_time = self.death_animation_elapsed % 0.5
            if flash_time < 0.25:
                self.draw_player_silhouette(screen, dead_player, (255, 255, 255))
            else:
                dead_player.draw(screen)
            return False

        # dissolve the player from top to bottom after flashing
        dissolve_duration = 1.5
        dissolve_time = self.death_animation_elapsed - flash_duration
        if dissolve_time < dissolve_duration:
            progress = dissolve_time / dissolve_duration
            self.draw_dissolving_player(screen, dead_player, progress)
            return False

        return True
