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
match_end_start = None
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
            elif (
                event.key == pygame.K_BACKSPACE
                and game.match_recording
                and match_end_start is None
            ):
                # keep recording for one final second
                match_end_start = pygame.time.get_ticks()
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if phase == "record1":
                game.throw_potion(player1, event.pos, 1)
            elif phase == "record2":
                game.throw_potion(player2, event.pos, 2)

    # Live throws continue to fly during recording and pause phases.
    if phase not in ("replay", "match_replay"):
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
        if game.replay(screen, player1, player2):
            phase = "done"
            pause_start = pygame.time.get_ticks()

    # final render
    elif phase == "done":
        game.done(screen, player1, player2)
        if pygame.time.get_ticks() - pause_start >= pause_time:
            phase = "ready" # restart the gameplay

    # continuously loop the complete match after recording ends
    elif phase == "match_replay":
        game.replay_match(screen, player1, player2)

    # backspace ends the match after one more second has been recorded
    if (
        match_end_start is not None
        and pygame.time.get_ticks() - match_end_start >= 500
    ):
        game.finish_match_recording()
        match_end_start = None
        phase = "match_replay"

    pygame.display.flip()

pygame.quit()
sys.exit()
