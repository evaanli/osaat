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

    # clear function
    def clear(self):
        self.full_replay = []
        self.player1_positions = {}
        self.player2_positions = {}
    
    # merge function
    def merge(self):
        self.full_replay[0] = self.player1_positions
        self.full_replay[1] = self.player2_positions

    
            
        
        
        
