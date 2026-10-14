import pygame
import player
import controls
import sys

pygame.init()

# initialize screen
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("OSAAT")

# fps config
clock = pygame.time.Clock()
FPS = 60

# colours
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
RED = (197, 17, 17)
BLUE = (0, 128, 255)

# initialize player
player1 = player.Player()
player1.x = 400
player1.y = 300
player1.color = RED
player1_speed = 5
running = True

while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

    screen.fill(BLACK)

    # convert player movements into x_vel and y_vel
    player_movements = controls.return_movements()
    player1.x_vel += player_movements[0][1] * player1_speed
    player1.y_vel += player_movements[0][0] * player1_speed
    
    player1.update()
    player1.draw(screen)

    pygame.display.flip()

    clock.tick(FPS)

pygame.quit()
sys.exit()

