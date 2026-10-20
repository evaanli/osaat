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

    # resize every frame from its original image
    def set_size(self, size):
        width, height = size
        self.width = max(1, round(width))
        self.height = max(1, round(height))
        self.frames = [
            pygame.transform.smoothscale(frame, self.size)
            for frame in self.original_frames
        ]

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
