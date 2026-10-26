from pathlib import Path

import pygame


class AudioSystem:
    def __init__(self, asset_folder):
        self.audio_folder = Path(asset_folder) / "audio"
        self.enabled = False
        self.current_music = None
        self.sounds = {}

        # some test machines do not provide an audio device
        try:
            if pygame.mixer.get_init() is None:
                pygame.mixer.init()
            self.enabled = True
        except pygame.error:
            return

        volumes = {
            "ui_move": 0.45,
            "ui_start": 0.55,
            "countdown": 0.55,
            "potion_throw": 0.55,
            "potion_break": 0.65,
            "cannon_charge": 0.55,
            "cannon_fire": 0.8,
            "cannon_reload": 0.65,
            "cannon_impact": 0.8,
            "player_hit": 0.55,
            "knockout": 0.75,
            "victory": 0.75,
        }
        for name, volume in volumes.items():
            path = self.audio_folder / "sfx" / f"{name}.wav"
            try:
                sound = pygame.mixer.Sound(str(path))
                sound.set_volume(volume)
                self.sounds[name] = sound
            except (pygame.error, FileNotFoundError):
                pass

    # play one effect without interrupting other effects
    def play(self, name):
        if self.enabled and name in self.sounds:
            self.sounds[name].play()

    # switch looping tracks only when the requested track changes
    def play_music(self, name, volume):
        if not self.enabled or self.current_music == name:
            return
        path = self.audio_folder / "music" / f"{name}.ogg"
        try:
            pygame.mixer.music.load(str(path))
            pygame.mixer.music.set_volume(volume)
            pygame.mixer.music.play(-1)
            self.current_music = name
        except (pygame.error, FileNotFoundError):
            pass

    def play_menu_music(self):
        self.play_music("menu", 0.28)

    def play_battle_music(self):
        self.play_music("battle", 0.34)

    def stop_music(self):
        if self.enabled:
            pygame.mixer.music.fadeout(250)
        self.current_music = None
