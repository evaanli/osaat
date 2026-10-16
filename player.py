import pygame

class Player:
    def __init__(self):
        self.x = 0
        self.y = 0
        self.x_vel = 0
        self.y_vel = 0

        self.width = 75
        self.height = 150

        self.color = (255, 255, 255)

        # simple rectangle for drawing
        self.player_rect = pygame.Rect(self.x, self.y, self.width, self.height)

    # update physics
    def update(self, dt):
        frame_scale = dt * 60

        self.x += self.x_vel * frame_scale
        self.y += self.y_vel * frame_scale

        self.x_vel *= 0.6 ** frame_scale
        self.y_vel *= 0.6 ** frame_scale

    # draw the rectangle
    def draw(self, surface):
        # update player rect
        self.player_rect.x = self.x
        self.player_rect.y = self.y
        
        # rectangle for now
        pygame.draw.rect(surface, self.color, self.player_rect)
