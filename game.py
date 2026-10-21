import pygame
import player
import gameplay
import projectile
import sys
from pathlib import Path

pygame.init()

# initialize screen
screen = pygame.display.set_mode(gameplay.GAME_SIZE, pygame.RESIZABLE)
pygame.display.set_caption("OSAAT")
# gameplay always draws at this resolution before window scaling
game_surface = pygame.Surface(gameplay.GAME_SIZE).convert()
# avoid decoding the large potion png files on the first throw
projectile.Potion.preload_assets()
projectile.CannonBall.preload_assets()

# fps config
clock = pygame.time.Clock()
FPS = 60

# colours
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
RED = (197, 17, 17)
BLUE = (0, 128, 255)

# character animation settings
ASSET_FOLDER = Path(__file__).resolve().parent / "assets"

DORY_SPRITES = ASSET_FOLDER / "dory_to"
# both fighters and their collision shapes use half of their original size
DORY_SIZE = (75, 75)
DORY_HITBOX_SIZE = (28, 28)
DORY_FRAME_TIME_MS = 200
DORY_POTION_COOLDOWN = 0.33
# center each pose on its visible artwork instead of transparent padding
DORY_SPRITE_CENTERS = {
    "idle": (47.25, 37.5),
    "walk_left": (40.5, 37.5),
    "walk_right": (40.5, 37.5),
}
MR_DONALD_SPRITES = ASSET_FOLDER / "mr_donald"
MR_DONALD_SIZE = (150, 150)
MR_DONALD_FRAME_TIME_MS = 100
MR_DONALD_HITBOX_SIZE = (100, 28)
MR_DONALD_HITBOX_OFFSET = (-13, 0)
# center both directions on the middle of the tank tracks
MR_DONALD_SPRITE_CENTERS = {
    "left": (96, 97.5),
    "right": (59, 97.5),
}
# fifty hp lets the tank survive nine potion hits
MR_DONALD_MAX_HP = 50

# initialize player 1
player1 = player.Player(
    DORY_SPRITES,
    sprite_frame_time_ms=DORY_FRAME_TIME_MS,
    sprite_size=DORY_SIZE,
    hitbox_size=DORY_HITBOX_SIZE,
    sprite_centers=DORY_SPRITE_CENTERS,
    projectile_cooldown=DORY_POTION_COOLDOWN,
)
# spawn dory in the left middle walkway
player1.x = 300
player1.y = 260
player1.color = RED

# initialize player 2
player2 = player.Player(
    MR_DONALD_SPRITES,
    sprite_frame_time_ms=MR_DONALD_FRAME_TIME_MS,
    sprite_size=MR_DONALD_SIZE,
    hitbox_size=MR_DONALD_HITBOX_SIZE,
    hitbox_offset=MR_DONALD_HITBOX_OFFSET,
    sprite_centers=MR_DONALD_SPRITE_CENTERS,
    max_hp=MR_DONALD_MAX_HP,
    direction_follows_mouse=True,
    projectile_type="cannon",
)
# spawn mr donald in the right middle walkway
player2.x = 1050
player2.y = 240
player2.color = BLUE

# game config
running = True
game = gameplay.Game(FPS)
phase = "ready"
pause_start = 0
recording_time = 5000
pause_time = 3000

# only match phases use the fixed aspect ratio canvas
GAMEPLAY_PHASES = {
    "ready",
    "record1",
    "pause1",
    "record2",
    "pause2",
    "replay",
    "done",
    "match_replay",
    "death",
    "game_over",
}

# game loop
while running:
    # deltatime
    dt = clock.tick(FPS) / 1000.0

    # check events
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        elif event.type == pygame.VIDEORESIZE:
            # menus can later use this full window size directly
            screen = pygame.display.set_mode(
                (max(1, event.w), max(1, event.h)),
                pygame.RESIZABLE,
            )
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_h:
                # show or hide the friendly collision squares
                game.toggle_hitboxes()
            elif (event.key == pygame.K_SPACE and phase == "ready"):
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
            target = game.window_to_game(event.pos, screen.get_size())
            # clicks in a black letterbox bar do not enter gameplay
            if target is not None:
                if phase == "record1":
                    game.throw_projectile(player1, target, 1)
                elif phase == "record2":
                    game.throw_projectile(player2, target, 2)

    # convert the mouse for dory's preview and mr donald's horizontal aim
    mouse_game_position = game.window_to_game(
        pygame.mouse.get_pos(),
        screen.get_size(),
    )
    if phase == "record2" and mouse_game_position is not None:
        player2.face_towards_x(mouse_game_position[0])

    # only throws owned by the player recording this turn can move
    if phase == "record1":
        game.update_projectiles(dt, 1, player1)
    elif phase == "record2":
        game.update_projectiles(dt, 2, player2)

    # remember which phase was actually drawn this frame
    rendered_phase = phase
    gameplay_frame = rendered_phase in GAMEPLAY_PHASES
    render_surface = game_surface if gameplay_frame else screen
    render_surface.fill(BLACK)

    # phase ready
    if phase == "ready":
        game.ready(render_surface, player1, player2)

    # recording player 1
    elif phase == "record1":
        if game.record1(
            render_surface,
            dt,
            player1,
            player2,
            recording_time,
            mouse_game_position,
        ): # returns true when done
            phase = "pause1"
            pause_start = pygame.time.get_ticks()

    # pause between recording
    elif phase == "pause1":
        game.pause1(render_surface, player1, player2)
        if pygame.time.get_ticks() - pause_start >= pause_time: # pause time in ms
            # if times up then we start recording
            game.start_record2(player1)
            phase = "record2"

    # recording player 2
    elif phase == "record2":
        if game.record2(
            render_surface,
            dt,
            player1,
            player2,
            recording_time,
            mouse_game_position,
        ): # returns true when done
            phase = "pause2"
            pause_start = pygame.time.get_ticks()

    # pause after player 2 recording
    elif phase == "pause2":
        game.pause2(render_surface, player1, player2)

        if pygame.time.get_ticks() - pause_start >= pause_time:
            game.start_replay()
            phase = "replay" # goes to replay

    # replays the two player's recordings
    elif phase == "replay":
        finished = game.replay(render_surface, player1, player2)
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
        game.done(render_surface, player1, player2)
        if pygame.time.get_ticks() - pause_start >= pause_time:
            phase = "ready" # restart the gameplay

    # replay the complete saved match
    elif phase == "match_replay":
        finished = game.replay_match(render_surface, player1, player2)
        if game.dead_player_number is not None:
            game.start_death_animation(game.dead_player_number)
            phase = "death"
        elif finished:
            phase = "game_over"

    # play the death animation over the black background
    elif phase == "death":
        if game.death_animation(render_surface, dt, player1, player2):
            phase = "game_over"

    # freeze on black until backspace is pressed
    elif phase == "game_over":
        game.draw_winner(render_surface, player1, player2)

    # do not advance animations during a phase change or frozen phase
    stable_phase = phase if phase == rendered_phase else None
    game.update_sprites(
        dt,
        player1,
        player2,
        player1_active=stable_phase in ("record1", "replay", "match_replay"),
        player2_active=stable_phase in ("record2", "replay", "match_replay"),
    )

    if gameplay_frame:
        game.draw_game_to_window(screen, game_surface)

    pygame.display.flip()

pygame.quit()
sys.exit()
