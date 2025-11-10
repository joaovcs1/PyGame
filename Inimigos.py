# Inimigos.py
import pygame
import os
import math
import random
from assets import *

class InimigoCyborg(pygame.sprite.Sprite):
    """Inimigo Cyborg - persegue o player e ataca com soco"""
    def __init__(self, x, y, scale=2.5, idle_count=None, run_count=None, punch_count=None):
        super().__init__()
        self.scale = float(scale) if scale >= 0.5 else 0.5
        
        # Carrega animações do Cyborg
        self.idle_frames = self._load_frames(cyborg_idle, idle_count, self.scale)
        self.run_frames = self._load_frames(cyborg_run, run_count, self.scale)
        self.punch_frames = self._load_frames(cyborg_attack3, 8, self.scale)  # Usa attack3 com 8 frames
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
        self._was_dying = False  # Flag para detectar quando acabou de morrer
        
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
        # Variação aleatória inicial no cooldown para evitar sincronização
        self.punch_cooldown = random.uniform(0.0, 1.5)  # Cooldown inicial aleatório entre 0 e 1.5 segundos
        self.punch_interval = 1.5
        self.detection_range = 1000  # Detecta o player de longe
        self.punch_range = 50  # Alcance do soco (muito perto - reduzido para aproximar mais)
        
        # Saúde
        self.health = 5  # Reduzido de 10 para 5
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
            self._was_dying = False  # Reseta para detectar morte no próximo frame
    
    def _executar_comportamento(self, target_x, target_y, distancia, dt):
        """Comportamento: persegue o player e soca quando dentro do alcance"""
        moving = False
        
        # Se está socando, não se move
        if self.punch_timer > 0:
            return False
        
        # Persegue o player quando detecta
        if distancia <= self.detection_range:
            # Verifica se está na mesma posição X do player (em cima do player)
            x_distance = abs(target_x - self.world_x)
            is_above_player = x_distance <= 30  # Tolerância de 30 pixels
            
            # Se está em cima do player, anda para a direita
            if is_above_player:
                moving = True
                self.world_x += self.speed
                return moving
            
            if distancia > self.punch_range:
                # Persegue o player
                moving = True
                if target_x < self.world_x:
                    self.world_x -= self.speed
                else:
                    self.world_x += self.speed
            elif self.pode_socar(target_x, target_y):
                # Está perto o suficiente, soca (e para de se mover)
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
        
        # Calcula a posição na tela (sempre baseada em world_x - camera_x)
        screen_centerx = int(self.world_x - camera_x)
        
        # Para o soco, usa uma posição Y fixa baseada no rect atual
        # Mas se está começando a socar, salva a posição Y inicial
        is_punching = self.punch_timer > 0
        if is_punching:
            # Se está socando, usa a posição Y salva quando começou a socar
            if not hasattr(self, '_punch_start_bottom'):
                # Primeira vez socando neste ciclo - salva a posição Y
                if hasattr(self, 'rect') and hasattr(self.rect, 'bottom'):
                    self._punch_start_bottom = self.rect.bottom
                else:
                    self._punch_start_bottom = 0
            prev_bottom = self._punch_start_bottom
        else:
            # Não está socando - limpa a posição salva e usa a atual
            if hasattr(self, '_punch_start_bottom'):
                delattr(self, '_punch_start_bottom')
            if hasattr(self, 'rect') and hasattr(self.rect, 'bottom'):
                prev_bottom = self.rect.bottom
            else:
                prev_bottom = 0
        
        # Identifica o estado atual da animação
        if is_punching:
            current_state = "punch"
            frames = self.punch_frames if self.punch_frames else self.idle_frames
            frame_time = max(0.06, self.animation_speed * 0.8)
        elif moving:
            current_state = "run"
            frames = self.run_frames if self.run_frames else self.idle_frames
            frame_time = self.animation_speed
        else:
            current_state = "idle"
            frames = self.idle_frames
            frame_time = self.animation_speed
        
        # Detecta mudança de animação comparando estados
        animation_changed = False
        if not hasattr(self, '_last_animation_state') or self._last_animation_state != current_state:
            # Mudou de animação - reseta frame_index e timer
            self.frame_index = 0
            self.animation_timer = 0.0
            self._last_animation_state = current_state
            animation_changed = True
        
        # Atualiza animação
        self.animation_timer += dt
        frame_changed = False
        if self.animation_timer >= frame_time:
            passos = int(self.animation_timer / frame_time)
            self.animation_timer -= passos * frame_time
            self.frame_index = (self.frame_index + passos) % len(frames)
            frame_changed = True
        
        # Garante que frame_index está dentro do range
        if self.frame_index >= len(frames) or self.frame_index < 0:
            self.frame_index = 0
        
        # SEMPRE atualiza o frame e rect para garantir que não há frames antigos
        # Pega o frame e cria uma cópia para evitar problemas de referência
        frame = frames[self.frame_index].copy()
        if self.facing == "left":
            frame = pygame.transform.flip(frame, True, False)
        
        # Atualiza image
        self.image = frame
        
        # Cria um NOVO rect do zero (nunca reutiliza o rect antigo)
        self.rect = self.image.get_rect()
        
        # Define posições: Y preserva altura, X sempre baseado em world_x
        # IMPORTANTE: Define centerx primeiro, depois bottom
        self.rect.centerx = screen_centerx
        self.rect.bottom = prev_bottom
    
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
    # Scale 3.2 para tornar o Cyborg maior
    return InimigoCyborg(spawn_x, spawn_y, scale=3.2, idle_count=None, run_count=None, punch_count=None)


class Careca(pygame.sprite.Sprite):
    """Inimigo Careca - atirador que fica parado e atira de longe"""
    def __init__(self, x, y, scale=2.5, idle_count=None, shot_count=None):
        super().__init__()
        self.scale = float(scale) if scale >= 0.5 else 0.5
        
        # Carrega animações do Careca
        self.idle_frames = self._load_frames(idle_careca, idle_count, self.scale)
        self.shot_frames = self._load_frames(shot_careca, shot_count, self.scale)
        self.dead_frames = self._load_frames(dead_careca, None, self.scale)  # Detecta automaticamente
        
        # Estado de animação
        self.current_frames = self.idle_frames if self.idle_frames else [self._fallback_surface(self.scale)]
        self.frame_index = 0
        self.animation_timer = 0.0
        self.animation_speed = 0.12
        self.shot_timer = 0.0
        self.shot_duration = 0.3  # Duração do tiro
        
        # Estado de morte
        self.is_dying = False
        self.dead_timer = 0.0
        self.dead_last_frame_duration = 2.0  # 2 segundos no último frame
        self._was_dying = False  # Flag para detectar quando acabou de morrer
        
        self.image = self.current_frames[self.frame_index]
        self.rect = self.image.get_rect(center=(x, y))
        
        # Movimento e direção - fica parado
        self.speed = 0.0  # Não se move
        self.facing = "left"  # Inimigos começam olhando para esquerda por padrão
        
        # Física vertical
        self.vel_y = 0.0
        self.gravidade = 0.45
        self.no_chao = True
        
        # Sistema de tiro (atirador de longe)
        # Variação aleatória inicial no cooldown para evitar sincronização
        self.shoot_cooldown = random.uniform(0.0, 1.2)  # Cooldown inicial aleatório entre 0 e 1.2 segundos
        self.shoot_interval = 1.2  # Atira a cada 1.2 segundos
        self.detection_range = 800  # Detecta o player de longe
        self.shoot_range = 700  # Alcance de tiro (muito longe)
        
        # Saúde
        self.health = 6
        self.alive = True
        
        # Posição no mundo
        self.world_x = x
    
    def _fallback_surface(self, scale=1):
        s = pygame.Surface((32*scale, 48*scale), pygame.SRCALPHA)
        s.fill((255, 0, 0))
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
            print(f"[Careca] Aviso: não foi possível carregar '{caminho}': {e}")
            return [self._fallback_surface(scale)]
        
        sheet_w, sheet_h = sheet.get_width(), sheet.get_height()
        
        if num_frames is None or num_frames <= 0:
            num_frames, frame_w = self._detectar_num_frames(sheet, frame_width_hint)
            print(f"[Careca] Detectados {num_frames} frames em '{os.path.basename(caminho)}' (largura: {frame_w}px)")
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
                print(f"[Careca] Erro ao extrair frame {i}: {e}")
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
        """Atualiza a direção visual do Careca"""
        target_screen_x = target_world_x - camera_x
        enemy_screen_centerx = self.rect.centerx

        if target_screen_x > enemy_screen_centerx:
            self.facing = "right"
        elif target_screen_x < enemy_screen_centerx:
            self.facing = "left"
    
    def pode_atirar(self, target_x, target_y):
        """Verifica se o Careca pode atirar no alvo"""
        distancia = self.calcular_distancia(target_x, target_y)
        return (distancia <= self.shoot_range and 
                self.shoot_cooldown <= 0.0 and 
                self.shot_timer <= 0.0)
    
    def shoot(self, target_x, target_y):
        """Dispara um projétil horizontal direcionado ao alvo"""
        if not self.alive or not self.pode_atirar(target_x, target_y):
            return None
        
        self.shot_timer = self.shot_duration
        self.shoot_cooldown = self.shoot_interval
        
        # Calcula direção do tiro apenas horizontal (sem componente vertical)
        enemy_world_x = self.world_x
        
        dx = target_x - enemy_world_x
        
        # Direção apenas horizontal (sempre para direita ou esquerda)
        if dx == 0:
            direction_x = 0
        else:
            direction_x = 1 if dx > 0 else -1
        
        # Sem componente vertical - projétil sempre horizontal
        direction_y = 0
        
        # Ponto de origem do projétil na tela
        muzzle_x = self.rect.centerx
        muzzle_y = self.rect.centery
        
        speed = 8
        return ProjetilInimigo(muzzle_x, muzzle_y, direction_x, direction_y, speed, self.scale)
    
    def take_damage(self, damage=1):
        """Inflige dano ao Careca"""
        if self.is_dying or not self.alive:
            return
        
        self.health -= damage
        
        if self.health <= 0:
            self.is_dying = True
            self.alive = False
            self.frame_index = 0
            self.animation_timer = 0.0
            self.dead_timer = 0.0
            self._was_dying = False  # Reseta para detectar morte no próximo frame
    
    def update(self, dt, camera_x, protagonista_pos=None):
        """Atualiza o Careca"""
        # Se está morrendo, mostra animação de morte
        if self.is_dying:
            self._update_death_animation(dt, camera_x)
            return
        
        if not self.alive:
            return
        
        # Atualiza cooldowns
        if self.shoot_cooldown > 0:
            self.shoot_cooldown -= dt
        if self.shot_timer > 0:
            self.shot_timer -= dt
        
        # Comportamento: fica parado e atira
        if protagonista_pos:
            target_x, target_y = protagonista_pos
            distancia = self.calcular_distancia(target_x, target_y)
            
            # Sempre atualiza a direção para olhar para o protagonista
            self.atualizar_direcao(target_x, camera_x)
        
        # Escolhe animação (sempre idle ou shot, nunca run pois não se move)
        if self.shot_timer > 0:
            frames = self.shot_frames if self.shot_frames else self.idle_frames
            frame_time = max(0.06, self.animation_speed * 0.8)
        else:
            frames = self.idle_frames
            frame_time = self.animation_speed
        
        # Calcula a posição na tela primeiro
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
        self.rect.centerx = screen_centerx
    
    def _update_death_animation(self, dt, camera_x):
        """Atualiza a animação de morte do Careca"""
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
        self.rect.centerx = screen_centerx


class ProjetilInimigo(pygame.sprite.Sprite):
    """Projétil disparado pelos inimigos"""
    def __init__(self, x, y, direction_x, direction_y, speed, scale=1.0):
        super().__init__()
        # Usa o mesmo sprite de projétil do protagonista
        try:
            img = pygame.image.load(bullet_path).convert_alpha()
        except Exception:
            # fallback simples se não conseguir carregar
            img = pygame.Surface((6, 2), pygame.SRCALPHA)
            img.fill((255, 200, 40))
        
        new_w = max(1, int(round(img.get_width() * scale)))
        new_h = max(1, int(round(img.get_height() * scale)))
        self.image = pygame.transform.scale(img, (new_w, new_h))
        
        # Rotaciona a imagem baseado na direção do movimento
        angle = math.degrees(math.atan2(-direction_y, direction_x))
        self.image = pygame.transform.rotate(self.image, angle)
        
        self.rect = self.image.get_rect(center=(x, y))
        
        self.direction_x = direction_x
        self.direction_y = direction_y
        self.speed = speed
        
    def update(self, dt):
        """Atualiza a posição do projétil"""
        self.rect.x += int(self.direction_x * self.speed)
        self.rect.y += int(self.direction_y * self.speed)
        
        # Remove projéteis que saem da tela
        if (self.rect.right < -100 or self.rect.left > 900 or 
            self.rect.bottom < -100 or self.rect.top > 700):
            self.kill()


def spawn_careca(camera_x, chao_y, screen_width, player_y, x_offset=0, lado="direita"):
    """
    Spawna um Careca em uma posição relativa à câmera
    
    Args:
        camera_x: Posição atual da câmera
        chao_y: Altura do chão
        screen_width: Largura da tela
        player_y: Altura Y do player (para spawnar na mesma altura)
        x_offset: Offset em relação à câmera (0 = próximo à câmera, positivo = mais à frente/atrás)
        lado: "direita" para spawnar à direita, "esquerda" para spawnar à esquerda
    
    Returns:
        Careca ou None
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
    # Scale 1.5 para tornar o Careca menor
    return Careca(spawn_x, spawn_y, scale=1.5, idle_count=None, shot_count=None)


class ColunaFogo(pygame.sprite.Sprite):
    """Coluna de fogo como obstáculo no jogo"""
    def __init__(self, x, y, scale=1.5):
        super().__init__()
        self.scale = float(scale) if scale >= 0.5 else 0.5
        
        # Carrega frames do fogo
        self.frames = self._load_fire_frames(scale)
        
        # Estado de animação
        self.frame_index = 0
        self.animation_timer = 0.0
        self.animation_speed = 0.08  # Animação rápida
        self.loop = True  # Faz loop continuamente
        
        self.image = self.frames[self.frame_index] if self.frames else self._fallback_surface()
        self.rect = self.image.get_rect(center=(x, y))
        
        # Área de colisão: apenas uma linha vertical estreita no centro (mesmo X)
        # Largura muito pequena (5% da largura) mas altura total
        collision_width = max(5, int(self.rect.width * 0.05))
        collision_height = self.rect.height
        self.collision_rect = pygame.Rect(0, 0, collision_width, collision_height)
        self.collision_rect.center = self.rect.center
        
        # Posição no mundo (para seguir a câmera)
        self.world_x = x
        self.world_y = y
        
        # Dano ao player
        self.damage_cooldown = 0.0
        self.damage_interval = 0.5  # Dano a cada 0.5 segundos
    
    def _fallback_surface(self):
        s = pygame.Surface((32, 32), pygame.SRCALPHA)
        s.fill((255, 100, 0))
        return s
    
    def _load_fire_frames(self, scale):
        """Carrega os frames do efeito de fogo"""
        frames = []
        for path in fire_frames_paths:
            try:
                img = pygame.image.load(path).convert_alpha()
                new_w = max(1, int(round(img.get_width() * scale)))
                new_h = max(1, int(round(img.get_height() * scale)))
                frame = pygame.transform.scale(img, (new_w, new_h))
                frames.append(frame)
            except Exception as e:
                print(f"[ColunaFogo] Erro ao carregar '{path}': {e}")
        
        return frames if frames else [self._fallback_surface()]
    
    def update(self, dt, camera_x):
        """Atualiza a coluna de fogo"""
        # Atualiza posição baseada na câmera
        self.rect.centerx = int(self.world_x - camera_x)
        # Mantém o bottom sempre no chão (world_y)
        self.rect.bottom = int(self.world_y)
        
        # Atualiza o rect de colisão (menor, apenas o centro)
        self.collision_rect.centerx = self.rect.centerx
        self.collision_rect.centery = self.rect.centery
        
        # Atualiza cooldown de dano
        if self.damage_cooldown > 0:
            self.damage_cooldown -= dt
        
        # Atualiza animação (loop contínuo)
        self.animation_timer += dt
        if self.animation_timer >= self.animation_speed:
            self.animation_timer = 0.0
            self.frame_index = (self.frame_index + 1) % len(self.frames)
            
            # Atualiza frame
            prev_centerx = self.rect.centerx
            prev_bottom = self.rect.bottom
            
            self.image = self.frames[self.frame_index]
            self.rect = self.image.get_rect()
            self.rect.centerx = prev_centerx
            self.rect.bottom = prev_bottom
            
            # Atualiza o rect de colisão após mudar o frame
            # Largura muito pequena (5% da largura) mas altura total
            collision_width = max(5, int(self.rect.width * 0.05))
            collision_height = self.rect.height
            self.collision_rect.width = collision_width
            self.collision_rect.height = collision_height
            self.collision_rect.center = self.rect.center
    
    def is_fire_on(self):
        """Verifica se o fogo está aceso (não apagado) baseado no frame atual"""
        if not self.frames or len(self.frames) == 0:
            return False
        # Os primeiros 70% dos frames são considerados "acesos"
        # Os últimos 30% são considerados "apagados"
        threshold = int(len(self.frames) * 0.7)
        return self.frame_index < threshold
    
    def can_damage(self):
        """Verifica se pode causar dano (cooldown acabou E fogo está aceso)"""
        return self.damage_cooldown <= 0.0 and self.is_fire_on()
    
    def apply_damage(self):
        """Aplica dano e reseta cooldown"""
        self.damage_cooldown = self.damage_interval


class Plataforma(pygame.sprite.Sprite):
    """Plataforma cinza claro que aparece antes das colunas de fogo"""
    def __init__(self, x, y, width=200, height=20):
        super().__init__()
        self.width = width
        self.height = height
        
        # Cria uma superfície cinza claro
        self.image = pygame.Surface((width, height))
        self.image.fill((180, 180, 180))  # Cinza claro
        
        self.rect = self.image.get_rect()
        self.rect.x = x
        self.rect.y = y
        
        # Posição no mundo (para seguir a câmera)
        self.world_x = x
        self.world_y = y
    
    def update(self, camera_x):
        """Atualiza a posição da plataforma baseada na câmera"""
        self.rect.x = int(self.world_x - camera_x)
        self.rect.y = int(self.world_y)


class Coracao(pygame.sprite.Sprite):
    """Coração que restaura vida do player"""
    def __init__(self, x, y, scale=1.0):
        super().__init__()
        
        # Tamanho fixo de 30x30 pixels
        target_size = 30
        
        # Carrega a imagem do coração
        try:
            img = pygame.image.load(heart_path).convert_alpha()
            # Redimensiona para 30x30 pixels
            self.image = pygame.transform.scale(img, (target_size, target_size))
        except Exception as e:
            print(f"[Coracao] Erro ao carregar '{heart_path}': {e}")
            # Fallback: cria uma superfície vermelha simples
            self.image = pygame.Surface((target_size, target_size), pygame.SRCALPHA)
            self.image.fill((255, 0, 0))
        
        self.rect = self.image.get_rect()
        # Define a posição inicial (será ajustada no update)
        self.rect.x = 0
        self.rect.y = 0
        
        # Posição no mundo (para seguir a câmera)
        self.world_x = x
        self.world_y = y
        
        # Animação de flutuação
        self.animation_timer = 0.0
        self.animation_speed = 2.0
        self.float_offset = 0.0
    
    def update(self, dt, camera_x):
        """Atualiza a posição do coração baseada na câmera e animação"""
        # Atualiza posição baseada na câmera
        self.rect.x = int(self.world_x - camera_x)
        
        # Animação de flutuação (mantém o bottom no chão)
        self.animation_timer += dt * self.animation_speed
        self.float_offset = math.sin(self.animation_timer) * 3  # Flutua 3 pixels para cima/baixo
        # Mantém o bottom no chão (world_y) e aplica a flutuação
        self.rect.bottom = int(self.world_y + self.float_offset)

