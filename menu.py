from pathlib import Path

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

        # snap every icon right and left twice per second
        bobble_distance = max(1, round(min(width, height) * 0.006))
        bobble_phase = (pygame.time.get_ticks() // 250) % 2
        bobble_offset = bobble_distance if bobble_phase == 0 else -bobble_distance

        selector_y = round(height * 0.68)
        heading_y = round(height * 0.53)
        name_y = round(height * 0.80)
        preview_limit = round(width * 0.09)

        for player_index, center_x in enumerate(
            (round(width * 0.28), round(width * 0.72))
        ):
            character_name = CHARACTERS[self.selections[player_index]]
            preview = self.previews[character_name]
            preview_rect = preview.get_rect(
                center=(center_x + bobble_offset, selector_y)
            )
            surface.blit(preview, preview_rect)

            left_rect = self.left_image.get_rect(
                center=(
                    center_x
                    - preview_limit
                    - self.left_image.get_width()
                    + bobble_offset,
                    selector_y,
                )
            )
            right_rect = self.right_image.get_rect(
                center=(
                    center_x
                    + preview_limit
                    + self.right_image.get_width()
                    + bobble_offset,
                    selector_y,
                )
            )
            surface.blit(self.left_image, left_rect)
            surface.blit(self.right_image, right_rect)
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

        start_rect = self.start_image.get_rect(
            center=(width // 2 + bobble_offset, round(height * 0.90))
        )
        surface.blit(self.start_image, start_rect)
        self.button_rects["start"] = start_rect

    # change one selection or report that the start button was clicked
    def handle_click(self, position):
        if self.button_rects.get("start", pygame.Rect(0, 0, 0, 0)).collidepoint(position):
            return True

        for player_index in range(2):
            for direction in (-1, 1):
                button_rect = self.button_rects.get((player_index, direction))
                if button_rect is not None and button_rect.collidepoint(position):
                    self.selections[player_index] = (
                        self.selections[player_index] + direction
                    ) % len(CHARACTERS)
                    return False
        return False

    # return the two selected character identifiers in player order
    def get_selections(self):
        return tuple(CHARACTERS[index] for index in self.selections)
