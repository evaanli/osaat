import math
import random
from time import perf_counter

import pygame

import drawing


class BattleEffects:
    def __init__(self):
        self.number_font = None
        self.reset()

    # clear short-lived visuals and reset the effect clock
    def reset(self, player1=None, player2=None):
        self.particles = []
        self.shockwaves = []
        self.damage_numbers = []
        self.flash_timers = {1: 0.0, 2: 0.0}
        self.shake_time = 0.0
        self.shake_strength = 0.0
        self.finisher_time = 0.0
        self.ghost_health = {}
        self.ghost_delays = {1: 0.0, 2: 0.0}
        if player1 is not None:
            self.ghost_health[1] = float(player1.hp)
        if player2 is not None:
            self.ghost_health[2] = float(player2.hp)
        self.last_update = perf_counter()

    # turn replay damage events into immediate visual and camera feedback
    def add_damage_events(self, events, player1, player2, replay_system):
        players = {1: player1, 2: player2}
        for event in events:
            player_number = event["player_number"]
            player_obj = players[player_number]
            damage = event["damage"]
            impact = pygame.Vector2(event["position"])
            target_center = pygame.Vector2(player_obj.get_hitbox().center)
            force = target_center - impact
            if force.length_squared() == 0:
                force.update(0, -1)
            else:
                force.normalize_ip()

            heavy = event["source"] == "cannon"
            lethal = event["health_after"] <= 0
            hitbox = player_obj.get_hitbox()
            contact = pygame.Vector2(
                max(hitbox.left, min(impact.x, hitbox.right)),
                max(hitbox.top, min(impact.y, hitbox.bottom)),
            )
            shockwave_duration = 0.30 if heavy else 0.22
            self.shockwaves.append(
                {
                    "position": contact,
                    "color": (255, 159, 56) if heavy else (190, 105, 255),
                    "life": shockwave_duration,
                    "maximum_life": shockwave_duration,
                    "start_radius": 8 if heavy else 5,
                    "end_radius": 92 if heavy else 46,
                    "width": 7 if heavy else 5,
                }
            )
            particle_count = 38 if lethal else (24 if heavy else 13)
            base_color = (255, 159, 56) if heavy else (190, 105, 255)
            base_angle = math.atan2(force.y, force.x)
            for _ in range(particle_count):
                angle = base_angle + random.uniform(-1.0, 1.0)
                speed = random.uniform(120, 340 if heavy else 240)
                velocity = pygame.Vector2(
                    math.cos(angle) * speed,
                    math.sin(angle) * speed,
                )
                self.particles.append(
                    {
                        "position": impact.copy(),
                        "velocity": velocity,
                        "color": base_color,
                        "radius": random.uniform(2.5, 6.5 if heavy else 4.5),
                        "life": random.uniform(0.28, 0.55),
                        "maximum_life": 0.55,
                    }
                )

            number_velocity = force * 48 + pygame.Vector2(0, -85)
            self.damage_numbers.append(
                {
                    "position": target_center.copy(),
                    "velocity": number_velocity,
                    "damage": damage,
                    "life": 0.8,
                    "maximum_life": 0.8,
                    "heavy": heavy,
                }
            )
            self.flash_timers[player_number] = 0.10 if heavy else 0.065
            self.shake_time = max(self.shake_time, 0.24 if heavy else 0.12)
            self.shake_strength = max(
                self.shake_strength,
                11.0 if heavy else 4.0,
            )
            if lethal:
                self.finisher_time = 0.55
                self.shake_time = max(self.shake_time, 0.45)
                self.shake_strength = max(self.shake_strength, 16.0)
            previous_health = event["health_before"]
            self.ghost_health[player_number] = max(
                self.ghost_health.get(player_number, previous_health),
                float(previous_health),
            )
            self.ghost_delays[player_number] = 0.35
            if lethal:
                replay_system.trigger_hit_stop(0.32)
            else:
                replay_system.trigger_hit_stop(0.085 if heavy else 0.045)

    # advance particles, floating numbers, flashes, shake, and ghost bars
    def update(self, player1, player2):
        now = perf_counter()
        dt = min(0.05, max(0.0, now - self.last_update))
        self.last_update = now

        for particle in self.particles:
            particle["life"] -= dt
            particle["velocity"].y += 360 * dt
            particle["position"] += particle["velocity"] * dt
        self.particles = [
            particle for particle in self.particles if particle["life"] > 0.0
        ]

        for shockwave in self.shockwaves:
            shockwave["life"] -= dt
        self.shockwaves = [
            shockwave
            for shockwave in self.shockwaves
            if shockwave["life"] > 0.0
        ]

        for number in self.damage_numbers:
            number["life"] -= dt
            number["velocity"].y += 150 * dt
            number["position"] += number["velocity"] * dt
        self.damage_numbers = [
            number for number in self.damage_numbers if number["life"] > 0.0
        ]

        for player_number in (1, 2):
            self.flash_timers[player_number] = max(
                0.0,
                self.flash_timers[player_number] - dt,
            )
            self.ghost_delays[player_number] = max(
                0.0,
                self.ghost_delays[player_number] - dt,
            )

        for player_number, player_obj in ((1, player1), (2, player2)):
            ghost = self.ghost_health.setdefault(
                player_number,
                float(player_obj.hp),
            )
            if self.ghost_delays[player_number] <= 0.0:
                self.ghost_health[player_number] = max(
                    float(player_obj.hp),
                    ghost - 14.0 * dt,
                )

        self.shake_time = max(0.0, self.shake_time - dt)
        self.finisher_time = max(0.0, self.finisher_time - dt)
        if self.shake_time == 0.0:
            self.shake_strength = 0.0
        return dt

    def is_flashing(self, player_number):
        return self.flash_timers[player_number] > 0.0

    def get_ghost_health(self, player_number, player_obj):
        return max(
            float(player_obj.hp),
            self.ghost_health.get(player_number, float(player_obj.hp)),
        )

    # return one fresh random offset while an impact shake is active
    def get_shake_offset(self):
        if self.shake_time <= 0.0:
            return 0, 0
        strength = max(1, round(self.shake_strength))
        return (
            random.randint(-strength, strength),
            random.randint(-strength, strength),
        )

    # dim the arena behind fighters during charges and final impacts
    def draw_focus_dim(self, surface, replay_system):
        cannon_charging = any(
            potion_obj.type == "cannon" and potion_obj.charging
            for throw_time, owner, potion_obj in replay_system.active_projectiles
        )
        if not cannon_charging and self.finisher_time <= 0.0:
            return

        alpha = 105 if self.finisher_time > 0.0 else 58
        dim = pygame.Surface(surface.get_size(), pygame.SRCALPHA)
        dim.fill((5, 8, 20, alpha))
        surface.blit(dim, (0, 0))

    # draw sparks and splatters behind the damage numbers
    def draw_particles(self, surface):
        for particle in self.particles:
            progress = particle["life"] / particle["maximum_life"]
            radius = max(1, round(particle["radius"] * progress))
            color = (*particle["color"], max(0, round(255 * progress)))
            drawing.draw_smooth_circle(
                surface,
                color,
                particle["position"],
                radius,
            )

    # draw a quick outlined ring from each registered hit point
    def draw_shockwaves(self, surface):
        scale = 3
        for shockwave in self.shockwaves:
            progress = 1.0 - (
                shockwave["life"] / shockwave["maximum_life"]
            )
            eased_progress = 1.0 - (1.0 - progress) ** 3
            radius = round(
                shockwave["start_radius"]
                + (
                    shockwave["end_radius"]
                    - shockwave["start_radius"]
                )
                * eased_progress
            )
            alpha = max(0, round(230 * (1.0 - progress) ** 2))
            width = max(1, round(shockwave["width"] * (1.0 - progress * 0.45)))
            padding = width + 3
            diameter = (radius + padding) * 2
            ring = pygame.Surface(
                (diameter * scale, diameter * scale),
                pygame.SRCALPHA,
            )
            center = (radius + padding) * scale
            pygame.draw.circle(
                ring,
                (24, 27, 44, alpha),
                (center, center),
                radius * scale,
                (width + 3) * scale,
            )
            pygame.draw.circle(
                ring,
                (*shockwave["color"], alpha),
                (center, center),
                radius * scale,
                width * scale,
            )
            ring = pygame.transform.smoothscale(
                ring,
                (diameter, diameter),
            )
            surface.blit(
                ring,
                (
                    round(shockwave["position"].x - radius - padding),
                    round(shockwave["position"].y - radius - padding),
                ),
            )

    # draw outlined bouncing damage values over the fighters
    def draw_damage_numbers(self, surface):
        if self.number_font is None:
            self.number_font = pygame.font.SysFont(
                "freesansbold",
                42,
                bold=True,
            )

        for number in self.damage_numbers:
            progress = number["life"] / number["maximum_life"]
            scale = 1.0 + (0.3 if number["heavy"] else 0.1) * progress
            text = self.number_font.render(
                f"-{number['damage']}",
                True,
                (255, 72, 58) if number["heavy"] else (255, 215, 80),
            )
            text = pygame.transform.rotozoom(text, 0, scale)
            center = round(number["position"].x), round(number["position"].y)
            border = pygame.mask.from_surface(text).to_surface(
                setcolor=(32, 10, 18, 255),
                unsetcolor=(0, 0, 0, 0),
            )
            border = pygame.transform.smoothscale(
                border,
                (text.get_width() + 6, text.get_height() + 6),
            )
            surface.blit(border, border.get_rect(center=center))
            surface.blit(text, text.get_rect(center=center))

    # pulse red edges when either player is near defeat
    def draw_low_health_vignette(self, surface, player1, player2):
        lowest_ratio = min(
            player1.hp / player1.max_hp,
            player2.hp / player2.max_hp,
        )
        if lowest_ratio > 0.3:
            return

        pulse = 0.55 + 0.45 * math.sin(perf_counter() * 7.0) ** 2
        danger = 1.0 - lowest_ratio / 0.3
        overlay = pygame.Surface(surface.get_size(), pygame.SRCALPHA)
        width, height = surface.get_size()
        for layer in range(10):
            thickness = round(min(width, height) * (0.012 + layer * 0.006))
            alpha = round(9 * pulse * danger)
            pygame.draw.rect(
                overlay,
                (190, 0, 24, alpha),
                (layer * 3, layer * 3, width - layer * 6, height - layer * 6),
                thickness,
            )
        surface.blit(overlay, (0, 0))
