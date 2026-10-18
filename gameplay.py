import controls
import record
import replay


# game class
class Game:
    def __init__(self, fps=60):
        # management variables
        self.fps = fps

        # player variables/properties
        self.player1_speed = 5
        self.player2_speed = 10

        # recording and replay system
        self.recording_system = record.RecordSystem()
        self.replay_system = None

    # draw player function
    def draw_players(self, screen, player1, player2):
        # draw based on layers
        if player1.y > player2.y:
            player1.draw(screen)
            player2.draw(screen)
        else:
            player2.draw(screen)
            player1.draw(screen)

    # initialize recording function
    def initialize_recording(self):
        # resets the recording system
        self.recording_system.clear()
        self.recording_system.timer_system.restart()

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
        
    # ready phase (draws both players)
    def ready(self, screen, player1, player2):
        self.draw_players(screen, player1, player2)
        
    # record player 1 phase
    def record1(self, screen, dt, player1, player2):
        # records the player
        self.record_player(player1, 1, self.player1_speed, dt)
        # draw
        self.draw_players(screen, player1, player2)
        # return if overtime
        return self.recording_system.timer_system.get_timestamp() >= 1

    # pause phase
    def pause1(self, screen, player1, player2):
        self.draw_players(screen, player1, player2)

    # initialize for second player
    def start_record2(self):
        # restarts recording timer
        self.recording_system.timer_system.restart()

    # record player 2 phase
    def record2(self, screen, dt, player1, player2):
        # records second player
        self.record_player(player2, 2, self.player2_speed, dt)
        self.draw_players(screen, player1, player2)

        # return if overtime
        return self.recording_system.timer_system.get_timestamp() >= 1

    # pause phase
    def pause2(self, screen, player1, player2):
        self.draw_players(screen, player1, player2)

    # initiate replay
    def start_replay(self):
        # assign player data to replay system
        self.replay_system = replay.ReplaySystem(
            self.recording_system.player1_positions,
            self.recording_system.player2_positions,
        )
        # initialize replay_system
        self.replay_system.restart()

    # replay phase
    def replay(self, screen, player1, player2):
        # play out the replay
        finished = self.replay_system.play_out(player1, player2)

        self.draw_players(screen, player1, player2)

        # return if done
        return finished

    # done phase
    def done(self, screen, player1, player2):
        self.draw_players(screen, player1, player2)
