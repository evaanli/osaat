from pathlib import Path

import pygame


# animated sprite loaded from numbered png files
class Sprite:
    MIN_FRAME_TIME_MS = 1.0

    def __init__(
        self,
        folder,
        frame_time_ms=100,
        size=None,
        loop=True,
        center=None,
    ):
        # sprite settings
        self.folder = Path(folder)
        self.loop = loop
        self.playing = True
        self.visible = True
        self.flip_x = False
        self.flip_y = False

        # animation state
        self.current_frame = 0
        self.elapsed_ms = 0.0
        self._frame_time_ms = 0.0
        self.frame_time_ms = frame_time_ms

        # keep original frames so resizing never lowers their source quality
        self.original_frames = self.load_frames()
        self.frames = []

        if size is None:
            size = self.original_frames[0].get_size()
        self.set_size(size)
        self.center = (
            center
            if center is not None
            else (self.width / 2, self.height / 2)
        )

    # load numbered frames in their numerical order
    def load_frames(self):
        if not self.folder.is_dir():
            raise FileNotFoundError(f"sprite folder does not exist: {self.folder}")

        frame_paths = sorted(
            (
                path
                for path in self.folder.glob("*.png")
                if path.stem.isdigit()
            ),
            key=lambda path: int(path.stem),
        )

        if not frame_paths or frame_paths[0].stem != "0":
            raise FileNotFoundError(
                f"sprite folder needs a 0.png frame: {self.folder}"
            )

        frames = []
        for frame_path in frame_paths:
            frame = pygame.image.load(str(frame_path))
            # alpha conversion needs an active display surface
            if pygame.display.get_surface() is not None:
                frame = frame.convert_alpha()
            else:
                frame = frame.copy()
            frames.append(frame)

        return frames

    # zero freezes the animation and positive values cannot go below one ms
    @property
    def frame_time_ms(self):
        return self._frame_time_ms

    @frame_time_ms.setter
    def frame_time_ms(self, value):
        value = float(value)
        if value < 0:
            raise ValueError("frame time cannot be negative")
        self._frame_time_ms = (
            0.0 if value == 0 else max(self.MIN_FRAME_TIME_MS, value)
        )

    # return the current drawing size
    @property
    def size(self):
        return self.width, self.height

    @size.setter
    def size(self, value):
        self.set_size(value)

    # return the custom center at the current sprite size
    @property
    def center(self):
        return (
            self.width * self._center_ratio[0],
            self.height * self._center_ratio[1],
        )

    @center.setter
    def center(self, value):
        self._center_ratio = (
            float(value[0]) / self.width,
            float(value[1]) / self.height,
        )

    # get the center after any sprite flips
    def get_center(self):
        center_x, center_y = self.center
        if self.flip_x:
            center_x = self.width - center_x
        if self.flip_y:
            center_y = self.height - center_y
        return center_x, center_y

    # resize every frame from its original image
    def set_size(self, size):
        width, height = size
        self.width = max(1, round(width))
        self.height = max(1, round(height))
        self.frames = [
            pygame.transform.smoothscale(frame, self.size)
            for frame in self.original_frames
        ]
        # cache visible bounds so transparent png padding does not affect hitboxes
        self.opaque_rects = [
            frame.get_bounding_rect(min_alpha=1)
            for frame in self.frames
        ]
        # cache both visible edge points for things such as weapon nozzles
        self.edge_points = [
            {
                "left": self.find_edge_point(frame, "left"),
                "right": self.find_edge_point(frame, "right"),
            }
            for frame in self.frames
        ]

    # find the middle of one visible edge without transparent png padding
    def find_edge_point(self, frame, direction):
        opaque_rect = frame.get_bounding_rect(min_alpha=16)
        if opaque_rect.width == 0 or opaque_rect.height == 0:
            return self.width / 2, self.height / 2

        edge_width = min(5, opaque_rect.width)
        if direction == "left":
            x_values = range(opaque_rect.left, opaque_rect.left + edge_width)
            edge_x = opaque_rect.left
        else:
            x_values = range(opaque_rect.right - edge_width, opaque_rect.right)
            edge_x = opaque_rect.right - 1

        visible_y_values = []
        for x in x_values:
            for y in range(opaque_rect.top, opaque_rect.bottom):
                if frame.get_at((x, y)).a >= 16:
                    visible_y_values.append(y)

        if not visible_y_values:
            return edge_x, opaque_rect.centery

        edge_y = (min(visible_y_values) + max(visible_y_values)) / 2
        return edge_x, edge_y

    # change the delay between frame changes
    def set_frame_speed(self, frame_time_ms):
        self.frame_time_ms = frame_time_ms

    # select a frame and clear leftover animation time
    def set_frame(self, frame_number):
        self.current_frame = max(
            0,
            min(int(frame_number), len(self.frames) - 1),
        )
        self.elapsed_ms = 0.0

    # resume from the current frame
    def play(self):
        self.playing = True

    # stop on the current frame
    def pause(self):
        self.playing = False

    # return to the first frame and start playing
    def restart(self):
        self.current_frame = 0
        self.elapsed_ms = 0.0
        self.playing = True

    # move through as many frames as the elapsed time requires
    def update(self, dt):
        if (
            not self.playing
            or self.frame_time_ms == 0
            or len(self.frames) <= 1
        ):
            return

        self.elapsed_ms += max(0.0, dt) * 1000.0
        frame_changes = int(self.elapsed_ms // self.frame_time_ms)
        if frame_changes == 0:
            return

        self.elapsed_ms %= self.frame_time_ms
        next_frame = self.current_frame + frame_changes

        if self.loop:
            self.current_frame = next_frame % len(self.frames)
        elif next_frame >= len(self.frames):
            self.current_frame = len(self.frames) - 1
            self.elapsed_ms = 0.0
            self.playing = False
        else:
            self.current_frame = next_frame

    # get the frame currently used for drawing
    def get_image(self):
        image = self.frames[self.current_frame]
        if self.flip_x or self.flip_y:
            image = pygame.transform.flip(image, self.flip_x, self.flip_y)
        return image

    # get the visible bounds of the current frame after any flips
    def get_opaque_rect(self):
        opaque_rect = self.opaque_rects[self.current_frame].copy()

        if self.flip_x:
            opaque_rect.x = self.width - opaque_rect.right
        if self.flip_y:
            opaque_rect.y = self.height - opaque_rect.bottom

        return opaque_rect

    # get a visible left or right edge point after any sprite flips
    def get_edge_point(self, direction):
        source_direction = direction
        if self.flip_x:
            source_direction = "left" if direction == "right" else "right"

        edge_x, edge_y = self.edge_points[self.current_frame][source_direction]
        if self.flip_x:
            edge_x = self.width - 1 - edge_x
        if self.flip_y:
            edge_y = self.height - 1 - edge_y
        return edge_x, edge_y

    # draw at a top left position and return the drawn rectangle
    def draw(self, surface, position):
        draw_rect = pygame.Rect(
            round(position[0]),
            round(position[1]),
            self.width,
            self.height,
        )
        if self.visible:
            surface.blit(self.get_image(), draw_rect)
        return draw_rect
