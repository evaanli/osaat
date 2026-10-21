from pathlib import Path
import math

import pygame


CHARACTERS = ("dory to", "mr donald")


# load one transparent menu element without its large empty canvas
def load_cropped_image(path):
    image = pygame.image.load(str(path)).convert_alpha()
    visible_rect = image.get_bounding_rect(min_alpha=8)
    if visible_rect.width == 0 or visible_rect.height == 0:
        return image
    return image.subsurface(visible_rect).copy()


# fit an image inside a box while preserving its proportions
def scale_to_fit(image, maximum_size):
    scale = min(
        maximum_size[0] / image.get_width(),
        maximum_size[1] / image.get_height(),
    )
    size = (
        max(1, round(image.get_width() * scale)),
        max(1, round(image.get_height() * scale)),
    )
    return pygame.transform.smoothscale(image, size)


class CharacterMenu:
    def __init__(self, asset_folder):
        asset_folder = Path(asset_folder)
        menu_folder = asset_folder / "menu"

        self.background_source = pygame.image.load(
            str(menu_folder / "background.png")
        ).convert()
        self.start_source = load_cropped_image(menu_folder / "start.png")
        self.right_source = load_cropped_image(menu_folder / "arrows" / "0.png")
        self.left_source = load_cropped_image(menu_folder / "arrows" / "1.png")
        self.preview_sources = {
            "dory to": load_cropped_image(
                asset_folder / "dory_to" / "idle" / "0.png"
            ),
            "mr donald": load_cropped_image(
                asset_folder / "mr_donald" / "right" / "0.png"
            ),
        }

        self.selections = [0, 1]
        self.button_rects = {}
        self.layout_size = None
        self.background = None
        self.start_image = None
        self.left_image = None
        self.right_image = None
        self.previews = {}
        self.heading_font = None
        self.name_font = None

    # rebuild scaled menu art only when the window dimensions change
    def prepare_layout(self, size):
        if size == self.layout_size:
            return

        width, height = max(1, size[0]), max(1, size[1])
        self.layout_size = width, height
        self.background = pygame.transform.smoothscale(
            self.background_source,
            self.layout_size,
        )

        start_width = max(1, round(min(width * 0.28, height * 0.46)))
        start_height = max(
            1,
            round(start_width * self.start_source.get_height() / self.start_source.get_width()),
        )
        self.start_image = pygame.transform.smoothscale(
            self.start_source,
            (start_width, start_height),
        )

        arrow_height = max(1, round(min(height * 0.13, width * 0.08)))
        arrow_width = max(
            1,
            round(arrow_height * self.left_source.get_width() / self.left_source.get_height()),
        )
        self.left_image = pygame.transform.smoothscale(
            self.left_source,
            (arrow_width, arrow_height),
        )
        self.right_image = pygame.transform.smoothscale(
            self.right_source,
            (arrow_width, arrow_height),
        )

        preview_box = (
            max(1, round(width * 0.18)),
            max(1, round(height * 0.20)),
        )
        self.previews = {
            character_name: scale_to_fit(source, preview_box)
            for character_name, source in self.preview_sources.items()
        }
        self.heading_font = pygame.font.Font(None, max(8, round(height * 0.045)))
        self.name_font = pygame.font.Font(None, max(8, round(height * 0.038)))

    # draw outlined text so labels stay readable over the checkerboard
    def draw_centered_text(self, surface, text, font, center, color):
        shadow = font.render(text, True, (16, 34, 70))
        label = font.render(text, True, color)
        shadow_rect = shadow.get_rect(center=(center[0] + 2, center[1] + 2))
        label_rect = label.get_rect(center=center)
        surface.blit(shadow, shadow_rect)
        surface.blit(label, label_rect)

    # draw both selectors and remember their clickable screen rectangles
    def draw(self, surface):
        self.prepare_layout(surface.get_size())
        width, height = self.layout_size
        surface.blit(self.background, (0, 0))
        self.button_rects = {}

        # snap every icon clockwise and counterclockwise twice per second
        bobble_phase = (pygame.time.get_ticks() // 250) % 2
        bobble_angle = 4 if bobble_phase == 0 else -4

        selector_y = round(height * 0.68)
        heading_y = round(height * 0.53)
        name_y = round(height * 0.80)
        preview_limit = round(width * 0.09)

        for player_index, center_x in enumerate(
            (round(width * 0.28), round(width * 0.72))
        ):
            character_name = CHARACTERS[self.selections[player_index]]
            preview = pygame.transform.rotate(
                self.previews[character_name],
                bobble_angle,
            )
            preview_rect = preview.get_rect(center=(center_x, selector_y))
            surface.blit(preview, preview_rect)

            left_image = pygame.transform.rotate(self.left_image, bobble_angle)
            right_image = pygame.transform.rotate(self.right_image, bobble_angle)
            left_rect = left_image.get_rect(
                center=(
                    center_x
                    - preview_limit
                    - self.left_image.get_width(),
                    selector_y,
                )
            )
            right_rect = right_image.get_rect(
                center=(
                    center_x
                    + preview_limit
                    + self.right_image.get_width(),
                    selector_y,
                )
            )
            surface.blit(left_image, left_rect)
            surface.blit(right_image, right_rect)
            self.button_rects[(player_index, -1)] = left_rect
            self.button_rects[(player_index, 1)] = right_rect

            self.draw_centered_text(
                surface,
                f"player {player_index + 1}",
                self.heading_font,
                (center_x, heading_y),
                (255, 255, 255),
            )
            self.draw_centered_text(
                surface,
                character_name,
                self.name_font,
                (center_x, name_y),
                (145, 222, 255),
            )

        start_image = pygame.transform.rotate(self.start_image, bobble_angle)
        start_rect = start_image.get_rect(
            center=(width // 2, round(height * 0.90))
        )
        surface.blit(start_image, start_rect)
        self.button_rects["start"] = start_rect

    # change one selection or report which menu control was clicked
    def handle_click(self, position):
        if self.button_rects.get("start", pygame.Rect(0, 0, 0, 0)).collidepoint(position):
            return "start"

        for player_index in range(2):
            for direction in (-1, 1):
                button_rect = self.button_rects.get((player_index, direction))
                if button_rect is not None and button_rect.collidepoint(position):
                    self.selections[player_index] = (
                        self.selections[player_index] + direction
                    ) % len(CHARACTERS)
                    return "move"
        return None

    # return the two selected character identifiers in player order
    def get_selections(self):
        return tuple(CHARACTERS[index] for index in self.selections)


class MatchTransition:
    STEP_DURATION = 0.7
    COUNTDOWN_LABELS = ("3", "2", "1", "GO!")

    def __init__(self, asset_folder):
        asset_folder = Path(asset_folder)
        menu_folder = asset_folder / "menu"
        self.background_source = pygame.image.load(
            str(menu_folder / "background.png")
        ).convert()
        self.start_source = load_cropped_image(menu_folder / "start.png")
        self.layout_size = None
        self.background = None
        self.start_image = None
        self.start_rect = pygame.Rect(0, 0, 0, 0)
        self.title_font = None
        self.counter_font = None
        self.time_up_font = None

    @property
    def countdown_duration(self):
        return self.STEP_DURATION * len(self.COUNTDOWN_LABELS)

    # cache transition artwork at the fixed gameplay canvas size
    def prepare_layout(self, size):
        if size == self.layout_size:
            return

        width, height = size
        self.layout_size = size
        self.background = pygame.transform.smoothscale(
            self.background_source,
            size,
        )
        start_width = max(1, round(min(width * 0.28, height * 0.46)))
        start_height = max(
            1,
            round(start_width * self.start_source.get_height() / self.start_source.get_width()),
        )
        self.start_image = pygame.transform.smoothscale(
            self.start_source,
            (start_width, start_height),
        )
        self.title_font = pygame.font.SysFont(
            "freesansbold",
            max(32, round(height * 0.11)),
            bold=True,
        )
        self.counter_font = pygame.font.SysFont(
            "freesansbold",
            max(80, round(height * 0.30)),
            bold=True,
        )
        self.time_up_font = pygame.font.SysFont(
            "freesansbold",
            max(52, round(height * 0.14)),
            bold=True,
        )

    # use the menu art while hiding all private gameplay information
    def draw_backdrop(self, surface, reference_surface=None):
        self.prepare_layout(surface.get_size())
        if reference_surface is None:
            surface.blit(self.background, (0, 0))
            shade_alpha = 185
        else:
            if reference_surface.get_size() == surface.get_size():
                reference = reference_surface
            else:
                reference = pygame.transform.smoothscale(
                    reference_surface,
                    surface.get_size(),
                )
            surface.blit(reference, (0, 0))
            shade_alpha = 145
        shade = pygame.Surface(surface.get_size(), pygame.SRCALPHA)
        shade.fill((5, 12, 30, shade_alpha))
        surface.blit(shade, (0, 0))

    # render chunky arcade text with a thick outline and drop shadow
    def draw_arcade_text(self, surface, text, font, center, color, outline=6):
        label = font.render(text, True, color)
        border = font.render(text, True, (10, 24, 58))
        for offset_x, offset_y in (
            (-outline, 0),
            (outline, 0),
            (0, -outline),
            (0, outline),
            (-outline, -outline),
            (outline, -outline),
            (-outline, outline),
            (outline, outline),
        ):
            surface.blit(
                border,
                border.get_rect(
                    center=(center[0] + offset_x, center[1] + offset_y)
                ),
            )
        surface.blit(label, label.get_rect(center=center))

    # draw a private device-handoff screen with a central start button
    def draw_handoff(
        self,
        surface,
        title,
        reference_surface=None,
    ):
        self.draw_backdrop(surface, reference_surface)
        width, height = surface.get_size()
        self.draw_arcade_text(
            surface,
            title.upper(),
            self.title_font,
            (width // 2, round(height * 0.35)),
            (115, 218, 255),
        )
        pulse = 1.0 + 0.035 * abs(
            ((pygame.time.get_ticks() % 700) / 350) - 1.0
        )
        button_size = (
            max(1, round(self.start_image.get_width() * pulse)),
            max(1, round(self.start_image.get_height() * pulse)),
        )
        button = pygame.transform.smoothscale(self.start_image, button_size)
        self.start_rect = button.get_rect(
            center=(width // 2, round(height * 0.66))
        )
        surface.blit(button, self.start_rect)

    # draw one popping mario-kart-style countdown number
    def draw_countdown(self, surface, elapsed, reference_surface=None):
        self.draw_backdrop(surface, reference_surface)
        width, height = surface.get_size()
        step = min(
            len(self.COUNTDOWN_LABELS) - 1,
            int(elapsed / self.STEP_DURATION),
        )
        local_progress = (elapsed % self.STEP_DURATION) / self.STEP_DURATION
        label_text = self.COUNTDOWN_LABELS[step]
        color = (93, 238, 132) if label_text == "GO!" else (255, 218, 74)

        base_label = self.counter_font.render(label_text, True, color)
        pop_scale = 1.0 + 0.55 * max(0.0, 1.0 - local_progress * 4.0)
        label = pygame.transform.smoothscale(
            base_label,
            (
                max(1, round(base_label.get_width() * pop_scale)),
                max(1, round(base_label.get_height() * pop_scale)),
            ),
        )
        border = pygame.mask.from_surface(label).to_surface(
            setcolor=(10, 24, 58, 255),
            unsetcolor=(0, 0, 0, 0),
        )
        border = pygame.transform.smoothscale(
            border,
            (label.get_width() + 18, label.get_height() + 18),
        )
        center = width // 2, height // 2
        surface.blit(border, border.get_rect(center=center))
        surface.blit(label, label.get_rect(center=center))

        ring_radius = round(95 + local_progress * 110)
        ring_surface = pygame.Surface(surface.get_size(), pygame.SRCALPHA)
        pygame.draw.circle(
            ring_surface,
            (*color, max(0, round(120 * (1.0 - local_progress)))),
            center,
            ring_radius,
            max(2, round(height * 0.008)),
        )
        surface.blit(ring_surface, (0, 0))

    # briefly freeze on the completed turn before showing the handoff
    def draw_times_up(self, surface, elapsed, reference_surface=None):
        self.draw_backdrop(surface, reference_surface)
        width, height = surface.get_size()
        pulse = 1.0 + 0.06 * math.sin(elapsed * math.tau * 3)
        base_label = self.time_up_font.render(
            "TIME'S UP!",
            True,
            (255, 88, 68),
        )
        label = pygame.transform.smoothscale(
            base_label,
            (
                max(1, round(base_label.get_width() * pulse)),
                max(1, round(base_label.get_height() * pulse)),
            ),
        )
        border = pygame.mask.from_surface(label).to_surface(
            setcolor=(10, 24, 58, 255),
            unsetcolor=(0, 0, 0, 0),
        )
        border = pygame.transform.smoothscale(
            border,
            (label.get_width() + 16, label.get_height() + 16),
        )
        center = width // 2, height // 2
        surface.blit(border, border.get_rect(center=center))
        surface.blit(label, label.get_rect(center=center))

    def start_clicked(self, position):
        return self.start_rect.collidepoint(position)
