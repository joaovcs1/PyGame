import pygame
import os
from assets import *
from collections import deque

class Protagonista(pygame.sprite.Sprite):
    def __init__(self, x, y, scale=1.5,
                 idle_count=6, run_count=10, jump_count=10, double_count=6):
        super().__init__()
        self.scale = float(scale) if scale >= 0.5 else 0.5

        self.idle_frames = self._load_frames(idle_path, idle_count, self.scale)
        self.run_frames = self._load_frames(run_path, run_count, self.scale)
        self.jump_frames = self._load_frames(jump_path, jump_count, self.scale)
        self.double_frames = self._load_frames(double_path, double_count, self.scale)
        self.shot_frames = self._load_frames(shot_path, 4, self.scale)

        self.current_frames = self.idle_frames if self.idle_frames else [self._fallback_surface(self.scale)]
        self.frame_index = 0
        self.animation_timer = 0.0
        self.animation_speed = 0.12
        self.shot_timer = 0.0
        self.shot_duration = 0.20

        self.image = self.current_frames[self.frame_index]
        self.rect = self.image.get_rect(center=(x, y))
        self.y = float(self.rect.y)  # posição vertical em float (sub-pixel movement)

        self.speed = 5
        self.facing = "right"

        # Física
        self.vel_y = 0.0
        self.gravidade = 0.45        
        self.jump_force = -10.0      
        self.double_jump_force = -8.0
        self.no_chao = True
        self.can_double_jump = True
        self.used_double = False

    def _fallback_surface(self, scale=1):
        s = pygame.Surface((32*scale, 48*scale), pygame.SRCALPHA)
        s.fill((200,80,40))
        return s

    def _load_frames(self, caminho, num_frames, scale):
        caminho = os.path.normpath(caminho)
        try:
            sheet = pygame.image.load(caminho).convert_alpha()
        except Exception as e:
            print(f"[Protagonista] Aviso: não foi possível carregar '{caminho}': {e}")
            return [self._fallback_surface(scale)]

        if num_frames <= 0:
            return [self._fallback_surface(scale)]

        sheet_w, sheet_h = sheet.get_width(), sheet.get_height()
        frame_w = sheet_w // num_frames
        frames = []
        for i in range(num_frames):
            rect = pygame.Rect(i * frame_w, 0, frame_w, sheet_h)
            frame = sheet.subsurface(rect).copy()
            new_w = max(1, int(round(frame.get_width() * self.scale)))
            new_h = max(1, int(round(frame.get_height() * self.scale)))
            frame = pygame.transform.scale(frame, (new_w, new_h))
            frames.append(frame)
        return frames

    def move(self, dx):
        if dx == 0:
            return
        self.facing = "right" if dx > 0 else "left"
        self.rect.x += int(dx)
        self.y = float(self.rect.y)

    def jump(self):
        if self.no_chao:
            self.vel_y = self.jump_force
            self.no_chao = False
            self.can_double_jump = True
            self.used_double = False
        else:
            if self.can_double_jump:
                self.vel_y = self.double_jump_force
                self.can_double_jump = False
                self.used_double = True

    def aplicar_gravidade(self, chao_y, platforms=None):
        """
        Atualizado: mantém posição vertical em float (self.y) para subpixel movement.
        Trata pouso em plataformas (iterável platforms) e pouso no chão (chao_y).
        """
        self.vel_y += self.gravidade
        prev_bottom = float(self.y + self.rect.height)
        next_bottom = prev_bottom + float(self.vel_y)
        landed_on_platform = None

        if platforms and self.vel_y > 0:
            for plat in platforms:
                if not hasattr(plat, "rect"):
                    continue
                plat_rect = plat.rect
                horiz_overlap = (self.rect.right > plat_rect.left + 2) and (self.rect.left < plat_rect.right - 2)
                if not horiz_overlap:
                    continue
                plat_top = float(plat_rect.top)
                if prev_bottom <= plat_top and next_bottom >= plat_top:
                    landed_on_platform = plat
                    break

        if landed_on_platform:
            self.y = float(landed_on_platform.rect.top - self.rect.height)
            self.rect.y = int(self.y)
            self.vel_y = 0.0
            self.no_chao = True
            self.can_double_jump = True
            self.used_double = False
        else:
            self.y += self.vel_y
            self.rect.y = int(self.y)
            if self.rect.bottom >= chao_y:
                self.rect.bottom = chao_y
                self.y = float(self.rect.y)
                self.vel_y = 0.0
                self.no_chao = True
                self.can_double_jump = True
                self.used_double = False
            else:
                self.no_chao = False

    def update(self, dt, moving=False):
        if self.shot_timer > 0:
            self.shot_timer = max(0.0, self.shot_timer - dt)
            frames = self.shot_frames if self.shot_frames else self.idle_frames
            frame_time = max(0.06, self.animation_speed * 0.8)
        elif not self.no_chao:
            frames = self.double_frames if (self.used_double and self.double_frames) else self.jump_frames
            frame_time = self.animation_speed
        else:
            frames = self.run_frames if (moving and self.run_frames) else self.idle_frames
            frame_time = self.animation_speed

        self.animation_timer += dt
        if self.animation_timer >= frame_time:
            passos = int(self.animation_timer / frame_time)
            self.animation_timer -= passos * frame_time
            self.frame_index = (self.frame_index + passos) % len(frames)

            prev_centerx = self.rect.centerx
            prev_bottom = self.rect.bottom

            frame = frames[self.frame_index]
            if self.facing == "left":
                frame = pygame.transform.flip(frame, True, False)

            self.image = frame
            self.rect = self.image.get_rect()
            self.rect.centerx = prev_centerx
            self.rect.bottom = prev_bottom
            self.y = float(self.rect.y)
 
    def shoot(self):
        """Dispara um projétil e aciona a animação de tiro. Retorna o sprite do projétil."""
        self.shot_timer = self.shot_duration
        img = self.image
        if self.facing == "right":
            muzzle_x = self.rect.centerx + img.get_width() // 8
        else:
            muzzle_x = self.rect.centerx - img.get_width() // 8
        muzzle_y = (self.rect.centery - img.get_height() // 10)+53
        direction = 1 if self.facing == "right" else -1
        speed = 12
        return Projetil(muzzle_x, muzzle_y, direction, speed, self.scale)


class Projetil(pygame.sprite.Sprite):
    def __init__(self, x, y, direction, speed, scale=1.0):
        super().__init__()
        try:
            img = pygame.image.load(bullet_path).convert_alpha()
        except Exception:
            img = pygame.Surface((6, 2), pygame.SRCALPHA)
            img.fill((255, 200, 40))
        new_w = max(1, int(round(img.get_width() * scale)))
        new_h = max(1, int(round(img.get_height() * scale)))
        self.image = pygame.transform.scale(img, (new_w, new_h))
        self.rect = self.image.get_rect(center=(x, y))
        self.direction = 1 if direction >= 0 else -1
        self.speed = speed

    def update(self, dt):
        self.rect.x += int(self.direction * self.speed)


# --------------------------------------------------------------------
# Plataformas (classes integradas ao final de Personagens.py)
# --------------------------------------------------------------------
class Platform(pygame.sprite.Sprite):
    def __init__(self):
        super().__init__()
        self.image = pygame.Surface((160, 30), pygame.SRCALPHA)
        self.rect = self.image.get_rect()
        self.active = False

    def activate(self, screen_x, screen_y, width=180, height=30, color=(150,150,150)):
        self.image = pygame.Surface((int(width), int(height)), pygame.SRCALPHA)
        self.image.fill(color)
        pygame.draw.rect(self.image, (100,100,100), self.image.get_rect(), 2)
        self.rect = self.image.get_rect(topleft=(int(screen_x), int(screen_y)))
        self.active = True

    def deactivate(self):
        self.active = False
        self.rect.x = -99999

    def update(self, camera_dx):
        if not self.active:
            return
        self.rect.x -= int(camera_dx)
        if self.rect.right < -200:
            self.deactivate()


class PlatformPool:
    def __init__(self, pool_size=12):
        self.pool = deque(Platform() for _ in range(pool_size))

    def get(self):
        for p in self.pool:
            if not p.active:
                return p
        new_p = Platform()
        self.pool.append(new_p)
        return new_p

    def active_sprites(self):
        return [p for p in self.pool if p.active]
