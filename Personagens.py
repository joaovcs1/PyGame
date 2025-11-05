# Personagens.py
import pygame
import os
from assets import*

class Protagonista(pygame.sprite.Sprite):
    def __init__(self, x, y, scale=1.5,
                 idle_count=6, run_count=10, jump_count=10, double_count=6):
        super().__init__()
        self.scale = float(scale) if scale >= 0.5 else 0.5

        self.idle_frames = self._load_frames(idle_path, idle_count, self.scale)
        self.run_frames = self._load_frames(run_path, run_count, self.scale)
        self.jump_frames = self._load_frames(jump_path, jump_count, self.scale)
        self.double_frames = self._load_frames(double_path, double_count, self.scale)

        # estado de animação
        self.current_frames = self.idle_frames if self.idle_frames else [self._fallback_surface(self.scale)]
        self.frame_index = 0
        self.animation_timer = 0.0
        self.animation_speed = 0.12

        self.image = self.current_frames[self.frame_index]
        self.rect = self.image.get_rect(center=(x, y))

        # movimento horizontal
        self.speed = 5
        self.facing = "right"

        # física vertical (AJUSTAR AQUI PARA CONTROLAR ALTURA DO PULO)

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

    def _apply_glow(self, frame, color=(255, 245, 200), radius=2, alpha=120):
        """Aplica um brilho constante ao redor do frame usando máscara."""
        if radius <= 0 or alpha <= 0:
            return frame
        mask = pygame.mask.from_surface(frame)
        if mask.count() == 0:
            return frame
        mask_surf = mask.to_surface(setcolor=(color[0], color[1], color[2], 255), unsetcolor=(0, 0, 0, 0))
        glow_w = frame.get_width() + radius * 2
        glow_h = frame.get_height() + radius * 2
        glow = pygame.Surface((glow_w, glow_h), pygame.SRCALPHA)
        for dx in range(-radius, radius + 1):
            for dy in range(-radius, radius + 1):
                if dx*dx + dy*dy <= radius*radius:
                    glow.blit(mask_surf, (dx + radius, dy + radius))
        glow.set_alpha(alpha)
        composed = pygame.Surface((glow_w, glow_h), pygame.SRCALPHA)
        composed.blit(glow, (0, 0))
        composed.blit(frame, (radius, radius))
        return composed

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
            # redimensiona usando escala fracionária
            new_w = max(1, int(round(frame.get_width() * self.scale)))
            new_h = max(1, int(round(frame.get_height() * self.scale)))
            frame = pygame.transform.smoothscale(frame, (new_w, new_h))
            frames.append(frame)
        return frames

    def move(self, dx):
        if dx == 0:
            return
        self.facing = "right" if dx > 0 else "left"
        self.rect.x += int(dx)

    def jump(self):
        # Primeiro pulo: se no chão, aplica jump_force.
       # Double jump: se já no ar e can_double_jump True aplica double_jump_force
        if self.no_chao:
            # primeiro pulo
            self.vel_y = self.jump_force
            self.no_chao = False
            self.can_double_jump = True
            self.used_double = False
        else:
            # double jump (uma vez por sequência)
            if self.can_double_jump:
                self.vel_y = self.double_jump_force
                self.can_double_jump = False
                self.used_double = True

    #fisica do
    def aplicar_gravidade(self, chao_y):
        self.vel_y += self.gravidade
        self.rect.y += int(self.vel_y)
        if self.rect.bottom >= chao_y:
            self.rect.bottom = chao_y
            self.vel_y = 0.0
            self.no_chao = True
            self.can_double_jump = True
            self.used_double = False
        else:
            self.no_chao = False

    def update(self, dt, moving=False):
        # escolhe frames por estado (prioridade: ar -> run -> idle)
        if not self.no_chao:
            frames = self.double_frames if (self.used_double and self.double_frames) else self.jump_frames
            frame_time = self.animation_speed
        else:
            frames = self.run_frames if (moving and self.run_frames) else self.idle_frames
            frame_time = self.animation_speed

        # animação por tempo
        self.animation_timer += dt
        if self.animation_timer >= frame_time:
            passos = int(self.animation_timer / frame_time)
            self.animation_timer -= passos * frame_time
            self.frame_index = (self.frame_index + passos) % len(frames)

            # preserva posição vertical (bottom) e centerx ao trocar frame
            prev_centerx = self.rect.centerx
            prev_bottom = self.rect.bottom

            frame = frames[self.frame_index]
            if self.facing == "left":
                frame = pygame.transform.flip(frame, True, False)

            self.image = frame
            self.rect = self.image.get_rect()
            self.rect.centerx = prev_centerx
            self.rect.bottom = prev_bottom
 