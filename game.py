import pygame
import player
import controls
import record
import replay
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
player1_speed = 5

# initialize player 2
player2 = player.Player()
player2.x = 400
player2.y = 300
player2.color = BLUE
player2_speed = 10

running = True

# initialize recording system
recording_system = record.RecordSystem()
replay_system = None
phase = "ready"
pause_start = 0

while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        # single key press
        if event.type == pygame.KEYDOWN:
            # start recording when user presses space key
            if event.key == pygame.K_SPACE and phase == "ready":
                recording_system.clear()
                recording_system.timer_system.restart()
                phase = "recording1"

    if not running:
        break

    screen.fill(BLACK)

    # wait for recording to start
    if phase == "ready":
        player1.draw(screen)

    # player 1
    elif phase == "recording1":
        # convert player movements into x_vel and y_vel
        player_movements = controls.return_movements()
        player1.x_vel += player_movements[0][1] * player1_speed
        player1.y_vel += player_movements[0][0] * player1_speed

        player1.update()

        # record player data
        recording_system.record(player1, 1)
        player1.draw(screen)

        # if it's greater than one then
        if recording_system.timer_system.get_timestamp() >= 1:
            phase = "pause1"
            pause_start = pygame.time.get_ticks()

    # pause before player 2
    elif phase == "pause1":
        if pygame.time.get_ticks() - pause_start >= 1000:
            recording_system.timer_system.restart()
            phase = "recording2"

        player1.draw(screen)

    # player 2
    elif phase == "recording2":
        # convert player movements into x_vel and y_vel
        player_movements = controls.return_movements()
        player2.x_vel += player_movements[1][1] * player2_speed
        player2.y_vel += player_movements[1][0] * player2_speed

        player2.update()

        # record player data
        recording_system.record(player2, 2)
        player2.draw(screen)

        # if it's greater than one then
        if recording_system.timer_system.get_timestamp() >= 1:
            phase = "pause2"
            pause_start = pygame.time.get_ticks()

    # pause before replay
    elif phase == "pause2":
        if pygame.time.get_ticks() - pause_start >= 1000:
            replay_system = replay.ReplaySystem(
                recording_system.player1_positions,
                recording_system.player2_positions,
            )
            replay_system.restart()
            phase = "replay"

        player2.draw(screen)

    # replay both players
    elif phase == "replay":
        finished = replay_system.play_out(player1, player2)

        player1.draw(screen)
        player2.draw(screen)

        if finished:
            phase = "done"

    # show final replay frame
    elif phase == "done":
        player1.draw(screen)
        player2.draw(screen)

    pygame.display.flip()

    clock.tick(FPS)

pygame.quit()
sys.exit()
