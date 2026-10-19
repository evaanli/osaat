import pygame
import player
import gameplay
import sys

pygame.init()

# initialize screen
SCREEN_WIDTH = 1200
SCREEN_HEIGHT = 860
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

# game config
running = True
game = gameplay.Game(FPS)
phase = "ready"
pause_start = 0
recording_time = 5000
pause_time = 3000

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
                # the first round also starts the full match recording
                if not game.match_recording:
                    game.initialize_match_recording()
                game.initialize_recording()
                phase = "record1"
            elif event.key == pygame.K_BACKSPACE and phase in ("death", "game_over"):
                # replay the saved match from the beginning
                if game.match_replay_system is not None:
                    game.start_match_replay(player1, player2)
                    phase = "match_replay"
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if phase == "record1":
                game.throw_potion(player1, event.pos, 1)
            elif phase == "record2":
                game.throw_potion(player2, event.pos, 2)

    # live throws continue to fly during recording and pause phases
    if phase in ("ready", "record1", "pause1", "record2", "pause2", "done"):
        game.update_projectiles(dt)

    # clear screen
    screen.fill(BLACK)

    # phase ready
    if phase == "ready":
        game.ready(screen, player1, player2)

    # recording player 1
    elif phase == "record1":
        if game.record1(screen, dt, player1, player2, recording_time): # returns true when done
            phase = "pause1"
            pause_start = pygame.time.get_ticks()

    # pause between recording
    elif phase == "pause1":
        game.pause1(screen, player1, player2)
        if pygame.time.get_ticks() - pause_start >= pause_time: # pause time in ms
            # if times up then we start recording
            game.start_record2(player1)
            phase = "record2"

    # recording player 2
    elif phase == "record2":
        if game.record2(screen, dt, player1, player2, recording_time): # returns true when done
            phase = "pause2"
            pause_start = pygame.time.get_ticks()

    # pause after player 2 recording
    elif phase == "pause2":
        game.pause2(screen, player1, player2)

        if pygame.time.get_ticks() - pause_start >= pause_time:
            game.start_replay()
            phase = "replay" # goes to replay

    # replays the two player's recordings
    elif phase == "replay":
        finished = game.replay(screen, player1, player2)
        if game.dead_player_number is not None:
            # save the full match as soon as a player dies
            game.finish_match_recording()
            game.start_death_animation(game.dead_player_number)
            phase = "death"
        elif finished:
            phase = "done"
            pause_start = pygame.time.get_ticks()

    # final render
    elif phase == "done":
        game.done(screen, player1, player2)
        if pygame.time.get_ticks() - pause_start >= pause_time:
            phase = "ready" # restart the gameplay

    # replay the complete saved match
    elif phase == "match_replay":
        finished = game.replay_match(screen, player1, player2)
        if game.dead_player_number is not None:
            game.start_death_animation(game.dead_player_number)
            phase = "death"
        elif finished:
            phase = "game_over"

    # play the death animation over the black background
    elif phase == "death":
        if game.death_animation(screen, dt, player1, player2):
            phase = "game_over"

    # freeze on black until backspace is pressed
    elif phase == "game_over":
        game.draw_winner(screen, player1, player2)

    pygame.display.flip()

pygame.quit()
sys.exit()
