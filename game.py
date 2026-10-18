import pygame
import player
import gameplay
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

# initialize player 1
player1 = player.Player()
player1.x = 400
player1.y = 300
player1.color = RED

# initialize player 2
player2 = player.Player()
player2.x = 400
player2.y = 300
player2.color = BLUE

running = True
game = gameplay.Game(FPS)
phase = "ready"
pause_start = 0

# game loop
while running:
    # deltatime
    dt = clock.tick(FPS) / 1000.0

    # check events
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        if (event.type == pygame.KEYDOWN):
            if (event.key == pygame.K_SPACE and phase == "ready"):
                game.initialize_recording()
                phase = "record1"

    # clear screen
    screen.fill(BLACK)

    # phase ready
    if phase == "ready":
        game.ready(screen, player1, player2)

    # recording player 1
    elif phase == "record1":
        if game.record1(screen, dt, player1, player2): # returns true when done
            phase = "pause1"
            pause_start = pygame.time.get_ticks()

    # pause between recording
    elif phase == "pause1":
        game.pause1(screen, player1, player2)
        if pygame.time.get_ticks() - pause_start >= 1000: # pause time in ms
            # if times up then we start recording
            game.start_record2()
            phase = "record2"

    # recording player 2
    elif phase == "record2":
        if game.record2(screen, dt, player1, player2): # returns true when done
            phase = "pause2"
            pause_start = pygame.time.get_ticks()

    # pause after player 2 recording
    elif phase == "pause2":
        game.pause2(screen, player1, player2)

        if pygame.time.get_ticks() - pause_start >= 1000:
            game.start_replay()
            phase = "replay" # goes to replay

    # replays the two player's recordings
    elif phase == "replay":
        if game.replay(screen, player1, player2):
            phase = "done"
            pause_start = pygame.time.get_ticks()

    # final render
    elif phase == "done":
        game.done(screen, player1, player2)
        if pygame.time.get_ticks() - pause_start >= 1000:
            phase = "ready" # restart the gameplay

    pygame.display.flip()

pygame.quit()
sys.exit()
