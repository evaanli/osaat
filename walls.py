import pygame


# default obstacle layout inside the fixed gameplay area
DEFAULT_WALL_RECTS = (
    (585, 150, 110, 170),
    (585, 400, 110, 170),
    (250, 505, 180, 45),
    (850, 170, 180, 45),
)


class Wall:
    COLOR = (82, 91, 108)
    INNER_COLOR = (105, 116, 136)
    BORDER_COLOR = (155, 169, 195)
    SHADOW_COLOR = (20, 24, 32)

    def __init__(self, rectangle):
        self.rect = pygame.Rect(rectangle)

    # draw a simple raised wall that stays readable on the dark ground
    def draw(self, surface):
        shadow = self.rect.move(0, 6)
        pygame.draw.rect(
            surface,
            self.SHADOW_COLOR,
            shadow,
            border_radius=8,
        )
        pygame.draw.rect(
            surface,
            self.BORDER_COLOR,
            self.rect,
            border_radius=8,
        )
        inner = self.rect.inflate(-6, -6)
        pygame.draw.rect(
            surface,
            self.COLOR,
            inner,
            border_radius=6,
        )
        highlight = pygame.Rect(
            inner.left + 4,
            inner.top + 4,
            max(1, inner.width - 8),
            max(2, min(6, inner.height - 8)),
        )
        pygame.draw.rect(
            surface,
            self.INNER_COLOR,
            highlight,
            border_radius=3,
        )


# return the entry time where one segment first reaches a rectangle
def get_segment_entry_time(original, target, rectangle):
    original = pygame.Vector2(original)
    direction = pygame.Vector2(target) - original
    minimum_time = 0.0
    maximum_time = 1.0

    for position, movement, minimum, maximum in (
        (original.x, direction.x, rectangle.left, rectangle.right),
        (original.y, direction.y, rectangle.top, rectangle.bottom),
    ):
        if abs(movement) < 0.000001:
            if position < minimum or position > maximum:
                return None
            continue

        first_time = (minimum - position) / movement
        second_time = (maximum - position) / movement
        near_time = min(first_time, second_time)
        far_time = max(first_time, second_time)
        minimum_time = max(minimum_time, near_time)
        maximum_time = min(maximum_time, far_time)
        if minimum_time > maximum_time:
            return None

    if minimum_time < 0.0 or minimum_time > 1.0:
        return None

    # touching a wall while moving away or along its edge is not a new hit
    if minimum_time <= 0.000001:
        probe = original + direction * 0.000001
        enters_wall = (
            rectangle.left < probe.x < rectangle.right
            and rectangle.top < probe.y < rectangle.bottom
        )
        if not enters_wall:
            return None
    return minimum_time


# stop a target at the first wall border along its intended direction
def get_blocked_target(original, target, wall_objects, clearance=0):
    original = pygame.Vector2(original)
    target = pygame.Vector2(target)
    direction = target - original
    earliest_time = 1.0

    for wall_obj in wall_objects:
        rectangle = wall_obj.rect.inflate(clearance * 2, clearance * 2)
        entry_time = get_segment_entry_time(original, target, rectangle)
        if entry_time is not None:
            earliest_time = min(earliest_time, entry_time)

    return original + direction * earliest_time
