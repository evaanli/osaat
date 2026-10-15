# efficient sorted index finder for locating replay samples
from bisect import bisect_right
from time import perf_counter

class ReplaySystem:
    def __init__(self, player1_positions, player2_positions):
        # format the track
        self.tracks = [
            self.prepare_track(player1_positions),
            self.prepare_track(player2_positions),
        ]
        # get duration of track using the max time
        self.duration = max(
            (times[-1] for times, states in self.tracks if times),
            default=0.0,
        )
        # safe set start time value
        self.start_time = None

    # formats the track into two different elements of times and states
    def prepare_track(self, positions):
        # retrieve position entries
        samples = positions.items()
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

        # apply both tracks at the same time
        self.apply_track(player1, self.tracks[0], current_time)
        self.apply_track(player2, self.tracks[1], current_time)

        # return if done
        return current_time >= self.duration
