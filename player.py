from pathlib import Path

import pygame
import sprite

class Player:
    MAX_HP = 20

    def __init__(
        self,
        sprite_folder=None,
        sprite_frame_time_ms=100,
        sprite_size=None,
        hitbox_size=None,
        hitbox_offset=(0, 0),
        sprite_centers=None,
        max_hp=None,
        direction_follows_mouse=False,
        projectile_type="harming",
        projectile_cooldown=0.0,
    ):
        self.x = 0
        self.y = 0
        self.x_vel = 0
        self.y_vel = 0

        self.width = 75
        self.height = 150
        self.sprite_size = sprite_size or (self.width, self.height)
        self.sprite_centers = sprite_centers or {}
        self.direction_follows_mouse = direction_follows_mouse
        self.facing_direction = "right"
        self.projectile_type = projectile_type
        self.projectile_cooldown = max(0.0, float(projectile_cooldown))

        # larger characters can provide a friendly custom rectangle
        self.hitbox_size = hitbox_size
        self.hitbox_offset = hitbox_offset

        self.color = (255, 255, 255)

        # health variables
        self.max_hp = self.MAX_HP if max_hp is None else max(1, int(max_hp))
        self.hp = self.max_hp

        # sprite animation is optional until its numbered png files exist
        self.animations = {}
        self.current_animation = None
        self.sprite = None
        self.sprite_hitbox_bottom = None
        if sprite_folder is not None:
            self.load_sprite(sprite_folder, sprite_frame_time_ms)

        # rectangle covering the full visible player
        self.player_rect = pygame.Rect(self.x, self.y, self.width, self.height)

        # smaller bottom square makes hits more forgiving
        self.hitbox_scale = 0.75

    # load each animation folder and scale its frames to the player size
    def load_sprite(self, folder, frame_time_ms=100):
        folder = Path(folder)
        self.animations = {}

        # a folder with 0.png is treated as one idle animation
        if (folder / "0.png").is_file():
            self.animations["idle"] = sprite.Sprite(
                folder,
                frame_time_ms=frame_time_ms,
                size=self.sprite_size,
                center=self.sprite_centers.get("idle"),
            )
        else:
            # subfolders such as idle and walk_left become animation names
            for animation_folder in sorted(folder.iterdir()):
                if (
                    animation_folder.is_dir()
                    # projectile art can live beside character animations
                    and animation_folder.name != "potions"
                    and not animation_folder.name.endswith("projectile")
                    and (animation_folder / "0.png").is_file()
                ):
                    self.animations[animation_folder.name] = sprite.Sprite(
                        animation_folder,
                        frame_time_ms=frame_time_ms,
                        size=self.sprite_size,
                        center=self.sprite_centers.get(animation_folder.name),
                    )

        if not self.animations:
            raise FileNotFoundError(
                f"sprite folder needs 0.png or animation subfolders: {folder}"
            )

        # support short left and right folder names used by some characters
        if "walk_left" not in self.animations and "left" in self.animations:
            self.animations["walk_left"] = self.animations["left"]
        if "walk_right" not in self.animations and "right" in self.animations:
            self.animations["walk_right"] = self.animations["right"]

        # use mirrored left frames when a separate right animation is missing
        if "walk_right" not in self.animations and "walk_left" in self.animations:
            self.animations["walk_right"] = self.animations["walk_left"]

        # characters without idle art begin on the first right or left frame
        if "idle" not in self.animations:
            idle_animation = self.animations.get(
                "walk_right",
                self.animations.get("walk_left"),
            )
            if idle_animation is not None:
                self.animations["idle"] = idle_animation

        first_animation = (
            "idle" if "idle" in self.animations else next(iter(self.animations))
        )
        self.set_animation(first_animation)

        # use one stable foot line so animation changes cannot move the hitbox
        unique_animations = {
            id(animation): animation
            for animation in self.animations.values()
        }.values()
        self.sprite_hitbox_bottom = max(
            opaque_rect.bottom
            for animation in unique_animations
            for opaque_rect in animation.opaque_rects
        )

    # change animation and restart only when the state changes
    def set_animation(self, animation_name):
        if animation_name not in self.animations:
            return False

        animation = self.animations[animation_name]
        if animation_name != self.current_animation:
            animation.restart()
            self.current_animation = animation_name

        self.sprite = animation
        # mirrored left frames face right when no right frames were loaded
        self.sprite.flip_x = (
            animation_name == "walk_right"
            and self.animations.get("walk_right") is self.animations.get("walk_left")
        )
        if animation_name.endswith("left"):
            self.facing_direction = "left"
        elif animation_name.endswith("right"):
            self.facing_direction = "right"
        return True

    # face one direction without tying it to horizontal movement
    def set_facing_direction(self, direction):
        if direction not in ("left", "right"):
            return False

        self.facing_direction = direction
        return self.set_animation(f"walk_{direction}")

    # choose a direction from the mouse position on the x axis
    def face_towards_x(self, target_x):
        center_x = self.x + self.width / 2 + self.hitbox_offset[0]
        if target_x < center_x:
            return self.set_facing_direction("left")
        if target_x > center_x:
            return self.set_facing_direction("right")
        return True

    # update regular characters from movement while mouse-aimed ones stay aimed
    def update_facing_from_velocity(self):
        if self.direction_follows_mouse:
            return
        if self.x_vel < -0.1:
            self.set_facing_direction("left")
        elif self.x_vel > 0.1:
            self.set_facing_direction("right")

    # update walking only while the player is actually moving
    def update_sprite(self, dt):
        if self.sprite is None:
            return

        moving = abs(self.x_vel) > 0.1 or abs(self.y_vel) > 0.1
        if not moving:
            # use a real idle pose when the character provides one
            idle_animation = self.animations.get("idle")
            if idle_animation not in (
                self.animations.get("walk_left"),
                self.animations.get("walk_right"),
            ):
                self.set_animation("idle")
            self.sprite.pause()
            return

        self.update_facing_from_velocity()
        if self.current_animation not in ("walk_left", "walk_right"):
            # vertical movement uses right until a facing direction exists
            self.set_facing_direction(self.facing_direction)

        self.sprite.play()
        self.sprite.update(dt)

    # freeze the current animation without changing its frame
    def pause_sprite(self):
        if self.sprite is not None:
            self.sprite.pause()

    # save the visible animation state for private turn recording
    def get_sprite_state(self):
        if self.sprite is None:
            return None
        return (
            self.current_animation,
            self.sprite.current_frame,
            self.sprite.elapsed_ms,
            self.sprite.playing,
        )

    # restore the exact animation frame another player last saw
    def set_sprite_state(self, state):
        if state is None:
            return

        animation_name, frame_number, elapsed_ms, playing = state
        if not self.set_animation(animation_name):
            return

        self.sprite.set_frame(frame_number)
        self.sprite.elapsed_ms = elapsed_ms
        if playing:
            self.sprite.play()
        else:
            self.sprite.pause()

    # get the full visual rectangle
    def get_rect(self):
        self.player_rect.update(
            round(self.x),
            round(self.y),
            self.width,
            self.height,
        )
        return self.player_rect

    # align the sprite's custom center while keeping its feet aligned
    def get_sprite_position(self):
        if self.sprite is None:
            return round(self.x), round(self.y)

        sprite_center_x, _ = self.sprite.get_center()
        player_center_x = (
            self.x
            + self.width / 2
            + self.hitbox_offset[0]
        )
        return (
            round(player_center_x - sprite_center_x),
            round(self.y + self.height - self.sprite.height),
        )

    # get the point where this player's projectile should begin
    def get_projectile_origin(self):
        if self.projectile_type != "cannon" or self.sprite is None:
            # use the visible sprite center until a hand attachment is available
            if self.sprite is None:
                return self.get_rect().center
            sprite_x, sprite_y = self.get_sprite_position()
            center_x, center_y = self.sprite.get_center()
            return sprite_x + center_x, sprite_y + center_y

        edge_x, edge_y = self.sprite.get_edge_point(self.facing_direction)
        sprite_x, sprite_y = self.get_sprite_position()
        return sprite_x + edge_x, sprite_y + edge_y

    # get the friendly collision rectangle placed at the player's visible feet
    def get_hitbox(self):
        default_hitbox_size = max(
            1,
            round(min(self.width, self.height) * self.hitbox_scale),
        )
        if self.hitbox_size is None:
            hitbox_width = default_hitbox_size
            hitbox_height = default_hitbox_size
        else:
            hitbox_width = max(1, round(self.hitbox_size[0]))
            hitbox_height = max(1, round(self.hitbox_size[1]))

        hitbox_bottom = self.y + self.height
        if self.sprite is not None:
            # ignore transparent padding below sprites such as mr donald's tracks
            if self.sprite_hitbox_bottom is not None:
                sprite_y = self.get_sprite_position()[1]
                hitbox_bottom = sprite_y + self.sprite_hitbox_bottom

        return pygame.Rect(
            round(
                self.x
                + (self.width - hitbox_width) / 2
                + self.hitbox_offset[0]
            ),
            round(hitbox_bottom - hitbox_height + self.hitbox_offset[1]),
            hitbox_width,
            hitbox_height,
        )

    # keep the full visible player inside the gameplay rectangle
    def constrain_to(self, game_area):
        # transparent sprite padding should not push a player across the map
        boundary_rect = self.get_hitbox()
        if self.sprite is not None:
            visible_rect = self.sprite.get_opaque_rect().move(
                self.get_sprite_position()
            )
            boundary_rect = boundary_rect.union(visible_rect)
        else:
            boundary_rect = boundary_rect.union(self.get_rect())

        x_correction = 0
        y_correction = 0
        if boundary_rect.left < game_area.left:
            x_correction = game_area.left - boundary_rect.left
        elif boundary_rect.right > game_area.right:
            x_correction = game_area.right - boundary_rect.right
        if boundary_rect.top < game_area.top:
            y_correction = game_area.top - boundary_rect.top
        elif boundary_rect.bottom > game_area.bottom:
            y_correction = game_area.bottom - boundary_rect.bottom

        self.x += x_correction
        self.y += y_correction

        # stop velocity on an axis when that boundary is reached
        if x_correction != 0:
            self.x_vel = 0
        if y_correction != 0:
            self.y_vel = 0

    # keep the friendly hitbox on its original side of every crossed wall
    def resolve_wall_collisions(
        self,
        wall_objects,
        axis,
        movement,
        previous_hitbox,
    ):
        if not wall_objects or movement == 0.0:
            return

        for wall_obj in wall_objects:
            wall_rect = wall_obj.rect
            hitbox = self.get_hitbox()

            if axis == "x":
                perpendicular_overlap = (
                    hitbox.top < wall_rect.bottom
                    and hitbox.bottom > wall_rect.top
                )
                if not perpendicular_overlap:
                    continue

                started_overlapping = previous_hitbox.colliderect(wall_rect)
                left_penetration = previous_hitbox.right - wall_rect.left
                right_penetration = wall_rect.right - previous_hitbox.left
                started_on_left = (
                    previous_hitbox.right <= wall_rect.left
                    or (
                        started_overlapping
                        and left_penetration <= right_penetration
                    )
                )
                started_on_right = (
                    previous_hitbox.left >= wall_rect.right
                    or (started_overlapping and not started_on_left)
                )

                if (
                    movement > 0.0
                    and started_on_left
                    and hitbox.right > wall_rect.left
                ):
                    self.x += wall_rect.left - hitbox.right - 1
                    self.x_vel = 0.0
                elif (
                    movement < 0.0
                    and started_on_right
                    and hitbox.left < wall_rect.right
                ):
                    self.x += wall_rect.right - hitbox.left + 1
                    self.x_vel = 0.0
                elif hitbox.colliderect(wall_rect):
                    # recover an old overlap without swapping wall sides
                    if started_on_left:
                        self.x += wall_rect.left - hitbox.right - 1
                    else:
                        self.x += wall_rect.right - hitbox.left + 1
                    self.x_vel = 0.0
            else:
                perpendicular_overlap = (
                    hitbox.left < wall_rect.right
                    and hitbox.right > wall_rect.left
                )
                if not perpendicular_overlap:
                    continue

                started_overlapping = previous_hitbox.colliderect(wall_rect)
                top_penetration = previous_hitbox.bottom - wall_rect.top
                bottom_penetration = wall_rect.bottom - previous_hitbox.top
                started_above = (
                    previous_hitbox.bottom <= wall_rect.top
                    or (
                        started_overlapping
                        and top_penetration <= bottom_penetration
                    )
                )
                started_below = (
                    previous_hitbox.top >= wall_rect.bottom
                    or (started_overlapping and not started_above)
                )

                if (
                    movement > 0.0
                    and started_above
                    and hitbox.bottom > wall_rect.top
                ):
                    self.y += wall_rect.top - hitbox.bottom - 1
                    self.y_vel = 0.0
                elif (
                    movement < 0.0
                    and started_below
                    and hitbox.top < wall_rect.bottom
                ):
                    self.y += wall_rect.bottom - hitbox.top + 1
                    self.y_vel = 0.0
                elif hitbox.colliderect(wall_rect):
                    # recover an old overlap without swapping wall sides
                    if started_above:
                        self.y += wall_rect.top - hitbox.bottom - 1
                    else:
                        self.y += wall_rect.bottom - hitbox.top + 1
                    self.y_vel = 0.0

    # update physics and apply optional gameplay and wall boundaries
    def update(self, dt, game_area=None, wall_objects=None):
        frame_scale = dt * 60

        x_movement = self.x_vel * frame_scale
        y_movement = self.y_vel * frame_scale

        previous_hitbox = self.get_hitbox()
        self.x += x_movement
        self.resolve_wall_collisions(
            wall_objects,
            "x",
            x_movement,
            previous_hitbox,
        )

        previous_hitbox = self.get_hitbox()
        self.y += y_movement
        self.resolve_wall_collisions(
            wall_objects,
            "y",
            y_movement,
            previous_hitbox,
        )

        self.x_vel *= 0.6 ** frame_scale
        self.y_vel *= 0.6 ** frame_scale

        if game_area is not None:
            self.constrain_to(game_area)

    # damage player health
    def take_damage(self, damage):
        # prevent health from going below zero
        self.hp = max(0, self.hp - damage)

    # reset player health
    def reset_health(self):
        self.hp = self.max_hp

    # draw the sprite or use the old rectangle as a fallback
    def draw(self, surface):
        self.get_rect()
        if self.sprite is not None:
            self.sprite.draw(surface, self.get_sprite_position())
        else:
            pygame.draw.rect(surface, self.color, self.player_rect)

    # draw a transparent collision square for debugging
    def draw_hitbox(self, surface):
        hitbox = self.get_hitbox()
        hitbox_surface = pygame.Surface(hitbox.size, pygame.SRCALPHA)
        hitbox_color = (*self.color[:3], 75)
        border_color = (*self.color[:3], 190)
        pygame.draw.rect(hitbox_surface, hitbox_color, hitbox_surface.get_rect())
        pygame.draw.rect(
            hitbox_surface,
            border_color,
            hitbox_surface.get_rect(),
            2,
        )
        surface.blit(hitbox_surface, hitbox.topleft)
