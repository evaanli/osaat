import pygame
import player
from time import perf_counter

class TimerSystem:
    def __init__(self):
        self.current_time = 0
        self.start_time = perf_counter()

    def restart(self):
        self.start_time = perf_counter()

    def get_timestamp(self):
        self.current_time = perf_counter() - self.start_time
        return self.current_time
        

# basic recording system that stores positions and timestamp via dictionary
class RecordSystem:
    def __init__(self):
        self.player1_positions = {
            # format is time: [x, y, x_vel, y_vel]
        }
        self.player2_positions = {}
        self.projectile_events = []

        # both replays
        self.full_replay = []

        # initiate timer system
        self.timer_system = TimerSystem()

    # record function
    def record(self, player_obj: player.Player, player_number):
        if player_number == 1:
            self.player1_positions[self.timer_system.get_timestamp()] = [player_obj.x, player_obj.y, player_obj.x_vel, player_obj.y_vel]
        elif player_number == 2:
            self.player2_positions[self.timer_system.get_timestamp()] = [player_obj.x, player_obj.y, player_obj.x_vel, player_obj.y_vel]

    # record projectile function
    def record_projectile(
        self, original, target, player_number, potion_type="harming"):
        # add projectile info to the projectile events
        self.projectile_events.append(
            {
                "timestamp": self.timer_system.get_timestamp(),
                "player_number": player_number,
                "original": tuple(original),
                "target": tuple(target),
                "potion_type": potion_type,
            } # no need for position update because it's calculated upon game run
        )

    # clear function
    def clear(self):
        # clears all replays
        self.full_replay = []
        self.player1_positions = {}
        self.player2_positions = {}
        self.projectile_events = []
    
    # merge function
    def merge(self):
        self.full_replay[0] = self.player1_positions
        self.full_replay[1] = self.player2_positions
