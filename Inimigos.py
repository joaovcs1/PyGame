# Inimigos.py
import pygame
import os
import math
import random
from assets import *

class Inimigo(pygame.sprite.Sprite):
    def __init__(self, x, y, scale=1.5, idle_count=None, run_count=None, shot_count=None, ai_type=None):
        super().__init__()
        self.scale = float(scale) if scale >= 0.5 else 0.5
        
        # Tipo de IA (se None, escolhe aleatoriamente)
        ai_types = ["agressivo", "defensivo", "perseguidor", "atirador", "patrulheiro", "cuidadoso"]
        self.ai_type = ai_type if ai_type else random.choice(ai_types)
        
        # Carrega animações (None = detecta automaticamente)
        self.idle_frames = self._load_frames(idle_careca, idle_count, self.scale)
        self.run_frames = self._load_frames(run_careca, run_count, self.scale)
        self.shot_frames = self._load_frames(shot_careca, shot_count, self.scale)
        self.dead_frames = self._load_frames(dead_careca, None, self.scale)  # Detecta automaticamente
        
        # Estado de animação
        self.current_frames = self.idle_frames if self.idle_frames else [self._fallback_surface(self.scale)]
        self.frame_index = 0
        self.animation_timer = 0.0
        self.animation_speed = 0.12
        self.shot_timer = 0.0
        self.shot_duration = 0.25  # segundos
        
        # Estado de morte
        self.is_dying = False
        self.dead_timer = 0.0
        self.dead_last_frame_duration = 2.0  # 2 segundos no último frame
        
        self.image = self.current_frames[self.frame_index]
        self.rect = self.image.get_rect(center=(x, y))
        
        # Movimento e direção (valores padrão, serão sobrescritos por _configurar_ia)
        self.speed = 2
        self.facing = "left"  # Inimigos começam olhando para esquerda por padrão
        
        # Física vertical
        self.vel_y = 0.0
        self.gravidade = 0.45
        self.no_chao = True
        
        # Sistema de tiro (valores padrão, serão sobrescritos por _configurar_ia)
        self.shoot_cooldown = 0.0
        self.shoot_interval = 1.5
        self.detection_range = 500
        self.shoot_range = 400
        
        # Saúde (valor padrão, será sobrescrito por _configurar_ia)
        self.health = 8
        self.alive = True
        
        # Posição no mundo (considerando câmera)
        self.world_x = x
        
        # Variáveis para IA específica
        self.patrol_direction = random.choice([-1, 1])  # Para patrulheiro
        self.patrol_timer = 0.0
        self.last_player_x = None
        self.retreat_timer = 0.0
        
        # Configurações baseadas no tipo de IA (deve ser chamado após inicializar todas as variáveis)
        self._configurar_ia()
        
    def _configurar_ia(self):
        """Configura parâmetros do inimigo baseado no tipo de IA"""
        # Velocidades balanceadas (protagonista tem speed = 5)
        if self.ai_type == "agressivo":
            self.speed = 2.5  # Moderadamente rápido para perseguir
            self.shoot_interval = 1.0
            self.detection_range = 600
            self.shoot_range = 350
            self.health = 6
        elif self.ai_type == "defensivo":
            self.speed = 1.8  # Lento para manter distância
            self.shoot_interval = 2.5
            self.detection_range = 550
            self.shoot_range = 450
            self.health = 10
        elif self.ai_type == "perseguidor":
            self.speed = 2.8  # Rápido para perseguir
            self.shoot_interval = 2.0
            self.detection_range = 700
            self.shoot_range = 200  # Só atira quando muito perto
            self.health = 8
        elif self.ai_type == "atirador":
            self.speed = 1.2  # Muito lento, quase parado
            self.shoot_interval = 0.8
            self.detection_range = 500
            self.shoot_range = 450
            self.health = 6
        elif self.ai_type == "patrulheiro":
            self.speed = 2.0  # Velocidade média para patrulhar
            self.shoot_interval = 1.8
            self.detection_range = 400
            self.shoot_range = 350
            self.health = 7
        elif self.ai_type == "cuidadoso":
            self.speed = 2.2  # Velocidade média-alta para ajustar distância
            self.shoot_interval = 2.2
            self.detection_range = 450
            self.shoot_range = 380
            self.health = 9
        else:
            # Padrão caso o tipo não seja reconhecido
            self.speed = 2.0
            self.shoot_interval = 1.5
            self.detection_range = 500
            self.shoot_range = 400
            self.health = 8
    
    def _fallback_surface(self, scale=1):
        s = pygame.Surface((32*scale, 48*scale), pygame.SRCALPHA)
        s.fill((255, 0, 0))
        return s
    
    def _detectar_num_frames(self, sheet, frame_width_hint=None):
        """
        Detecta automaticamente o número de frames em um sprite sheet.
        Tenta detectar a largura padrão do frame analisando o sprite sheet.
        """
        sheet_w, sheet_h = sheet.get_width(), sheet.get_height()
        
        if frame_width_hint:
            # Se forneceu uma largura sugerida, usa ela
            num_frames = sheet_w // frame_width_hint
            if num_frames > 0 and (num_frames * frame_width_hint) == sheet_w:
                return num_frames, frame_width_hint
        
        # Tenta detectar automaticamente larguras comuns de frames
        # Ordenado do maior para o menor para pegar a divisão mais provável
        larguras_comuns = [256, 192, 144, 128, 112, 96, 80, 64, 48, 32]
        
        melhor_opcao = None
        melhor_score = 0
        
        for largura in larguras_comuns:
            if sheet_w % largura == 0:
                num_frames = sheet_w // largura
                if num_frames > 0:
                    # Prefere números de frames entre 4 e 20 (mais comum em sprites)
                    if 4 <= num_frames <= 20:
                        return num_frames, largura
                    # Se não está na faixa ideal, guarda como opção
                    if melhor_opcao is None or (melhor_score < num_frames <= 20):
                        melhor_opcao = (num_frames, largura)
                        melhor_score = num_frames
        
        # Se encontrou uma opção, usa ela
        if melhor_opcao:
            return melhor_opcao
        
        # Se não encontrou, tenta dividir por potências de 2 começando de baixo
        # Começa com 32 e vai aumentando
        largura = 32
        while largura <= sheet_w:
            if sheet_w % largura == 0:
                num_frames = sheet_w // largura
                if num_frames > 0 and num_frames <= 30:  # Limite razoável
                    return num_frames, largura
            largura *= 2
        
        # Fallback: assume que todo o sprite sheet é um único frame
        return 1, sheet_w
    
    def _load_frames(self, caminho, num_frames=None, scale=1.0, frame_width_hint=None):
        caminho = os.path.normpath(caminho)
        try:
            sheet = pygame.image.load(caminho).convert_alpha()
        except Exception as e:
            print(f"[Inimigo] Aviso: não foi possível carregar '{caminho}': {e}")
            return [self._fallback_surface(scale)]
        
        sheet_w, sheet_h = sheet.get_width(), sheet.get_height()
        
        # Se num_frames não foi fornecido ou é 0, detecta automaticamente
        if num_frames is None or num_frames <= 0:
            num_frames, frame_w = self._detectar_num_frames(sheet, frame_width_hint)
            print(f"[Inimigo] Detectados {num_frames} frames em '{os.path.basename(caminho)}' (largura: {frame_w}px)")
        else:
            # Se forneceu num_frames, usa ele
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
                print(f"[Inimigo] Erro ao extrair frame {i}: {e}")
                # Se der erro, adiciona um frame vazio para manter o índice
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
        """Calcula a distância até o alvo (usando coordenadas do mundo)"""
        # target_x é coordenada do mundo (x do protagonista no mundo)
        # target_y é a coordenada vertical do protagonista (a câmera não se move em Y neste jogo,
        # então podemos comparar diretamente com self.rect.centery).
        dx = target_x - self.world_x
        dy = target_y - self.rect.centery
        return math.sqrt(dx * dx + dy * dy)
    
    def atualizar_direcao(self, target_world_x, camera_x=0):
        """Atualiza a direção visual do inimigo baseada na posição do protagonista na TELA.

        Usamos coordenadas de tela (target_world_x - camera_x) ao comparar com
        self.rect.centerx para evitar viradas erradas quando a câmera se move.

        Args:
            target_world_x: posição X do protagonista no mundo
            camera_x: posição X da câmera (padrão 0)
        """
        # Converte posição do protagonista para coordenada de tela e compara
        target_screen_x = target_world_x - camera_x
        enemy_screen_centerx = self.rect.centerx

        if target_screen_x > enemy_screen_centerx:
            self.facing = "right"
        elif target_screen_x < enemy_screen_centerx:
            self.facing = "left"
    
    def pode_atirar(self, target_x, target_y):
        """Verifica se o inimigo pode atirar no alvo"""
        distancia = self.calcular_distancia(target_x, target_y)
        return (distancia <= self.shoot_range and 
                self.shoot_cooldown <= 0.0 and 
                self.shot_timer <= 0.0)
    
    def detectar_protagonista(self, target_x, target_y):
        """Verifica se o protagonista está dentro do alcance de detecção"""
        distancia = self.calcular_distancia(target_x, target_y)
        return distancia <= self.detection_range
    
    def shoot(self, target_x, target_y):
        """Dispara um projétil direcionado ao alvo"""
        if not self.alive or not self.pode_atirar(target_x, target_y):
            return None
        
        self.shot_timer = self.shot_duration
        self.shoot_cooldown = self.shoot_interval
        
        # Calcula direção do tiro usando coordenadas do mundo
        # target_x e target_y são coordenadas do mundo do protagonista
        enemy_world_x = self.world_x
        enemy_world_y = self.rect.centery  # Y é o mesmo em mundo e tela
        
        dx = target_x - enemy_world_x
        dy = target_y - enemy_world_y
        distancia = math.sqrt(dx * dx + dy * dy)
        
        if distancia == 0:
            direction_x = 0
            direction_y = 0
        else:
            direction_x = dx / distancia
            direction_y = dy / distancia
        
        # Ponto de origem do projétil na tela (usa posição da tela para renderização)
        muzzle_x = self.rect.centerx
        muzzle_y = self.rect.centery
        
        speed = 8
        return ProjetilInimigo(muzzle_x, muzzle_y, direction_x, direction_y, speed, self.scale)
    
    def take_damage(self, damage=1):
        """Inflige dano ao inimigo - garante que cada inimigo é tratado individualmente"""
        # Verifica se já está morrendo ou morto
        if self.is_dying or not self.alive:
            return  # Já está morrendo ou morto, não recebe mais dano
        
        # Aplica dano apenas a este inimigo específico
        self.health -= damage
        
        if self.health <= 0:
            # Marca este inimigo específico como morrendo
            self.is_dying = True
            self.alive = False
            self.frame_index = 0  # Reinicia a animação de morte
            self.animation_timer = 0.0
            self.dead_timer = 0.0
    
    def _executar_comportamento_ia(self, target_x, target_y, distancia, dt):
        """Executa o comportamento específico baseado no tipo de IA"""
        moving = False
        
        if self.ai_type == "agressivo":
            # Agressivo: persegue rapidamente e atira com frequência
            if distancia <= self.detection_range:
                if distancia > self.shoot_range:
                    # Persegue
                    moving = True
                    if target_x < self.world_x:
                        self.world_x -= self.speed
                    else:
                        self.world_x += self.speed
                # Sempre tenta atirar quando detecta
            
        elif self.ai_type == "defensivo":
            # Defensivo: mantém distância e recua se muito perto
            if distancia <= self.detection_range:
                if distancia < 250:  # Muito perto, recua
                    moving = True
                    if target_x < self.world_x:
                        self.world_x += self.speed * 0.8  # Recua
                    else:
                        self.world_x -= self.speed * 0.8
                elif distancia > self.shoot_range:
                    # Mantém distância ideal
                    moving = True
                    if target_x < self.world_x:
                        self.world_x -= self.speed * 0.6
                    else:
                        self.world_x += self.speed * 0.6
            
        elif self.ai_type == "perseguidor":
            # Perseguidor: sempre tenta se aproximar, só atira quando muito perto
            if distancia <= self.detection_range:
                if distancia > self.shoot_range:
                    # Persegue agressivamente
                    moving = True
                    if target_x < self.world_x:
                        self.world_x -= self.speed
                    else:
                        self.world_x += self.speed
            
        elif self.ai_type == "atirador":
            # Atirador: fica parado e atira frequentemente
            # Não se move, apenas atira
            moving = False
            
        elif self.ai_type == "patrulheiro":
            # Patrulheiro: patrulha quando não detecta, persegue quando detecta
            if distancia <= self.detection_range:
                # Detectou o protagonista, persegue
                if distancia > self.shoot_range:
                    moving = True
                    if target_x < self.world_x:
                        self.world_x -= self.speed
                    else:
                        self.world_x += self.speed
            else:
                # Patrulha de um lado para outro
                self.patrol_timer += dt
                if self.patrol_timer > 3.0:  # Muda direção a cada 3 segundos
                    self.patrol_direction *= -1
                    self.patrol_timer = 0.0
                moving = True
                self.world_x += self.speed * 0.6 * self.patrol_direction  # Patrulha mais rápido
            
        elif self.ai_type == "cuidadoso":
            # Cuidadoso: mantém distância média, só atira quando tem certeza
            if distancia <= self.detection_range:
                # Mantém distância ideal (entre 300-400 pixels)
                if distancia < 300:
                    # Muito perto, recua
                    moving = True
                    if target_x < self.world_x:
                        self.world_x += self.speed * 0.7
                    else:
                        self.world_x -= self.speed * 0.7
                elif distancia > 400:
                    # Muito longe, aproxima um pouco
                    moving = True
                    if target_x < self.world_x:
                        self.world_x -= self.speed * 0.9
                    else:
                        self.world_x += self.speed * 0.9
        
        return moving
    
    def update(self, dt, camera_x, protagonista_pos=None):
        """Atualiza o inimigo"""
        # Atualiza posição no mundo baseada na câmera
        # O inimigo fica fixo no mundo, mas sua posição na tela muda com a câmera
        self.rect.x = self.world_x - camera_x
        
        # Se está morrendo, mostra animação de morte
        if self.is_dying:
            self._update_death_animation(dt)
            return
        
        if not self.alive:
            return
        
        # Atualiza cooldowns
        if self.shoot_cooldown > 0:
            self.shoot_cooldown -= dt
        if self.shot_timer > 0:
            self.shot_timer -= dt
        
        # Comportamento do inimigo baseado no tipo de IA
        moving = False
        if protagonista_pos:
            target_x, target_y = protagonista_pos
            distancia = self.calcular_distancia(target_x, target_y)
            
            # SEMPRE atualiza a direção para olhar para o protagonista (independente da distância)
            # Passa camera_x para converter para coordenadas de tela dentro do método
            self.atualizar_direcao(target_x, camera_x)
            
            # Executa comportamento específico baseado no tipo de IA
            moving = self._executar_comportamento_ia(target_x, target_y, distancia, dt)
        
        # Escolhe animação
        if self.shot_timer > 0:
            frames = self.shot_frames if self.shot_frames else self.idle_frames
            frame_time = max(0.06, self.animation_speed * 0.8)
        elif moving:
            frames = self.run_frames if self.run_frames else self.idle_frames
            frame_time = self.animation_speed
        else:
            frames = self.idle_frames
            frame_time = self.animation_speed
        
        # Atualiza animação
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
    
    def _update_death_animation(self, dt):
        """Atualiza a animação de morte do inimigo"""
        if not self.dead_frames or len(self.dead_frames) == 0:
            # Se não tem frames de morte, remove imediatamente
            self.kill()
            return
        
        total_frames = len(self.dead_frames)
        last_frame_index = total_frames - 1
        
        # Verifica se está no último frame
        if self.frame_index == last_frame_index:
            # Está no último frame, conta o tempo
            self.dead_timer += dt
            if self.dead_timer >= self.dead_last_frame_duration:
                # Passou 2 segundos no último frame, remove o inimigo
                self.kill()
                return
            # Ainda está no tempo, mantém o último frame
            frame = self.dead_frames[last_frame_index]
        else:
            # Ainda não chegou no último frame, anima normalmente
            self.animation_timer += dt
            frame_time = self.animation_speed
            
            if self.animation_timer >= frame_time:
                passos = int(self.animation_timer / frame_time)
                self.animation_timer -= passos * frame_time
                self.frame_index = min(self.frame_index + passos, last_frame_index)
                frame = self.dead_frames[self.frame_index]
            else:
                frame = self.dead_frames[self.frame_index]
        
        # Aplica o frame, mantendo a posição
        prev_centerx = self.rect.centerx
        prev_bottom = self.rect.bottom
        
        # Mantém a direção que estava quando morreu (não flipa durante morte)
        if self.facing == "left":
            frame = pygame.transform.flip(frame, True, False)
        
        self.image = frame
        self.rect = self.image.get_rect()
        self.rect.centerx = prev_centerx
        self.rect.bottom = prev_bottom


class InimigoCyborg(pygame.sprite.Sprite):
    """Inimigo Cyborg - ataca com soco ao invés de atirar"""
    def __init__(self, x, y, scale=1.5, idle_count=None, run_count=None, punch_count=None, ai_type=None):
        super().__init__()
        self.scale = float(scale) if scale >= 0.5 else 0.5
        
        # Tipo de IA (se None, escolhe aleatoriamente)
        ai_types = ["agressivo", "perseguidor", "patrulheiro"]
        self.ai_type = ai_type if ai_type else random.choice(ai_types)
        
        # Carrega animações do Cyborg (None = detecta automaticamente)
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
        self.speed = 2.5
        self.facing = "left"  # Inimigos começam olhando para esquerda por padrão
        
        # Física vertical
        self.vel_y = 0.0
        self.gravidade = 0.45
        self.no_chao = True
        
        # Sistema de soco (corpo-a-corpo)
        self.punch_cooldown = 0.0
        self.punch_interval = 2.0
        self.detection_range = 400
        self.punch_range = 80  # Alcance do soco (muito perto)
        
        # Saúde
        self.health = 10
        self.alive = True
        
        # Posição no mundo
        self.world_x = x
        
        # Variáveis para IA
        self.patrol_direction = random.choice([-1, 1])
        self.patrol_timer = 0.0
        
        # Configurações baseadas no tipo de IA
        self._configurar_ia()
    
    def _configurar_ia(self):
        """Configura parâmetros do Cyborg baseado no tipo de IA"""
        if self.ai_type == "agressivo":
            self.speed = 3.0
            self.punch_interval = 1.5
            self.detection_range = 500
            self.punch_range = 80
            self.health = 12
        elif self.ai_type == "perseguidor":
            self.speed = 3.2
            self.punch_interval = 1.8
            self.detection_range = 600
            self.punch_range = 80
            self.health = 10
        elif self.ai_type == "patrulheiro":
            self.speed = 2.8
            self.punch_interval = 2.0
            self.detection_range = 450
            self.punch_range = 80
            self.health = 10
    
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
    
    def _executar_comportamento_ia(self, target_x, target_y, distancia, dt):
        """Executa o comportamento específico baseado no tipo de IA"""
        moving = False
        
        if self.ai_type == "agressivo":
            # Agressivo: persegue rapidamente e soca quando perto
            if distancia <= self.detection_range:
                if distancia > self.punch_range:
                    moving = True
                    if target_x < self.world_x:
                        self.world_x -= self.speed
                    else:
                        self.world_x += self.speed
                elif self.pode_socar(target_x, target_y):
                    self.socar(target_x, target_y)
        
        elif self.ai_type == "perseguidor":
            # Perseguidor: sempre tenta se aproximar para socar
            if distancia <= self.detection_range:
                if distancia > self.punch_range:
                    moving = True
                    if target_x < self.world_x:
                        self.world_x -= self.speed
                    else:
                        self.world_x += self.speed
                elif self.pode_socar(target_x, target_y):
                    self.socar(target_x, target_y)
        
        elif self.ai_type == "patrulheiro":
            # Patrulheiro: patrulha quando não detecta, persegue quando detecta
            if distancia <= self.detection_range:
                if distancia > self.punch_range:
                    moving = True
                    if target_x < self.world_x:
                        self.world_x -= self.speed
                    else:
                        self.world_x += self.speed
                elif self.pode_socar(target_x, target_y):
                    self.socar(target_x, target_y)
            else:
                # Patrulha de um lado para o outro
                self.patrol_timer += dt
                if self.patrol_timer > 3.0:
                    self.patrol_direction *= -1
                    self.patrol_timer = 0.0
                moving = True
                self.world_x += self.speed * 0.6 * self.patrol_direction
        
        return moving
    
    def update(self, dt, camera_x, protagonista_pos=None):
        """Atualiza o Cyborg"""
        self.rect.x = self.world_x - camera_x
        
        # Se está morrendo, mostra animação de morte
        if self.is_dying:
            self._update_death_animation(dt)
            return
        
        if not self.alive:
            return
        
        # Atualiza cooldowns
        if self.punch_cooldown > 0:
            self.punch_cooldown -= dt
        if self.punch_timer > 0:
            self.punch_timer -= dt
        
        # Comportamento do Cyborg baseado no tipo de IA
        moving = False
        if protagonista_pos:
            target_x, target_y = protagonista_pos
            distancia = self.calcular_distancia(target_x, target_y)
            
            self.atualizar_direcao(target_x, camera_x)
            moving = self._executar_comportamento_ia(target_x, target_y, distancia, dt)
        
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
        
        # Atualiza animação
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
    
    def _update_death_animation(self, dt):
        """Atualiza a animação de morte do Cyborg"""
        if not self.dead_frames or len(self.dead_frames) == 0:
            self.kill()
            return
        
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
        
        prev_centerx = self.rect.centerx
        prev_bottom = self.rect.bottom
        
        if self.facing == "left":
            frame = pygame.transform.flip(frame, True, False)
        
        self.image = frame
        self.rect = self.image.get_rect()
        self.rect.centerx = prev_centerx
        self.rect.bottom = prev_bottom


class ProjetilInimigo(pygame.sprite.Sprite):
    """Projétil disparado pelos inimigos - usa o mesmo sprite do protagonista"""
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
        # Calcula o ângulo da direção
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
        if (self.rect.right < 0 or self.rect.left > 800 or 
            self.rect.bottom < 0 or self.rect.top > 600):
            self.kill()


def spawn_inimigo(camera_x, chao_y, screen_width, x_offset=0, lado="direita"):
    """
    Spawna um inimigo em uma posição relativa à câmera
    
    Args:
        camera_x: Posição atual da câmera
        chao_y: Altura do chão
        screen_width: Largura da tela
        x_offset: Offset em relação à câmera (0 = próximo à câmera, positivo = mais à frente/atrás)
        lado: "direita" para spawnar à direita, "esquerda" para spawnar à esquerda
    
    Returns:
        Inimigo ou None
    """
    spawn_y = chao_y - 50  # 50 pixels acima do chão
    
    if lado == "esquerda":
        # Spawna o inimigo à esquerda da câmera
        # x_offset positivo = mais à esquerda, negativo = mais próximo do centro
        if x_offset > 0:
            spawn_x = camera_x - x_offset
        else:
            # Se offset negativo, spawna em posição relativa à esquerda da tela
            spawn_x = camera_x + abs(x_offset)
    else:
        # Spawna o inimigo à direita da câmera (padrão)
        # x_offset positivo = mais à direita, negativo = mais próximo do centro
        if x_offset >= 0:
            spawn_x = camera_x + screen_width + x_offset
        else:
            # Se offset negativo, spawna dentro da tela (à direita do centro)
            spawn_x = camera_x + screen_width + x_offset
    
    # None = detecta automaticamente o número de frames
    return Inimigo(spawn_x, spawn_y, scale=1.5, idle_count=None, run_count=None, shot_count=None)


def spawn_inimigo_cyborg(camera_x, chao_y, screen_width, x_offset=0, lado="direita"):
    """
    Spawna um Cyborg em uma posição relativa à câmera
    
    Args:
        camera_x: Posição atual da câmera
        chao_y: Altura do chão
        screen_width: Largura da tela
        x_offset: Offset em relação à câmera (0 = próximo à câmera, positivo = mais à frente/atrás)
        lado: "direita" para spawnar à direita, "esquerda" para spawnar à esquerda
    
    Returns:
        InimigoCyborg ou None
    """
    spawn_y = chao_y - 50  # 50 pixels acima do chão
    
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
    return InimigoCyborg(spawn_x, spawn_y, scale=1.5, idle_count=None, run_count=None, punch_count=None)


def spawn_inimigos_aleatorios(camera_x, chao_y, screen_width, quantidade=3, espacamento=200):
    """
    Spawna múltiplos inimigos em posições aleatórias à frente
    
    Args:
        camera_x: Posição atual da câmera
        chao_y: Altura do chão
        screen_width: Largura da tela
        quantidade: Número de inimigos a spawnar
        espacamento: Espaçamento mínimo entre inimigos
    
    Returns:
        Lista de Inimigos
    """
    inimigos = []
    for i in range(quantidade):
        offset = screen_width + (i * espacamento)
        inimigo = spawn_inimigo(camera_x, chao_y, screen_width, offset)
        inimigos.append(inimigo)
    return inimigos

