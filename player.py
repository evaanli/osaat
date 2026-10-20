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
    ):
        self.x = 0
        self.y = 0
        self.x_vel = 0
        self.y_vel = 0

        self.width = 75
        self.height = 150
        self.sprite_size = sprite_size or (self.width, self.height)

        self.color = (255, 255, 255)

        # health variables
        self.hp = self.MAX_HP

        # sprite animation is optional until its numbered png files exist
        self.animations = {}
        self.current_animation = None
        self.sprite = None
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
            )
        else:
            # subfolders such as idle and walk_left become animation names
            for animation_folder in sorted(folder.iterdir()):
                if (
                    animation_folder.is_dir()
                    and (animation_folder / "0.png").is_file()
                ):
                    self.animations[animation_folder.name] = sprite.Sprite(
                        animation_folder,
                        frame_time_ms=frame_time_ms,
                        size=self.sprite_size,
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
        return True

    # update walking only while the player is actually moving
    def update_sprite(self, dt):
        if self.sprite is None:
            return

        moving = abs(self.x_vel) > 0.1 or abs(self.y_vel) > 0.1
        if not moving:
            # keep the exact walking frame reached before stopping
            self.sprite.pause()
            return

        if self.x_vel < -0.1:
            self.set_animation("walk_left")
        elif self.x_vel > 0.1:
            self.set_animation("walk_right")
        elif self.current_animation not in ("walk_left", "walk_right"):
            # vertical movement uses right until a facing direction exists
            self.set_animation("walk_right")

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

    # center the sprite over the body while keeping its feet aligned
    def get_sprite_position(self):
        if self.sprite is None:
            return round(self.x), round(self.y)
        return (
            round(self.x + (self.width - self.sprite.width) / 2),
            round(self.y + self.height - self.sprite.height),
        )

    # get the smaller collision square placed at the player's feet
    def get_hitbox(self):
        hitbox_size = max(
            1,
            round(min(self.width, self.height) * self.hitbox_scale),
        )
        return pygame.Rect(
            round(self.x + (self.width - hitbox_size) / 2),
            round(self.y + self.height - hitbox_size),
            hitbox_size,
            hitbox_size,
        )

    # keep the full visible player inside the gameplay rectangle
    def constrain_to(self, game_area):
        sprite_width = self.sprite.width if self.sprite is not None else self.width
        sprite_height = self.sprite.height if self.sprite is not None else self.height
        horizontal_overhang = max(0.0, (sprite_width - self.width) / 2)
        top_overhang = max(0.0, sprite_height - self.height)

        minimum_x = game_area.left + horizontal_overhang
        maximum_x = game_area.right - self.width - horizontal_overhang
        minimum_y = game_area.top + top_overhang
        maximum_y = game_area.bottom - self.height

        old_x = self.x
        old_y = self.y
        self.x = max(minimum_x, min(self.x, maximum_x))
        self.y = max(minimum_y, min(self.y, maximum_y))

        # stop velocity on an axis when that boundary is reached
        if self.x != old_x:
            self.x_vel = 0
        if self.y != old_y:
            self.y_vel = 0

    # update physics and apply the optional gameplay boundary
    def update(self, dt, game_area=None):
        frame_scale = dt * 60

        self.x += self.x_vel * frame_scale
        self.y += self.y_vel * frame_scale

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
        self.hp = self.MAX_HP

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
