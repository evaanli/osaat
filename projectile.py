import math
import random
from pathlib import Path

import pygame

import drawing


POTION_SPRITE_FOLDER = (
    Path(__file__).resolve().parent / "assets" / "dory_to" / "potions"
)


# potion projectiles
class Potion:
    # speed
    SPEED = 300.0
    # time spent charging before movement starts
    CHARGE_TIME = 0.0
    # potion draw radius
    RADIUS = 10
    # colour
    COLOR = (170, 75, 255)
    # arc settings
    ARC_SCALE = 0.3
    MIN_ARC_HEIGHT = 40.0
    MAX_ARC_HEIGHT = 160.0
    # longest allowed potion throw in gameplay pixels
    MAX_DISTANCE = 450.0
    # visible bottle size and tumbling speed during flight
    SPRITE_SIZE = (28, 54)
    SPIN_SPEED = 720.0
    USES_POTION_SPRITE = True
    VARIANT_COLORS = (
        (171, 112, 246),
        (255, 153, 0),
        (101, 242, 83),
    )
    _sprite_variants = None

    # prepare large source images before gameplay can receive a throw input
    @classmethod
    def preload_assets(cls):
        cls.get_sprite_variants()

    # harming potion
    def __init__(
        self,
        original=(0, 0),
        target=(10, 10),
        potion_type="harming",
        owner=None,
        visual_variant=None,
    ):
        # potion type
        self.type = potion_type
        # player number controlling this live recording projectile
        self.owner = owner
        # original position vector
        self.original = pygame.Vector2(original)
        # target stops at maximum range in the mouse direction
        self.target = self.get_limited_target(self.original, target)
        # current position
        self.position = self.original.copy()

        # time elapsed
        self.elapsed = 0.0

        # current distance to target
        self.distance = self.original.distance_to(self.target)
        # charge and flight times make up the full projectile lifetime
        self.charge_time = self.CHARGE_TIME
        self.flight_time = self.get_travel_time(
            self.original,
            self.target,
        )
        self.travel_time = self.charge_time + self.flight_time
        # arc height calculation
        self.arc_height = self.get_arc_height(self.original, self.target)
        # status
        self.alive = True
        self.broken = False
        self.charging = self.charge_time > 0.0

        # choose one bottle colour and keep it for this whole throw
        self.visual_variant = None
        if self.USES_POTION_SPRITE:
            variants = self.get_sprite_variants()
            if variants:
                if visual_variant is None:
                    visual_variant = random.randrange(len(variants))
                self.visual_variant = int(visual_variant) % len(variants)

        # spin with the direction of horizontal travel like a thrown bottle
        self.spin_direction = -1.0 if self.target.x >= self.original.x else 1.0

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

    # clamp a target to maximum range while preserving its direction
    @classmethod
    def get_limited_target(cls, original, target):
        original = pygame.Vector2(original)
        target = pygame.Vector2(target)
        offset = target - original
        if cls.MAX_DISTANCE is None or offset.length() <= cls.MAX_DISTANCE:
            return target
        return original + offset.normalize() * cls.MAX_DISTANCE

    # calculate the same arc height for projectiles and the aiming guide
    @classmethod
    def get_arc_height(cls, original, target):
        distance = pygame.Vector2(original).distance_to(target)
        if distance == 0.0:
            return 0.0
        return max(
            cls.MIN_ARC_HEIGHT,
            min(cls.MAX_ARC_HEIGHT, distance * cls.ARC_SCALE),
        )

    # load and crop the numbered potion colour variants once
    @classmethod
    def get_sprite_variants(cls):
        if Potion._sprite_variants is not None:
            return Potion._sprite_variants

        variants = []
        frame_paths = sorted(
            (
                path
                for path in POTION_SPRITE_FOLDER.glob("*.png")
                if path.stem.isdigit()
            ),
            key=lambda path: int(path.stem),
        )
        for frame_path in frame_paths:
            image = pygame.image.load(str(frame_path))
            if pygame.display.get_surface() is not None:
                image = image.convert_alpha()
            else:
                image = image.copy()

            # remove the large transparent canvas around the bottle art
            visible_rect = image.get_bounding_rect(min_alpha=16)
            if visible_rect.width == 0 or visible_rect.height == 0:
                continue
            image = image.subsurface(visible_rect).copy()
            variants.append(
                pygame.transform.smoothscale(image, cls.SPRITE_SIZE)
            )

        Potion._sprite_variants = variants
        return Potion._sprite_variants

    # move a charging projectile with its firing point before release
    def set_original(self, original):
        if not self.charging:
            return

        self.original.update(original)
        self.position = self.original.copy()
        self.distance = self.original.distance_to(self.target)
        self.flight_time = self.get_travel_time(
            self.original,
            self.target,
        )
        self.travel_time = self.charge_time + self.flight_time
        self.arc_height = self.get_arc_height(self.original, self.target)

    # set elapsed time
    def set_elapsed(self, elapsed):
        # set elapsed time to above zero
        self.elapsed = max(0.0, elapsed)

        # stay on the firing point until the charge finishes
        if self.elapsed < self.charge_time:
            self.position = self.original.copy()
            self.charging = True
            self.broken = False
            self.alive = True
            return

        self.charging = False
        flight_elapsed = self.elapsed - self.charge_time

        # break when there is no flight or the projectile reaches its target
        if self.travel_time == 0.0 or self.elapsed >= self.travel_time:
            self.break_potion()
            return

        # get progress percentage
        progress = flight_elapsed / self.flight_time
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
        self.charging = False
        self.broken = True
        self.alive = False

    # update the potion position and elapsed time
    def update(self, dt):
        self.set_elapsed(self.elapsed + max(0.0, dt))

    # draw the potion
    def draw(self, surface):
        if not self.alive:
            return

        variants = self.get_sprite_variants()
        if self.visual_variant is None or not variants:
            drawing.draw_smooth_circle(
                surface,
                self.COLOR,
                (round(self.position.x), round(self.position.y)),
                self.RADIUS,
            )
            return

        # rotate from elapsed flight time so replay and live throws match
        flight_elapsed = max(0.0, self.elapsed - self.charge_time)
        angle = self.spin_direction * self.SPIN_SPEED * flight_elapsed
        image = pygame.transform.rotozoom(
            variants[self.visual_variant],
            angle,
            1.0,
        )
        draw_rect = image.get_rect(
            center=(round(self.position.x), round(self.position.y))
        )
        surface.blit(image, draw_rect)


# large charged projectile fired by mr donald
class CannonBall(Potion):
    SPEED = 1800.0
    CHARGE_TIME = 0.75
    RADIUS = 24
    COLOR = (255, 142, 45)
    OUTLINE_COLOR = (90, 38, 12)
    ARC_SCALE = 0.0
    MIN_ARC_HEIGHT = 0.0
    MAX_ARC_HEIGHT = 0.0
    MAX_DISTANCE = None
    USES_POTION_SPRITE = False

    def __init__(self, original, target, owner=None):
        super().__init__(original, target, "cannon", owner)

    # draw a growing square charge before drawing the fired square
    def draw(self, surface):
        if not self.alive:
            return

        center = round(self.position.x), round(self.position.y)
        if self.charging:
            charge_progress = min(1.0, self.elapsed / self.charge_time)
            charge_radius = max(
                4,
                round(self.RADIUS * (0.35 + charge_progress * 0.65)),
            )
            charge_rect = pygame.Rect(
                0,
                0,
                charge_radius * 2,
                charge_radius * 2,
            )
            charge_rect.center = center
            pygame.draw.rect(surface, self.COLOR, charge_rect, 3)
            inner_rect = pygame.Rect(0, 0, charge_radius, charge_radius)
            inner_rect.center = center
            pygame.draw.rect(
                surface,
                (255, 220, 120),
                inner_rect,
            )
            return

        projectile_rect = pygame.Rect(
            0,
            0,
            self.RADIUS * 2,
            self.RADIUS * 2,
        )
        projectile_rect.center = center
        pygame.draw.rect(surface, self.OUTLINE_COLOR, projectile_rect)
        pygame.draw.rect(surface, self.COLOR, projectile_rect.inflate(-8, -8))
        shine_rect = pygame.Rect(0, 0, 8, 8)
        shine_rect.center = center[0] - 7, center[1] - 7
        pygame.draw.rect(
            surface,
            (255, 220, 120),
            shine_rect,
        )


# build the correct projectile class from recorded type data
def create_projectile(
    projectile_type,
    original=(0, 0),
    target=(10, 10),
    owner=None,
    visual_variant=None,
):
    if projectile_type == "cannon":
        return CannonBall(original, target, owner)
    return Potion(
        original,
        target,
        projectile_type,
        owner,
        visual_variant,
    )


# measure from an effect center to the nearest part of the friendly hitbox
def distance_to_player(position, player_obj):
    player_hitbox = player_obj.get_hitbox()
    closest_x = max(
        player_hitbox.left,
        min(position.x, player_hitbox.right),
    )
    closest_y = max(
        player_hitbox.top,
        min(position.y, player_hitbox.bottom),
    )
    return position.distance_to((closest_x, closest_y))


# check a circular effect against the player's friendly rectangle
def circle_touches_player(position, radius, player_obj):
    return distance_to_player(position, player_obj) <= radius


# potion damage area
class PotionArea:
    TYPE = "potion"
    # distance from the center that counts as touching
    RADIUS = 65
    # aiming circle stays much smaller than the real damage area
    PREVIEW_RADIUS = 25
    # maximum amount of time the area can stay active
    DURATION = 2.0
    # damage dealt each time the cooldown allows a hit
    DAMAGE = 5
    # time before a player can take area damage again
    DAMAGE_INTERVAL = 0.75
    # fallback transparent colour used to show the area
    COLOR = (170, 75, 255, 75)

    def __init__(
        self,
        position,
        owner,
        start_time,
        end_time=None,
        visual_variant=None,
    ):
        # center position of the area
        self.position = pygame.Vector2(position)
        # player number that threw the potion
        self.owner = owner
        # match the spill to the bottle colour selected for this throw
        self.visual_variant = visual_variant
        if visual_variant is None:
            self.color = self.COLOR
        else:
            color_index = int(visual_variant) % len(Potion.VARIANT_COLORS)
            self.color = (*Potion.VARIANT_COLORS[color_index], self.COLOR[3])
        # replay time when the potion broke
        self.start_time = start_time
        # stop after two seconds unless an earlier limit is requested
        self.end_time = min(
            start_time + self.DURATION,
            end_time if end_time is not None else start_time + self.DURATION,
        )
        # current area state
        self.elapsed = 0.0
        self.alive = True

    # update area lifetime
    def set_time(self, current_time):
        self.elapsed = max(0.0, current_time - self.start_time)
        self.alive = current_time < self.end_time

    # check if player is inside the area
    def contains_player(self, player_obj):
        return circle_touches_player(self.position, self.RADIUS, player_obj)

    # draw transparent damage area
    def draw(self, surface):
        if not self.alive:
            return

        # use a separate alpha surface to make the circle transparent
        padding = 2
        diameter = (self.RADIUS + padding) * 2
        area_surface = pygame.Surface((diameter, diameter), pygame.SRCALPHA)
        drawing.draw_smooth_circle(
            area_surface,
            self.color,
            (self.RADIUS + padding, self.RADIUS + padding),
            self.RADIUS,
        )
        surface.blit(
            area_surface,
            (
                round(self.position.x - self.RADIUS - padding),
                round(self.position.y - self.RADIUS - padding),
            ),
        )


# short cannon impact that deals one replay-only hit
class CannonImpact:
    TYPE = "cannon"
    RADIUS = 160
    DURATION = 0.3
    # a direct hit still lets mr donald defeat dory in two shots
    DAMAGE = 10
    MIN_DAMAGE = 1
    COLOR = (255, 142, 45, 110)

    def __init__(
        self,
        position,
        owner,
        start_time,
        damage_applied=False,
    ):
        self.position = pygame.Vector2(position)
        self.owner = owner
        self.start_time = start_time
        self.end_time = start_time + self.DURATION
        self.elapsed = 0.0
        self.alive = True
        self.damage_applied = damage_applied

    # update the brief impact lifetime
    def set_time(self, current_time):
        self.elapsed = max(0.0, current_time - self.start_time)
        self.alive = current_time < self.end_time

    # check the impact against the opponent's friendly hitbox
    def contains_player(self, player_obj):
        return circle_touches_player(self.position, self.RADIUS, player_obj)

    # lower damage linearly from ten at the center to one at the edge
    def get_damage(self, player_obj):
        distance = distance_to_player(self.position, player_obj)
        if distance > self.RADIUS:
            return 0

        falloff = 1.0 - distance / self.RADIUS
        return max(self.MIN_DAMAGE, math.ceil(self.DAMAGE * falloff))

    # draw a fading orange impact circle
    def draw(self, surface):
        if not self.alive:
            return

        progress = min(1.0, self.elapsed / self.DURATION)
        radius = max(1, round(self.RADIUS * (0.5 + progress * 0.5)))
        alpha = max(0, round(self.COLOR[3] * (1.0 - progress)))
        padding = 2
        diameter = (radius + padding) * 2
        impact_surface = pygame.Surface((diameter, diameter), pygame.SRCALPHA)
        drawing.draw_smooth_circle(
            impact_surface,
            (*self.COLOR[:3], alpha),
            (radius + padding, radius + padding),
            radius,
        )
        surface.blit(
            impact_surface,
            (
                round(self.position.x - radius - padding),
                round(self.position.y - radius - padding),
            ),
        )


# rebuild a carried area or impact from its recorded type
def create_area(
    area_type,
    position,
    owner,
    start_time,
    damage_applied=False,
    visual_variant=None,
):
    if area_type == CannonImpact.TYPE:
        return CannonImpact(
            position,
            owner,
            start_time,
            damage_applied,
        )
    return PotionArea(
        position,
        owner,
        start_time,
        visual_variant=visual_variant,
    )
