import controls
import projectile
import pygame
import record
import replay


# game class
class Game:
    # ----setup----
    def __init__(self, fps=60):
        # management variables
        self.fps = fps

        # player variables/properties
        self.player1_speed = 5
        self.player2_speed = 10

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

        # live potion projectiles
        self.projectiles = []
        # unfinished replay projectiles waiting for the next round
        # events rebuild flight state when the next replay starts
        self.carried_projectile_events = []
        # objects draw the same frozen position between replays
        self.paused_projectiles = []

        # player 1 state before recording
        self.player1_original_state = None

        # death animation variables
        self.dead_player_number = None
        self.winner_player_number = None
        self.death_animation_elapsed = 0.0
        self.winner_font = None

    # ----helper----

    # draw player function
    def draw_players(self, screen, player1, player2):
        # draw based on layers
        if player1.y > player2.y:
            player1.draw(screen)
            player2.draw(screen)
        else:
            player2.draw(screen)
            player1.draw(screen)

    def draw_scene(self, screen, player1, player2, projectiles=None):
        self.draw_players(screen, player1, player2)
        for potion_obj in self.projectiles if projectiles is None else projectiles:
            potion_obj.draw(screen)
        # draw carried projectiles without updating their flight
        for potion_obj in self.paused_projectiles:
            potion_obj.draw(screen)

    # draw a health bar above a player
    def draw_health_bar(self, screen, player_obj):
        bar_x = round(player_obj.x)
        bar_y = round(player_obj.y - 14)
        bar_width = player_obj.width
        health_width = round(bar_width * player_obj.hp / player_obj.MAX_HP)
        pygame.draw.rect(screen, (45, 45, 45), (bar_x, bar_y, bar_width, 8))
        pygame.draw.rect(screen, (50, 210, 80), (bar_x, bar_y, health_width, 8))

    def throw_potion(self, player_obj, target, player_number):
        # the player position is the temporary hand location until animations exist
        original = (player_obj.x, player_obj.y)
        potion_obj = projectile.Potion(original, target)

        if potion_obj.alive:
            self.projectiles.append(potion_obj)

        self.recording_system.record_projectile(
            original,
            target,
            player_number,
            potion_obj.type,
        )

    def update_projectiles(self, dt):
        for potion_obj in self.projectiles:
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
    def record_player(self, player_obj, player_number, speed, dt):
        # collects movements from player object
        player_movements = controls.return_movements()
        # apply movements from movement vector
        player_obj.x_vel += player_movements[1] * speed * dt * self.fps # with deltatime
        player_obj.y_vel += player_movements[0] * speed * dt * self.fps

        # update player object
        player_obj.update(dt)
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

    # start recording the full match
    def initialize_match_recording(self):
        self.match_recording_system.clear()
        self.match_replay_system = None
        self.match_recording = True
        self.match_recording_time = 0
        # clear old boundaries and carried flights for a new match
        self.match_round_end_times = []
        self.carried_projectile_events = []
        self.paused_projectiles = []
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
        # areas stop at this boundary while midair potions continue
        self.match_round_end_times.append(self.match_recording_time)

    # stop recording and prepare the full match replay
    def finish_match_recording(self):
        self.match_recording = False
        # full replay uses every boundary to preserve cross-round flights
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
    def record1(self, screen, dt, player1, player2, recording_time):
        # save player 1 state before their turn
        if self.player1_original_state is None:
            self.player1_original_state = (
                player1.x,
                player1.y,
                player1.x_vel,
                player1.y_vel,
            )

        # records the player
        self.record_player(player1, 1, self.player1_speed, dt)
        # draw
        self.draw_scene(screen, player1, player2)
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

        # restarts recording timer
        self.recording_system.timer_system.restart()

    # record player 2 phase
    def record2(self, screen, dt, player1, player2, recording_time):
        # records second player
        self.record_player(player2, 2, self.player2_speed, dt)
        self.draw_scene(screen, player1, player2)

        # return if overtime
        return self.recording_system.timer_system.get_timestamp() >= recording_time / 1000

    # ----phases----

    # ready phase (draws both players)
    def ready(self, screen, player1, player2):
        self.draw_scene(screen, player1, player2)

    # pause phase
    def pause1(self, screen, player1, player2):
        self.draw_scene(screen, player1, player2)

    # pause phase
    def pause2(self, screen, player1, player2):
        self.draw_scene(screen, player1, player2)

    # done phase
    def done(self, screen, player1, player2):
        self.draw_scene(screen, player1, player2)

    # ----replay----

    # initiate replay
    def start_replay(self):
        # add this round directly to the continuous match recording
        self.record_round()

        # carried events use negative time and new throws use normal time
        replay_events = (
            self.carried_projectile_events
            + self.recording_system.projectile_events
        )
        # assign player data to replay system
        self.replay_system = replay.ReplaySystem(
            self.recording_system.player1_positions,
            self.recording_system.player2_positions,
            replay_events,
        )
        # carried projectiles are now controlled by the replay system
        self.paused_projectiles = []
        # initialize replay_system
        self.replay_system.restart()

    # save unfinished projectiles for the next round
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
        player_x = round(player_obj.x)
        player_y = round(player_obj.y)
        dissolve_line = player_obj.height * progress

        for block_y in range(0, player_obj.height, block_size):
            row = block_y // block_size
            for block_x in range(0, player_obj.width, block_size):
                column = block_x // block_size
                pattern = ((row * 17 + column * 37) % 100) / 100
                dissolve_offset = (pattern - 0.5) * 20

                if block_y + dissolve_offset > dissolve_line:
                    pygame.draw.rect(
                        screen,
                        player_obj.color,
                        (
                            player_x + block_x,
                            player_y + block_y,
                            min(block_size, player_obj.width - block_x),
                            min(block_size, player_obj.height - block_y),
                        ),
                    )

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
        player_rect = pygame.Rect(
            dead_player.x,
            dead_player.y,
            dead_player.width,
            dead_player.height,
        )

        # flash the player three times
        flash_duration = 1.5
        if self.death_animation_elapsed < flash_duration:
            flash_time = self.death_animation_elapsed % 0.5
            flash_color = (255, 255, 255) if flash_time < 0.25 else dead_player.color
            pygame.draw.rect(screen, flash_color, player_rect)
            return False

        # dissolve the player from top to bottom after flashing
        dissolve_duration = 1.5
        dissolve_time = self.death_animation_elapsed - flash_duration
        if dissolve_time < dissolve_duration:
            progress = dissolve_time / dissolve_duration
            self.draw_dissolving_player(screen, dead_player, progress)
            return False

        return True
