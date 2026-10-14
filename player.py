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

    def update(self):
        self.x += self.x_vel
        self.y += self.y_vel

        self.x_vel *= 0.6
        self.y_vel *= 0.6

        # update player rect
        self.player_rect.x = self.x
        self.player_rect.y = self.y

    def draw(self, surface):
        # rectangle for now
        pygame.draw.rect(surface, self.color, self.player_rect)
