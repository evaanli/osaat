import math

import pygame


# potion projectiles
class Potion:
    # speed
    SPEED = 300.0
    # potion draw radius
    RADIUS = 10
    # colour
    COLOR = (170, 75, 255)

    # harming potion
    def __init__(self, original=(0, 0), target=(10, 10), potion_type="harming"):
        # potion type
        self.type = potion_type
        # original position vector
        self.original = pygame.Vector2(original)
        # target position vector
        self.target = pygame.Vector2(target)
        # current position
        self.position = self.original.copy()

        # time elapsed
        self.elapsed = 0.0

        # current distance to target
        self.distance = self.original.distance_to(self.target)
        # travel time calculation
        self.travel_time = self.get_travel_time(
            self.original,
            self.target,
        )
        # arc height calculation
        self.arc_height = max(40.0, min(160.0, self.distance * 0.3))
        # status
        self.alive = True
        self.broken = False

        # if already at target then just break the potion
        if self.travel_time == 0.0:
            self.break_potion()

    # get travel tiem required from original to target
    @classmethod
    def get_travel_time(cls, original, target):
        # hypotenuse
        distance = math.hypot(
            target[0] - original[0],
            target[1] - original[1],
        )
        # return the time
        return distance / cls.SPEED

    # set elapsed time
    def set_elapsed(self, elapsed):
        # set elapsed time to above zero
        self.elapsed = max(0.0, elapsed)

        # if there is no time left or the elapsed time is over travle time then break the potion
        if self.travel_time == 0.0 or self.elapsed >= self.travel_time:
            self.break_potion()
            return

        # get progress percentage
        progress = self.elapsed / self.travel_time
        # get the position from the ground
        ground_position = self.original.lerp(self.target, progress)
        # get the height off the ground
        height = 4.0 * self.arc_height * progress * (1.0 - progress)
        # update the position
        self.position.update(ground_position.x, ground_position.y - height)
        # update status
        self.broken = False
        self.alive = True

    # when potion hits the groudn
    def break_potion(self):
        # position is the same as the target (perfect accuracy)
        self.position = self.target.copy()
        # update status
        self.broken = True
        self.alive = False

    # update the potion position and elapsed time
    def update(self, dt):
        self.set_elapsed(self.elapsed + max(0.0, dt))

    # draw the potion
    def draw(self, surface):
        if self.alive: # if alive
            pygame.draw.circle(
                surface,
                self.COLOR,
                (round(self.position.x), round(self.position.y)),
                self.RADIUS,
            )
