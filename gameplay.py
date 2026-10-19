import controls
import projectile
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

        # live potion projectiles
        self.projectiles = []

        # player 1 state before recording
        self.player1_original_state = None

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

    def throw_potion(self, player_obj, target, player_number):
        # The player position is the temporary hand location until animations exist.
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

        for event in self.recording_system.projectile_events:
            match_event = event.copy()
            match_event["timestamp"] = self.match_recording_time + event["timestamp"]
            self.match_recording_system.projectile_events.append(match_event)

        round_duration = max(
            max(player1_positions, default=0),
            max(player2_positions, default=0),
        )
        self.match_recording_time += round_duration

    # stop recording and prepare the full match replay
    def finish_match_recording(self):
        self.match_recording = False
        self.match_replay_system = replay.ReplaySystem(
            self.match_recording_system.player1_positions,
            self.match_recording_system.player2_positions,
            self.match_recording_system.projectile_events,
        )
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

        # assign player data to replay system
        self.replay_system = replay.ReplaySystem(
            self.recording_system.player1_positions,
            self.recording_system.player2_positions,
            self.recording_system.projectile_events,
        )
        # initialize replay_system
        self.replay_system.restart()

    # replay phase
    def replay(self, screen, player1, player2):
        # play out the replay
        finished = self.replay_system.play_out(player1, player2)

        self.draw_players(screen, player1, player2)
        self.replay_system.draw_projectiles(screen)

        # return if done
        return finished

    # replay the full match forever
    def replay_match(self, screen, player1, player2):
        finished = self.match_replay_system.play_out(player1, player2)
        self.draw_players(screen, player1, player2)
        self.match_replay_system.draw_projectiles(screen)

        if finished:
            self.match_replay_system.restart()
