# Inimigos.py
import pygame
import os
import math
from assets import *

class InimigoCyborg(pygame.sprite.Sprite):
    """Inimigo Cyborg - persegue o player e ataca com soco"""
    def __init__(self, x, y, scale=2.5, idle_count=None, run_count=None, punch_count=None):
        super().__init__()
        self.scale = float(scale) if scale >= 0.5 else 0.5
        
        # Carrega animações do Cyborg
        self.idle_frames = self._load_frames(cyborg_idle, idle_count, self.scale)
        self.run_frames = self._load_frames(cyborg_run, run_count, self.scale)
        self.punch_frames = self._load_frames(cyborg_punch, punch_count, self.scale)
        self.dead_frames = self._load_frames(cyborg_death, None, self.scale)  # Detecta automaticamente
        
        # Estado de animação
        self.current_frames = self.idle_frames if self.idle_frames else [self._fallback_surface(self.scale)]
        self.frame_index = 0
        self.animation_timer = 0.0
        self.animation_speed = 0.12
        self.punch_timer = 0.0
        self.punch_duration = 0.4  # Duração do soco
        
        # Estado de morte
        self.is_dying = False
        self.dead_timer = 0.0
        self.dead_last_frame_duration = 2.0  # 2 segundos no último frame
        
        self.image = self.current_frames[self.frame_index]
        self.rect = self.image.get_rect(center=(x, y))
        
        # Movimento e direção
        self.speed = 3.575  # 43% mais rápido que o original (2.5 * 1.43 = 3.575)
        self.facing = "left"  # Inimigos começam olhando para esquerda por padrão
        
        # Física vertical
        self.vel_y = 0.0
        self.gravidade = 0.45
        self.no_chao = True
        
        # Sistema de soco (corpo-a-corpo)
        self.punch_cooldown = 0.0
        self.punch_interval = 1.5
        self.detection_range = 1000  # Detecta o player de longe
        self.punch_range = 50  # Alcance do soco (muito perto - reduzido para aproximar mais)
        
        # Saúde
        self.health = 10
        self.alive = True
        
        # Posição no mundo
        self.world_x = x
    
    def _fallback_surface(self, scale=1):
        s = pygame.Surface((32*scale, 48*scale), pygame.SRCALPHA)
        s.fill((100, 100, 200))
        return s
    
    def _detectar_num_frames(self, sheet, frame_width_hint=None):
        """Detecta automaticamente o número de frames em um sprite sheet"""
        sheet_w, sheet_h = sheet.get_width(), sheet.get_height()
        
        if frame_width_hint:
            num_frames = sheet_w // frame_width_hint
            if num_frames > 0 and (num_frames * frame_width_hint) == sheet_w:
                return num_frames, frame_width_hint
        
        larguras_comuns = [256, 192, 144, 128, 112, 96, 80, 64, 48, 32]
        
        melhor_opcao = None
        melhor_score = 0
        
        for largura in larguras_comuns:
            if sheet_w % largura == 0:
                num_frames = sheet_w // largura
                if num_frames > 0:
                    if 4 <= num_frames <= 20:
                        return num_frames, largura
                    if melhor_opcao is None or (melhor_score < num_frames <= 20):
                        melhor_opcao = (num_frames, largura)
                        melhor_score = num_frames
        
        if melhor_opcao:
            return melhor_opcao
        
        largura = 32
        while largura <= sheet_w:
            if sheet_w % largura == 0:
                num_frames = sheet_w // largura
                if num_frames > 0 and num_frames <= 30:
                    return num_frames, largura
            largura *= 2
        
        return 1, sheet_w
    
    def _load_frames(self, caminho, num_frames=None, scale=1.0, frame_width_hint=None):
        caminho = os.path.normpath(caminho)
        try:
            sheet = pygame.image.load(caminho).convert_alpha()
        except Exception as e:
            print(f"[InimigoCyborg] Aviso: não foi possível carregar '{caminho}': {e}")
            return [self._fallback_surface(scale)]
        
        sheet_w, sheet_h = sheet.get_width(), sheet.get_height()
        
        if num_frames is None or num_frames <= 0:
            num_frames, frame_w = self._detectar_num_frames(sheet, frame_width_hint)
            print(f"[InimigoCyborg] Detectados {num_frames} frames em '{os.path.basename(caminho)}' (largura: {frame_w}px)")
        else:
            frame_w = sheet_w // num_frames
        
        frames = []
        for i in range(num_frames):
            rect = pygame.Rect(i * frame_w, 0, frame_w, sheet_h)
            try:
                frame = sheet.subsurface(rect).copy()
                new_w = max(1, int(round(frame.get_width() * scale)))
                new_h = max(1, int(round(frame.get_height() * scale)))
                frame = pygame.transform.scale(frame, (new_w, new_h))
                frames.append(frame)
            except Exception as e:
                print(f"[InimigoCyborg] Erro ao extrair frame {i}: {e}")
                frames.append(self._fallback_surface(scale))
        
        return frames if frames else [self._fallback_surface(scale)]
    
    def aplicar_gravidade(self, chao_y):
        self.vel_y += self.gravidade
        self.rect.y += int(self.vel_y)
        if self.rect.bottom >= chao_y:
            self.rect.bottom = chao_y
            self.vel_y = 0.0
            self.no_chao = True
        else:
            self.no_chao = False
    
    def calcular_distancia(self, target_x, target_y):
        """Calcula a distância até o alvo"""
        dx = target_x - self.world_x
        dy = target_y - self.rect.centery
        return math.sqrt(dx * dx + dy * dy)
    
    def atualizar_direcao(self, target_world_x, camera_x=0):
        """Atualiza a direção visual do Cyborg"""
        target_screen_x = target_world_x - camera_x
        enemy_screen_centerx = self.rect.centerx

        if target_screen_x > enemy_screen_centerx:
            self.facing = "right"
        elif target_screen_x < enemy_screen_centerx:
            self.facing = "left"
    
    def pode_socar(self, target_x, target_y):
        """Verifica se o Cyborg pode socar o alvo"""
        distancia = self.calcular_distancia(target_x, target_y)
        return (distancia <= self.punch_range and 
                self.punch_cooldown <= 0.0 and 
                self.punch_timer <= 0.0)
    
    def socar(self, target_x, target_y):
        """Executa um soco no alvo (ataque corpo-a-corpo)"""
        if not self.alive or not self.pode_socar(target_x, target_y):
            return False
        
        self.punch_timer = self.punch_duration
        self.punch_cooldown = self.punch_interval
        return True
    
    def take_damage(self, damage=1):
        """Inflige dano ao Cyborg"""
        if self.is_dying or not self.alive:
            return
        
        self.health -= damage
        
        if self.health <= 0:
            self.is_dying = True
            self.alive = False
            self.frame_index = 0
            self.animation_timer = 0.0
            self.dead_timer = 0.0
    
    def _executar_comportamento(self, target_x, target_y, distancia, dt):
        """Comportamento: persegue o player e soca quando dentro do alcance"""
        moving = False
        
        # Persegue o player quando detecta
        if distancia <= self.detection_range:
            if distancia > self.punch_range:
                # Persegue o player
                moving = True
                if target_x < self.world_x:
                    self.world_x -= self.speed
                else:
                    self.world_x += self.speed
            elif self.pode_socar(target_x, target_y):
                # Está perto o suficiente, soca
                self.socar(target_x, target_y)
        
        return moving
    
    def update(self, dt, camera_x, protagonista_pos=None):
        """Atualiza o Cyborg"""
        # Se está morrendo, mostra animação de morte
        if self.is_dying:
            self._update_death_animation(dt, camera_x)
            return
        
        if not self.alive:
            return
        
        # Atualiza cooldowns
        if self.punch_cooldown > 0:
            self.punch_cooldown -= dt
        if self.punch_timer > 0:
            self.punch_timer -= dt
        
        # Comportamento: persegue o player
        moving = False
        if protagonista_pos:
            target_x, target_y = protagonista_pos
            distancia = self.calcular_distancia(target_x, target_y)
            
            # Sempre atualiza a direção para olhar para o protagonista
            self.atualizar_direcao(target_x, camera_x)
            
            # Executa comportamento de perseguição
            moving = self._executar_comportamento(target_x, target_y, distancia, dt)
        
        # Escolhe animação
        if self.punch_timer > 0:
            frames = self.punch_frames if self.punch_frames else self.idle_frames
            frame_time = max(0.06, self.animation_speed * 0.8)
        elif moving:
            frames = self.run_frames if self.run_frames else self.idle_frames
            frame_time = self.animation_speed
        else:
            frames = self.idle_frames
            frame_time = self.animation_speed
        
        # Calcula a posição na tela primeiro (antes de qualquer mudança de frame)
        screen_centerx = int(self.world_x - camera_x)
        
        # Atualiza animação
        self.animation_timer += dt
        if self.animation_timer >= frame_time:
            passos = int(self.animation_timer / frame_time)
            self.animation_timer -= passos * frame_time
            self.frame_index = (self.frame_index + passos) % len(frames)
            
            # Preserva posições antes de recriar o rect
            prev_bottom = self.rect.bottom if hasattr(self, 'rect') else 0
            prev_centerx = self.rect.centerx if hasattr(self, 'rect') else screen_centerx
            
            frame = frames[self.frame_index]
            if self.facing == "left":
                frame = pygame.transform.flip(frame, True, False)
            
            self.image = frame
            self.rect = self.image.get_rect()
            # Restaura posições após recriar o rect
            self.rect.centerx = prev_centerx
            self.rect.bottom = prev_bottom
        
        # SEMPRE atualiza a posição X baseado em world_x - camera_x
        # Isso garante que cada inimigo tenha sua própria posição única
        # e que a posição seja atualizada mesmo quando o frame não muda
        self.rect.centerx = screen_centerx
    
    def _update_death_animation(self, dt, camera_x):
        """Atualiza a animação de morte do Cyborg"""
        if not self.dead_frames or len(self.dead_frames) == 0:
            self.kill()
            return
        
        # Calcula a posição na tela primeiro
        screen_centerx = int(self.world_x - camera_x)
        
        total_frames = len(self.dead_frames)
        last_frame_index = total_frames - 1
        
        if self.frame_index == last_frame_index:
            self.dead_timer += dt
            if self.dead_timer >= self.dead_last_frame_duration:
                self.kill()
                return
            frame = self.dead_frames[last_frame_index]
        else:
            self.animation_timer += dt
            frame_time = self.animation_speed
            
            if self.animation_timer >= frame_time:
                passos = int(self.animation_timer / frame_time)
                self.animation_timer -= passos * frame_time
                self.frame_index = min(self.frame_index + passos, last_frame_index)
                frame = self.dead_frames[self.frame_index]
            else:
                frame = self.dead_frames[self.frame_index]
        
        # Preserva posições antes de recriar o rect
        prev_bottom = self.rect.bottom if hasattr(self, 'rect') else 0
        prev_centerx = self.rect.centerx if hasattr(self, 'rect') else screen_centerx
        
        if self.facing == "left":
            frame = pygame.transform.flip(frame, True, False)
        
        self.image = frame
        self.rect = self.image.get_rect()
        # Restaura posições após recriar o rect
        self.rect.centerx = prev_centerx
        self.rect.bottom = prev_bottom
        
        # SEMPRE atualiza a posição X baseado em world_x - camera_x
        # Isso garante que cada inimigo tenha sua própria posição única mesmo quando morrendo
        self.rect.centerx = screen_centerx


def spawn_inimigo_cyborg(camera_x, chao_y, screen_width, player_y, x_offset=0, lado="direita"):
    """
    Spawna um Cyborg em uma posição relativa à câmera
    
    Args:
        camera_x: Posição atual da câmera
        chao_y: Altura do chão
        screen_width: Largura da tela
        player_y: Altura Y do player (para spawnar na mesma altura)
        x_offset: Offset em relação à câmera (0 = próximo à câmera, positivo = mais à frente/atrás)
        lado: "direita" para spawnar à direita, "esquerda" para spawnar à esquerda
    
    Returns:
        InimigoCyborg ou None
    """
    spawn_y = player_y  # Mesma altura do player
    
    if lado == "esquerda":
        if x_offset > 0:
            spawn_x = camera_x - x_offset
        else:
            spawn_x = camera_x + abs(x_offset)
    else:
        if x_offset >= 0:
            spawn_x = camera_x + screen_width + x_offset
        else:
            spawn_x = camera_x + screen_width + x_offset
    
    # None = detecta automaticamente o número de frames
    # Scale 2.5 = 15% menor que 2.94 (2.94 * 0.85 = 2.499)
    return InimigoCyborg(spawn_x, spawn_y, scale=2.5, idle_count=None, run_count=None, punch_count=None)

