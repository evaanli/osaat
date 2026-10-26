import pygame
import audio
import player
import gameplay
import menu
import projectile
import sys
from pathlib import Path

pygame.init()

# initialize screen
screen = pygame.display.set_mode(gameplay.GAME_SIZE, pygame.RESIZABLE)
pygame.display.set_caption("Fiendish Food Fights")
# gameplay always draws at this resolution before window scaling
game_surface = pygame.Surface(gameplay.GAME_SIZE).convert()

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
# charge, fire, then finish the reload before another shot can begin
MR_DONALD_PROJECTILE_COOLDOWN = 1.75
# center both directions on the middle of the tank tracks
MR_DONALD_SPRITE_CENTERS = {
    "left": (96, 97.5),
    "right": (59, 97.5),
}
# fifty hp lets the tank survive nine potion hits
MR_DONALD_MAX_HP = 50


# build a fighter from the character selected for either player slot
def create_character(character_name, player_number):
    if character_name == "mr donald":
        player_obj = player.Player(
            MR_DONALD_SPRITES,
            sprite_frame_time_ms=MR_DONALD_FRAME_TIME_MS,
            sprite_size=MR_DONALD_SIZE,
            hitbox_size=MR_DONALD_HITBOX_SIZE,
            hitbox_offset=MR_DONALD_HITBOX_OFFSET,
            sprite_centers=MR_DONALD_SPRITE_CENTERS,
            max_hp=MR_DONALD_MAX_HP,
            direction_follows_mouse=True,
            projectile_type="cannon",
            projectile_cooldown=MR_DONALD_PROJECTILE_COOLDOWN,
        )
        player_obj.move_speed = 1
    else:
        player_obj = player.Player(
            DORY_SPRITES,
            sprite_frame_time_ms=DORY_FRAME_TIME_MS,
            sprite_size=DORY_SIZE,
            hitbox_size=DORY_HITBOX_SIZE,
            sprite_centers=DORY_SPRITE_CENTERS,
            projectile_cooldown=DORY_POTION_COOLDOWN,
        )
        player_obj.move_speed = 2

    player_obj.character_name = character_name
    if player_number == 1:
        player_obj.x = 300
        player_obj.y = 260
        player_obj.color = RED
    else:
        player_obj.x = 1050
        player_obj.y = 240
        player_obj.color = BLUE
    return player_obj


# show a frame before decoding the larger game and menu artwork
def draw_loading_screen():
    screen.fill((18, 24, 38))
    loading_font = pygame.font.Font(None, 56)
    loading_text = loading_font.render("loading...", True, WHITE)
    screen.blit(
        loading_text,
        loading_text.get_rect(center=screen.get_rect().center),
    )
    pygame.display.flip()
    pygame.event.pump()


draw_loading_screen()
# avoid decoding projectile artwork on the first attack
projectile.Potion.preload_assets()
projectile.CannonBall.preload_assets()
character_menu = menu.CharacterMenu(ASSET_FOLDER)
match_transition = menu.MatchTransition(ASSET_FOLDER)
match_replay_controls = menu.MatchReplayControls()
audio_system = audio.AudioSystem(ASSET_FOLDER)
audio_system.play_menu_music()

# game config
running = True
game = gameplay.Game(FPS)
player1 = None
player2 = None
phase = "menu"
# each private recording turn lasts exactly seven seconds
recording_time = 7000
handoff_target = None
handoff_title = ""
countdown_target = None
countdown_start = 0
countdown_sound_step = -1
round_reference_surface = None
times_up_start = 0
times_up_target = None
times_up_surface = None
times_up_duration = 1000
end_replay_time = 0.0
end_replay_playing = True
end_replay_dragging = False
end_replay_resume_after_drag = False
end_replay_seek_pending = False

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
    "handoff",
    "countdown",
    "times_up",
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
            if event.key == pygame.K_h and phase in GAMEPLAY_PHASES:
                # show or hide the friendly collision squares
                game.toggle_hitboxes()
            elif (event.key == pygame.K_SPACE and phase == "ready"):
                # the first round also starts the full match recording
                if not game.match_recording:
                    game.initialize_match_recording()
                game.initialize_recording()
                phase = "record1"
            elif event.key == pygame.K_SPACE and phase == "game_over":
                end_replay_playing = not end_replay_playing
                audio_system.play("ui_start")
            elif event.key == pygame.K_BACKSPACE and phase == "game_over":
                # restart the finished-match video from the beginning
                end_replay_time = 0.0
                end_replay_playing = True
                end_replay_seek_pending = True
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if phase == "menu":
                menu_action = character_menu.handle_click(event.pos)
                if menu_action == "move":
                    audio_system.play("ui_move")
                elif menu_action == "start":
                    audio_system.play("ui_start")
                    audio_system.play_battle_music()
                    player1_name, player2_name = character_menu.get_selections()
                    player1 = create_character(player1_name, 1)
                    player2 = create_character(player2_name, 2)
                    game.initialize_match_recording()
                    round_reference_surface = game.capture_round_reference(
                        player1,
                        player2,
                    )
                    handoff_target = "record1"
                    handoff_title = "player 1's turn"
                    phase = "handoff"
            elif phase == "handoff":
                target = game.window_to_game(event.pos, screen.get_size())
                if target is not None and match_transition.start_clicked(target):
                    audio_system.play("ui_start")
                    countdown_target = handoff_target
                    countdown_start = pygame.time.get_ticks()
                    countdown_sound_step = -1
                    phase = "countdown"
            elif phase == "game_over":
                target = game.window_to_game(event.pos, screen.get_size())
                if target is not None:
                    replay_action = match_replay_controls.get_action(target)
                    if replay_action == "back":
                        audio_system.play("ui_start")
                        audio_system.stop_music()
                        audio_system.play_menu_music()
                        game = gameplay.Game(FPS)
                        player1 = None
                        player2 = None
                        round_reference_surface = None
                        phase = "menu"
                    elif replay_action == "play_again":
                        audio_system.play("ui_start")
                        player1_name = player1.character_name
                        player2_name = player2.character_name
                        game = gameplay.Game(FPS)
                        player1 = create_character(player1_name, 1)
                        player2 = create_character(player2_name, 2)
                        game.initialize_match_recording()
                        round_reference_surface = game.capture_round_reference(
                            player1,
                            player2,
                        )
                        handoff_target = "record1"
                        handoff_title = "player 1's turn"
                        end_replay_dragging = False
                        phase = "handoff"
                    elif replay_action == "toggle":
                        audio_system.play("ui_start")
                        end_replay_playing = not end_replay_playing
                    elif replay_action == "timeline":
                        end_replay_resume_after_drag = end_replay_playing
                        end_replay_playing = False
                        end_replay_dragging = True
                        end_replay_time = (
                            match_replay_controls.get_timeline_fraction(target)
                            * game.match_replay_system.duration
                        )
                        end_replay_seek_pending = True
            else:
                target = game.window_to_game(event.pos, screen.get_size())
                # clicks in a black letterbox bar do not enter gameplay
                if target is not None:
                    if phase == "record1":
                        thrown = game.throw_projectile(player1, target, 1)
                    elif phase == "record2":
                        thrown = game.throw_projectile(player2, target, 2)
                    else:
                        thrown = None
                    if thrown is not None:
                        audio_system.play(
                            "cannon_charge"
                            if thrown.type == "cannon"
                            else "potion_throw"
                        )
        elif event.type == pygame.MOUSEMOTION and end_replay_dragging:
            target = game.window_to_game(event.pos, screen.get_size())
            if target is not None:
                end_replay_time = (
                    match_replay_controls.get_timeline_fraction(target)
                    * game.match_replay_system.duration
                )
                end_replay_seek_pending = True
        elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
            if end_replay_dragging:
                target = game.window_to_game(event.pos, screen.get_size())
                if target is not None:
                    end_replay_time = (
                        match_replay_controls.get_timeline_fraction(target)
                        * game.match_replay_system.duration
                    )
                end_replay_dragging = False
                end_replay_playing = end_replay_resume_after_drag
                end_replay_seek_pending = True

    # convert the mouse only while the fixed gameplay canvas is active
    mouse_game_position = None
    if phase in GAMEPLAY_PHASES:
        mouse_game_position = game.window_to_game(
            pygame.mouse.get_pos(),
            screen.get_size(),
        )
    if mouse_game_position is not None:
        if phase == "record1" and player1.direction_follows_mouse:
            player1.face_towards_x(mouse_game_position[0])
        elif phase == "record2" and player2.direction_follows_mouse:
            player2.face_towards_x(mouse_game_position[0])

    # only throws owned by the player recording this turn can move
    if phase == "record1":
        live_audio_events = game.update_projectiles(dt, 1, player1)
    elif phase == "record2":
        live_audio_events = game.update_projectiles(dt, 2, player2)
    else:
        live_audio_events = []
    for sound_name in live_audio_events:
        audio_system.play(sound_name)

    # remember which phase was actually drawn this frame
    rendered_phase = phase
    gameplay_frame = rendered_phase in GAMEPLAY_PHASES
    render_surface = game_surface if gameplay_frame else screen
    render_surface.fill(BLACK)

    # character selection uses the full resizable window
    if phase == "menu":
        character_menu.draw(render_surface)

    # hide private movement while the device changes hands
    elif phase == "handoff":
        match_transition.draw_handoff(
            render_surface,
            handoff_title,
            round_reference_surface,
        )

    # count down before revealing and advancing the next timeline
    elif phase == "countdown":
        countdown_elapsed = (
            pygame.time.get_ticks() - countdown_start
        ) / 1000.0
        countdown_step = min(
            len(match_transition.COUNTDOWN_LABELS) - 1,
            int(countdown_elapsed / match_transition.STEP_DURATION),
        )
        if countdown_step != countdown_sound_step:
            audio_system.play("countdown")
            countdown_sound_step = countdown_step
        match_transition.draw_countdown(
            render_surface,
            countdown_elapsed,
            round_reference_surface,
        )
        if countdown_elapsed >= match_transition.countdown_duration:
            if countdown_target == "record1":
                game.initialize_recording()
            elif countdown_target == "record2":
                game.start_record2(player1)
            elif countdown_target == "replay":
                game.start_replay()
            phase = countdown_target

    # hold the completed turn for one second before changing hands
    elif phase == "times_up":
        times_up_elapsed = (
            pygame.time.get_ticks() - times_up_start
        ) / 1000.0
        match_transition.draw_times_up(
            render_surface,
            times_up_elapsed,
            times_up_surface,
        )
        if pygame.time.get_ticks() - times_up_start >= times_up_duration:
            handoff_target = times_up_target
            if times_up_target == "record2":
                handoff_title = "player 2's turn"
            else:
                handoff_title = "watch replay"
            phase = "handoff"

    # phase ready
    elif phase == "ready":
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
            times_up_start = pygame.time.get_ticks()
            times_up_target = "record2"
            times_up_surface = game_surface.copy()
            phase = "times_up"

    # pause between recording
    elif phase == "pause1":
        game.pause1(render_surface, player1, player2)

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
            times_up_start = pygame.time.get_ticks()
            times_up_target = "replay"
            times_up_surface = game_surface.copy()
            phase = "times_up"

    # pause after player 2 recording
    elif phase == "pause2":
        game.pause2(render_surface, player1, player2)

    # replays the two player's recordings
    elif phase == "replay":
        finished = game.replay(render_surface, player1, player2)
        for sound_name in game.pop_audio_events():
            audio_system.play(sound_name)
        if game.dead_player_number is not None:
            # save the full match as soon as a player dies
            game.finish_match_recording(game.death_replay_time)
            game.start_death_animation(game.dead_player_number)
            audio_system.play("knockout")
            phase = "death"
        elif finished:
            round_reference_surface = game.capture_round_reference(
                player1,
                player2,
            )
            handoff_target = "record1"
            handoff_title = "player 1's turn"
            phase = "handoff"

    # final render
    elif phase == "done":
        game.done(render_surface, player1, player2)

    # replay the complete saved match
    elif phase == "match_replay":
        finished = game.replay_match(render_surface, player1, player2)
        for sound_name in game.pop_audio_events():
            audio_system.play(sound_name)
        if game.dead_player_number is not None:
            game.start_death_animation(game.dead_player_number)
            audio_system.play("knockout")
            phase = "death"
        elif finished:
            phase = "game_over"

    # play the death animation over the black background
    elif phase == "death":
        if game.death_animation(render_surface, dt, player1, player2):
            audio_system.stop_music()
            audio_system.play("victory")
            game.start_match_viewer(player1, player2)
            end_replay_time = 0.0
            end_replay_playing = True
            end_replay_dragging = False
            end_replay_seek_pending = False
            audio_system.play_battle_music()
            phase = "game_over"

    # play the full saved match behind video-style end controls
    elif phase == "game_over":
        replay_duration = game.match_replay_system.duration
        if end_replay_playing and not end_replay_dragging:
            end_replay_time = min(
                replay_duration,
                end_replay_time + dt,
            )
            if end_replay_time >= replay_duration:
                end_replay_playing = False

        if end_replay_dragging:
            replay_draw_time = game.match_replay_system.last_time
            replay_audio_enabled = False
        else:
            replay_draw_time = end_replay_time
            replay_audio_enabled = (
                end_replay_playing and not end_replay_seek_pending
            )

        game.draw_match_viewer(
            render_surface,
            player1,
            player2,
            replay_draw_time,
            play_sounds=replay_audio_enabled,
        )
        for sound_name in game.pop_audio_events():
            audio_system.play(sound_name)
        if not end_replay_dragging:
            end_replay_seek_pending = False

        if game.winner_player_number == 0:
            winner_color = WHITE
        elif game.winner_player_number == 1:
            winner_color = player1.color
        else:
            winner_color = player2.color
        match_replay_controls.draw(
            render_surface,
            game.winner_player_number,
            winner_color,
            end_replay_time,
            replay_duration,
            end_replay_playing,
        )

    # do not advance animations during a phase change or frozen phase
    stable_phase = phase if phase == rendered_phase else None
    if player1 is not None and player2 is not None:
        game.update_sprites(
            dt,
            player1,
            player2,
            player1_active=stable_phase in (
                "record1",
                "replay",
                "match_replay",
                "game_over",
            ),
            player2_active=stable_phase in (
                "record2",
                "replay",
                "match_replay",
                "game_over",
            ),
        )

    if gameplay_frame:
        game.draw_game_to_window(screen, game_surface)

    pygame.display.flip()

pygame.quit()
sys.exit()
