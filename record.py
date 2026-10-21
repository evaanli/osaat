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
        # negative and positive values preserve left and right during replay
        facing_value = -1 if player_obj.facing_direction == "left" else 1
        state = [
            player_obj.x,
            player_obj.y,
            player_obj.x_vel,
            player_obj.y_vel,
            facing_value,
        ]
        if player_number == 1:
            self.player1_positions[self.timer_system.get_timestamp()] = state
        elif player_number == 2:
            self.player2_positions[self.timer_system.get_timestamp()] = state

    # record projectile function
    def record_projectile(
        self,
        original,
        target,
        player_number,
        potion_type="harming",
        visual_variant=None,
        aim_target=None,
    ):
        # add projectile info to the projectile events
        event = {
            "timestamp": self.timer_system.get_timestamp(),
            "player_number": player_number,
            "original": tuple(original),
            "target": tuple(target),
            "potion_type": potion_type,
            # replay the same random colour chosen for the live throw
            "visual_variant": visual_variant,
            # preserve the mouse aim for moving charged projectiles
            "aim_target": tuple(aim_target if aim_target is not None else target),
        }
        self.projectile_events.append(event)
        # live charging projectiles update this event with their final origin
        return event

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
