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
        self.current_frames = self.idle_frames if self.idle_frames else [self._superficie_fallback(self.scale)]
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
    
    def _superficie_fallback(self, escala=1):
        superficie = pygame.Surface((32*escala, 48*escala), pygame.SRCALPHA)
        superficie.fill((100, 100, 200))
        return superficie
    
    def _detectar_numero_quadros(self, folha, dica_largura_quadro=None):
        """Detecta automaticamente o número de frames em um sprite sheet"""
        largura_folha, altura_folha = folha.get_width(), folha.get_height()
        
        if dica_largura_quadro:
            numero_quadros = largura_folha // dica_largura_quadro
            if numero_quadros > 0 and (numero_quadros * dica_largura_quadro) == largura_folha:
                return numero_quadros, dica_largura_quadro
        
        larguras_comuns = [256, 192, 144, 128, 112, 96, 80, 64, 48, 32]
        
        melhor_opcao = None
        melhor_pontuacao = 0
        
        for largura in larguras_comuns:
            if largura_folha % largura == 0:
                numero_quadros = largura_folha // largura
                if numero_quadros > 0:
                    if 4 <= numero_quadros <= 20:
                        return numero_quadros, largura
                    if melhor_opcao is None or (melhor_pontuacao < numero_quadros <= 20):
                        melhor_opcao = (numero_quadros, largura)
                        melhor_pontuacao = numero_quadros
        
        if melhor_opcao:
            return melhor_opcao
        
        largura = 32
        while largura <= largura_folha:
            if largura_folha % largura == 0:
                numero_quadros = largura_folha // largura
                if numero_quadros > 0 and numero_quadros <= 30:
                    return numero_quadros, largura
            largura *= 2
        
        return 1, largura_folha
    
    def _load_frames(self, caminho, num_frames=None, scale=1.0, frame_width_hint=None):
        caminho = os.path.normpath(caminho)
        try:
            folha = pygame.image.load(caminho).convert_alpha()
        except Exception:
            return [self._superficie_fallback(scale)]
        
        largura_folha, altura_folha = folha.get_width(), folha.get_height()
        
        if num_frames is None or num_frames <= 0:
            numero_quadros, largura_quadro = self._detectar_numero_quadros(folha, frame_width_hint)
        else:
            numero_quadros = num_frames
            # Calcula a largura exata de cada frame
            # Se não divide exatamente, ajusta para garantir que todos os frames sejam extraídos
            if largura_folha % numero_quadros == 0:
                largura_quadro = largura_folha // numero_quadros
            else:
                # Se não divide exatamente, usa divisão inteira e ajusta o último frame
                largura_quadro = largura_folha // numero_quadros
        
        quadros = []
        for i in range(numero_quadros):
            # Calcula a posição X exata de cada frame
            x_inicio = i * largura_quadro
            # Para o último frame, usa o resto da largura para evitar perder pixels
            if i == numero_quadros - 1:
                largura_atual = largura_folha - x_inicio
            else:
                largura_atual = largura_quadro
            
            # Garante que não ultrapasse os limites
            if x_inicio >= largura_folha or largura_atual <= 0:
                break
                
            rect = pygame.Rect(x_inicio, 0, largura_atual, altura_folha)
            try:
                quadro = folha.subsurface(rect).copy()
                nova_largura = max(1, int(round(quadro.get_width() * scale)))
                nova_altura = max(1, int(round(quadro.get_height() * scale)))
                quadro = pygame.transform.scale(quadro, (nova_largura, nova_altura))
                quadros.append(quadro)
            except Exception:
                quadros.append(self._superficie_fallback(scale))
        
        return quadros if quadros else [self._superficie_fallback(scale)]
    
    def aplicar_gravidade(self, chao_y):
        self.vel_y += self.gravidade
        self.rect.y += int(self.vel_y)
        if self.rect.bottom >= chao_y:
            self.rect.bottom = chao_y
            self.vel_y = 0.0
            self.no_chao = True
        else:
            self.no_chao = False
    
    def calcular_distancia(self, alvo_x, alvo_y):
        """Calcula a distância até o alvo"""
        delta_x = alvo_x - self.world_x
        delta_y = alvo_y - self.rect.centery
        return math.sqrt(delta_x * delta_x + delta_y * delta_y)
    
    def atualizar_direcao(self, alvo_mundo_x, camera_x=0):
        """Atualiza a direção visual do Cyborg"""
        alvo_tela_x = alvo_mundo_x - camera_x
        centro_x_tela_inimigo = self.rect.centerx

        if alvo_tela_x > centro_x_tela_inimigo:
            self.facing = "right"
        elif alvo_tela_x < centro_x_tela_inimigo:
            self.facing = "left"
    
    def pode_socar(self, alvo_x, alvo_y):
        """Verifica se o Cyborg pode socar o alvo"""
        distancia = self.calcular_distancia(alvo_x, alvo_y)
        return (distancia <= self.punch_range and 
                self.punch_cooldown <= 0.0 and 
                self.punch_timer <= 0.0)
    
    def socar(self, alvo_x, alvo_y):
        """Executa um soco no alvo (ataque corpo-a-corpo)"""
        if not self.alive or not self.pode_socar(alvo_x, alvo_y):
            return False
        
        self.punch_timer = self.punch_duration
        self.punch_cooldown = self.punch_interval
        return True
    
    def take_damage(self, dano=1):
        """Inflige dano ao Cyborg"""
        if self.is_dying or not self.alive:
            return
        
        self.health -= dano
        
        if self.health <= 0:
            self.is_dying = True
            self.alive = False
            self.frame_index = 0
            self.animation_timer = 0.0
            self.dead_timer = 0.0
            self._was_dying = False  # Reseta para detectar morte no próximo frame
    
    def _executar_comportamento(self, alvo_x, alvo_y, distancia, delta_tempo):
        """Comportamento: persegue o player e soca quando dentro do alcance"""
        movendo = False
        
        # Se está socando, não se move
        if self.punch_timer > 0:
            return False
        
        # Persegue o player quando detecta
        if distancia <= self.detection_range:
            # Verifica se está na mesma posição X do player (em cima do player)
            distancia_x = abs(alvo_x - self.world_x)
            esta_acima_jogador = distancia_x <= 30  # Tolerância de 30 pixels
            
            # Se está em cima do player, anda para a direita
            if esta_acima_jogador:
                movendo = True
                self.world_x += self.speed
                return movendo
            
            if distancia > self.punch_range:
                # Persegue o player
                movendo = True
                if alvo_x < self.world_x:
                    self.world_x -= self.speed
                else:
                    self.world_x += self.speed
            elif self.pode_socar(alvo_x, alvo_y):
                # Está perto o suficiente, soca (e para de se mover)
                self.socar(alvo_x, alvo_y)
        
        return movendo
    
    def update(self, delta_tempo, camera_x, protagonista_pos=None):
        """Atualiza o Cyborg"""
        # Se está morrendo, mostra animação de morte
        if self.is_dying:
            self._atualizar_animacao_morte(delta_tempo, camera_x)
            return
        
        if not self.alive:
            return
        
        # Atualiza cooldowns
        if self.punch_cooldown > 0:
            self.punch_cooldown -= delta_tempo
        if self.punch_timer > 0:
            self.punch_timer -= delta_tempo
        
        # Comportamento: persegue o player
        movendo = False
        if protagonista_pos:
            alvo_x, alvo_y = protagonista_pos
            distancia = self.calcular_distancia(alvo_x, alvo_y)
            
            # Sempre atualiza a direção para olhar para o protagonista
            self.atualizar_direcao(alvo_x, camera_x)
            
            # Executa comportamento de perseguição
            movendo = self._executar_comportamento(alvo_x, alvo_y, distancia, delta_tempo)
        
        # Calcula a posição na tela (sempre baseada em world_x - camera_x)
        centro_x_tela = int(self.world_x - camera_x)
        
        # Para o soco, usa uma posição Y fixa baseada no rect atual
        # Mas se está começando a socar, salva a posição Y inicial
        esta_socando = self.punch_timer > 0
        if esta_socando:
            # Se está socando, usa a posição Y salva quando começou a socar
            if not hasattr(self, '_base_inicio_soco'):
                # Primeira vez socando neste ciclo - salva a posição Y
                if hasattr(self, 'rect') and hasattr(self.rect, 'bottom'):
                    self._base_inicio_soco = self.rect.bottom
                else:
                    self._base_inicio_soco = 0
            base_anterior = self._base_inicio_soco
        else:
            # Não está socando - limpa a posição salva e usa a atual
            if hasattr(self, '_base_inicio_soco'):
                delattr(self, '_base_inicio_soco')
            if hasattr(self, 'rect') and hasattr(self.rect, 'bottom'):
                base_anterior = self.rect.bottom
            else:
                base_anterior = 0
        
        # Identifica o estado atual da animação
        if esta_socando:
            estado_atual = "punch"
            quadros = self.punch_frames if self.punch_frames else self.idle_frames
            tempo_quadro = max(0.06, self.animation_speed * 0.8)
        elif movendo:
            estado_atual = "run"
            quadros = self.run_frames if self.run_frames else self.idle_frames
            tempo_quadro = self.animation_speed
        else:
            estado_atual = "idle"
            quadros = self.idle_frames
            tempo_quadro = self.animation_speed
        
        # Detecta mudança de animação comparando estados
        animacao_mudou = False
        if not hasattr(self, '_ultimo_estado_animacao') or self._ultimo_estado_animacao != estado_atual:
            # Mudou de animação - reseta frame_index e timer
            self.frame_index = 0
            self.animation_timer = 0.0
            self._ultimo_estado_animacao = estado_atual
            animacao_mudou = True
        
        # Atualiza animação
        self.animation_timer += delta_tempo
        quadro_mudou = False
        if self.animation_timer >= tempo_quadro:
            passos = int(self.animation_timer / tempo_quadro)
            self.animation_timer -= passos * tempo_quadro
            self.frame_index = (self.frame_index + passos) % len(quadros)
            quadro_mudou = True
        
        # Garante que frame_index está dentro do range
        if self.frame_index >= len(quadros) or self.frame_index < 0:
            self.frame_index = 0
        
        # SEMPRE atualiza o frame e rect para garantir que não há frames antigos
        # Pega o frame e cria uma cópia para evitar problemas de referência
        quadro = quadros[self.frame_index].copy()
        if self.facing == "left":
            quadro = pygame.transform.flip(quadro, True, False)
        
        # Atualiza image
        self.image = quadro
        
        # Cria um NOVO rect do zero (nunca reutiliza o rect antigo)
        self.rect = self.image.get_rect()
        
        # Define posições: Y preserva altura, X sempre baseado em world_x
        # IMPORTANTE: Define centerx primeiro, depois bottom
        self.rect.centerx = centro_x_tela
        self.rect.bottom = base_anterior
    
    def _atualizar_animacao_morte(self, delta_tempo, camera_x):
        """Atualiza a animação de morte do Cyborg"""
        if not self.dead_frames or len(self.dead_frames) == 0:
            self.kill()
            return
        
        # Calcula a posição na tela primeiro
        centro_x_tela = int(self.world_x - camera_x)
        
        total_quadros = len(self.dead_frames)
        indice_ultimo_quadro = total_quadros - 1
        
        if self.frame_index == indice_ultimo_quadro:
            self.dead_timer += delta_tempo
            if self.dead_timer >= self.dead_last_frame_duration:
                self.kill()
                return
            quadro = self.dead_frames[indice_ultimo_quadro]
        else:
            self.animation_timer += delta_tempo
            tempo_quadro = self.animation_speed
            
            if self.animation_timer >= tempo_quadro:
                passos = int(self.animation_timer / tempo_quadro)
                self.animation_timer -= passos * tempo_quadro
                self.frame_index = min(self.frame_index + passos, indice_ultimo_quadro)
                quadro = self.dead_frames[self.frame_index]
            else:
                quadro = self.dead_frames[self.frame_index]
        
        # Preserva posições antes de recriar o rect
        base_anterior = self.rect.bottom if hasattr(self, 'rect') else 0
        centro_x_anterior = self.rect.centerx if hasattr(self, 'rect') else centro_x_tela
        
        if self.facing == "left":
            quadro = pygame.transform.flip(quadro, True, False)
        
        self.image = quadro
        self.rect = self.image.get_rect()
        # Restaura posições após recriar o rect
        self.rect.centerx = centro_x_anterior
        self.rect.bottom = base_anterior
        
        # SEMPRE atualiza a posição X baseado em world_x - camera_x
        # Isso garante que cada inimigo tenha sua própria posição única mesmo quando morrendo
        self.rect.centerx = centro_x_tela


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
    posicao_y_spawn = player_y  # Mesma altura do player
    
    if lado == "esquerda":
        if x_offset > 0:
            posicao_x_spawn = camera_x - x_offset
        else:
            posicao_x_spawn = camera_x + abs(x_offset)
    else:
        if x_offset >= 0:
            posicao_x_spawn = camera_x + screen_width + x_offset
        else:
            posicao_x_spawn = camera_x + screen_width + x_offset
    
    # None = detecta automaticamente o número de frames
    # Scale 3.2 para tornar o Cyborg maior
    return InimigoCyborg(posicao_x_spawn, posicao_y_spawn, scale=3.2, idle_count=None, run_count=None, punch_count=None)


class Careca(pygame.sprite.Sprite):
    """Inimigo Careca - atirador que fica parado e atira de longe"""
    def __init__(self, x, y, scale=2.5, idle_count=None, shot_count=None):
        super().__init__()
        self.scale = float(scale) if scale >= 0.5 else 0.5
        
        # Carrega animações do Careca
        # Idle_2.png tem 7 frames - força isso para garantir detecção correta
        if idle_count is None:
            idle_count = 7  # Idle_2.png tem exatamente 7 frames
        self.idle_frames = self._load_frames(idle_careca, idle_count, self.scale)
        # Garante que tem exatamente 7 frames (remove duplicatas se houver)
        if len(self.idle_frames) > 7:
            self.idle_frames = self.idle_frames[:7]
        elif len(self.idle_frames) < 7 and len(self.idle_frames) > 0:
            # Se tiver menos de 7, completa com o último frame
            while len(self.idle_frames) < 7:
                self.idle_frames.append(self.idle_frames[-1].copy())
        # Shot.png tem 12 frames - força isso para garantir detecção correta
        if shot_count is None:
            shot_count = 12  # Shot.png tem exatamente 12 frames
        self.shot_frames = self._load_frames(shot_careca, shot_count, self.scale)
        # Garante que shot_frames tem exatamente o número esperado de frames
        if len(self.shot_frames) > shot_count:
            self.shot_frames = self.shot_frames[:shot_count]
        elif len(self.shot_frames) < shot_count and len(self.shot_frames) > 0:
            # Se tiver menos frames, completa com o último frame
            while len(self.shot_frames) < shot_count:
                self.shot_frames.append(self.shot_frames[-1].copy())
        
        self.dead_frames = self._load_frames(dead_careca, None, self.scale)  # Detecta automaticamente
        
        # CRÍTICO: Normaliza TODAS as animações com as MESMAS dimensões máximas
        # Isso garante que idle, shot e dead tenham exatamente o mesmo tamanho
        # evitando movimento visual quando muda de animação
        todas_animacoes = []
        if self.idle_frames:
            todas_animacoes.extend(self.idle_frames)
        if self.shot_frames:
            todas_animacoes.extend(self.shot_frames)
        if self.dead_frames:
            todas_animacoes.extend(self.dead_frames)
        
        # Encontra a largura e altura máxima entre TODAS as animações
        if todas_animacoes:
            largura_maxima_global = max(frame.get_width() for frame in todas_animacoes)
            altura_maxima_global = max(frame.get_height() for frame in todas_animacoes)
        else:
            # Fallback se não houver frames
            largura_maxima_global = 32
            altura_maxima_global = 32
        
        # Normaliza cada animação usando as dimensões máximas globais
        self.idle_frames = self._normalizar_frames_com_dimensoes(self.idle_frames, largura_maxima_global, altura_maxima_global)
        self.shot_frames = self._normalizar_frames_com_dimensoes(self.shot_frames, largura_maxima_global, altura_maxima_global)
        self.dead_frames = self._normalizar_frames_com_dimensoes(self.dead_frames, largura_maxima_global, altura_maxima_global)
        
        # Validação: garante que os frames foram carregados corretamente
        if len(self.idle_frames) == 0:
            print(f"AVISO: Nenhum frame idle foi carregado para Careca!")
            self.idle_frames = [self._superficie_fallback(self.scale)]
        if len(self.shot_frames) == 0:
            print(f"AVISO: Nenhum frame shot foi carregado para Careca! Usando idle como fallback.")
            self.shot_frames = self.idle_frames.copy() if len(self.idle_frames) > 0 else [self._superficie_fallback(self.scale)]
        
        # Estado de animação
        # CRÍTICO: Sempre usa shot_frames (nunca muda para idle)
        self.current_frames = self.shot_frames if self.shot_frames else (self.idle_frames if self.idle_frames else [self._superficie_fallback(self.scale)])
        self.frame_index = 0
        self.animation_timer = 0.0
        self.animation_speed = 0.12
        self.shot_timer = 0.0
        self.shot_duration = 1.0  # Duração do tiro (aumentado para mostrar a animação completa)
        self._ultimos_quadros = self.shot_frames if self.shot_frames else self.idle_frames  # Sempre shot_frames
        
        # Estado de morte
        self.is_dying = False
        self.dead_timer = 0.0
        self.dead_last_frame_duration = 2.0  # 2 segundos no último frame
        self._was_dying = False  # Flag para detectar quando acabou de morrer
        self._death_base_y = None  # Posição Y preservada quando morre
        
        # Movimento e direção - fica parado
        self.speed = 0.0  # Não se move
        self.facing = "left"  # Inimigos começam olhando para esquerda por padrão
        
        # Inicializa a imagem corretamente com flip se necessário
        # CRÍTICO: Usa shot_frames como padrão (nunca idle)
        quadro_inicial = self.shot_frames[0] if self.shot_frames else (self.idle_frames[0] if self.idle_frames else self._superficie_fallback(self.scale))
        quadro_inicial = quadro_inicial.copy()
        if self.facing == "left":
            quadro_inicial = pygame.transform.flip(quadro_inicial, True, False)
        self.image = quadro_inicial
        self.rect = self.image.get_rect(center=(x, y))
        
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
    
    def _superficie_fallback(self, escala=1):
        superficie = pygame.Surface((32*escala, 48*escala), pygame.SRCALPHA)
        superficie.fill((255, 0, 0))
        return superficie
    
    def _detectar_numero_quadros(self, folha, dica_largura_quadro=None):
        """Detecta automaticamente o número de frames em um sprite sheet"""
        largura_folha, altura_folha = folha.get_width(), folha.get_height()
        
        if dica_largura_quadro:
            numero_quadros = largura_folha // dica_largura_quadro
            if numero_quadros > 0 and (numero_quadros * dica_largura_quadro) == largura_folha:
                return numero_quadros, dica_largura_quadro
        
        larguras_comuns = [256, 192, 144, 128, 112, 96, 80, 64, 48, 32]
        
        melhor_opcao = None
        melhor_pontuacao = 0
        
        for largura in larguras_comuns:
            if largura_folha % largura == 0:
                numero_quadros = largura_folha // largura
                if numero_quadros > 0:
                    if 4 <= numero_quadros <= 20:
                        return numero_quadros, largura
                    if melhor_opcao is None or (melhor_pontuacao < numero_quadros <= 20):
                        melhor_opcao = (numero_quadros, largura)
                        melhor_pontuacao = numero_quadros
        
        if melhor_opcao:
            return melhor_opcao
        
        largura = 32
        while largura <= largura_folha:
            if largura_folha % largura == 0:
                numero_quadros = largura_folha // largura
                if numero_quadros > 0 and numero_quadros <= 30:
                    return numero_quadros, largura
            largura *= 2
        
        return 1, largura_folha
    
    def _load_frames(self, caminho, num_frames=None, scale=1.0, frame_width_hint=None):
        caminho = os.path.normpath(caminho)
        try:
            folha = pygame.image.load(caminho).convert_alpha()
        except Exception:
            return [self._superficie_fallback(scale)]
        
        largura_folha, altura_folha = folha.get_width(), folha.get_height()
        
        if num_frames is None or num_frames <= 0:
            numero_quadros, largura_quadro = self._detectar_numero_quadros(folha, frame_width_hint)
        else:
            numero_quadros = num_frames
            # Calcula a largura exata de cada frame
            # Se não divide exatamente, ajusta para garantir que todos os frames sejam extraídos
            if largura_folha % numero_quadros == 0:
                largura_quadro = largura_folha // numero_quadros
            else:
                # Se não divide exatamente, usa divisão inteira e ajusta o último frame
                largura_quadro = largura_folha // numero_quadros
        
        quadros = []
        for i in range(numero_quadros):
            # Calcula a posição X exata de cada frame
            x_inicio = i * largura_quadro
            # Para o último frame, usa o resto da largura para evitar perder pixels
            if i == numero_quadros - 1:
                largura_atual = largura_folha - x_inicio
            else:
                largura_atual = largura_quadro
            
            # Garante que não ultrapasse os limites
            if x_inicio >= largura_folha or largura_atual <= 0:
                break
                
            rect = pygame.Rect(x_inicio, 0, largura_atual, altura_folha)
            try:
                quadro = folha.subsurface(rect).copy()
                nova_largura = max(1, int(round(quadro.get_width() * scale)))
                nova_altura = max(1, int(round(quadro.get_height() * scale)))
                quadro = pygame.transform.scale(quadro, (nova_largura, nova_altura))
                quadros.append(quadro)
            except Exception:
                quadros.append(self._superficie_fallback(scale))
        
        return quadros if quadros else [self._superficie_fallback(scale)]
    
    def aplicar_gravidade(self, chao_y):
        self.vel_y += self.gravidade
        self.rect.y += int(self.vel_y)
        if self.rect.bottom >= chao_y:
            self.rect.bottom = chao_y
            self.vel_y = 0.0
            self.no_chao = True
        else:
            self.no_chao = False
    
    def _normalizar_largura_frames(self, frames):
        """Garante que todos os frames tenham a mesma largura e altura para evitar movimento durante animação"""
        if not frames or len(frames) == 0:
            return frames
        
        # Encontra a largura e altura máxima de todos os frames
        largura_maxima = max(frame.get_width() for frame in frames)
        altura_maxima = max(frame.get_height() for frame in frames)
        
        # Redimensiona todos os frames para terem exatamente a mesma largura e altura
        frames_normalizados = []
        for frame in frames:
            # Cria uma nova superfície com a largura e altura máximas (transparente)
            frame_normalizado = pygame.Surface((largura_maxima, altura_maxima), pygame.SRCALPHA)
            
            # Calcula a posição X e Y para centralizar o frame original
            offset_x = (largura_maxima - frame.get_width()) // 2
            offset_y = (altura_maxima - frame.get_height()) // 2
            
            # Copia o frame original para a superfície normalizada, centralizado
            frame_normalizado.blit(frame, (offset_x, offset_y))
            
            frames_normalizados.append(frame_normalizado)
        
        return frames_normalizados
    
    def _normalizar_frames_com_dimensoes(self, frames, largura_maxima, altura_maxima):
        """Normaliza frames usando dimensões pré-definidas (garante que todas as animações tenham o mesmo tamanho)"""
        if not frames or len(frames) == 0:
            return frames
        
        # Redimensiona todos os frames para terem exatamente a mesma largura e altura
        frames_normalizados = []
        for frame in frames:
            # Cria uma nova superfície com a largura e altura máximas (transparente)
            frame_normalizado = pygame.Surface((largura_maxima, altura_maxima), pygame.SRCALPHA)
            
            # Calcula a posição X e Y para centralizar o frame original
            offset_x = (largura_maxima - frame.get_width()) // 2
            offset_y = (altura_maxima - frame.get_height()) // 2
            
            # Copia o frame original para a superfície normalizada, centralizado
            frame_normalizado.blit(frame, (offset_x, offset_y))
            
            frames_normalizados.append(frame_normalizado)
        
        return frames_normalizados
    
    def calcular_distancia(self, alvo_x, alvo_y):
        """Calcula a distância até o alvo"""
        delta_x = alvo_x - self.world_x
        delta_y = alvo_y - self.rect.centery
        return math.sqrt(delta_x * delta_x + delta_y * delta_y)
    
    def atualizar_direcao(self, alvo_mundo_x, camera_x=0):
        """Atualiza a direção visual do Careca"""
        alvo_tela_x = alvo_mundo_x - camera_x
        centro_x_tela_inimigo = self.rect.centerx

        if alvo_tela_x > centro_x_tela_inimigo:
            self.facing = "right"
        elif alvo_tela_x < centro_x_tela_inimigo:
            self.facing = "left"
    
    def pode_atirar(self, alvo_x, alvo_y):
        """Verifica se o Careca pode atirar no alvo"""
        distancia = self.calcular_distancia(alvo_x, alvo_y)
        return (distancia <= self.shoot_range and 
                self.shoot_cooldown <= 0.0 and 
                self.shot_timer <= 0.0)
    
    def shoot(self, alvo_x, alvo_y):
        """Dispara um projétil horizontal direcionado ao alvo"""
        if not self.alive or not self.pode_atirar(alvo_x, alvo_y):
            return None
        
        self.shot_timer = self.shot_duration
        self.shoot_cooldown = self.shoot_interval
        
        # Calcula direção do tiro apenas horizontal (sem componente vertical)
        mundo_x_inimigo = self.world_x
        
        delta_x = alvo_x - mundo_x_inimigo
        
        # Direção apenas horizontal (sempre para direita ou esquerda)
        if delta_x == 0:
            direcao_x = 0
        else:
            direcao_x = 1 if delta_x > 0 else -1
        
        # Sem componente vertical - projétil sempre horizontal
        direcao_y = 0
        
        # Ponto de origem do projétil na tela
        # A arma está próxima ao centro horizontal do sprite, com um pequeno offset na direção do tiro
        # Usa centerx como base e adiciona um offset pequeno baseado na direção
        offset_x_arma = int(15 * self.scale)  # Offset horizontal da arma em relação ao centro
        if self.facing == "right":
            # Arma está ligeiramente à direita do centro
            posicao_x_cano = self.rect.centerx + offset_x_arma
        else:
            # Arma está ligeiramente à esquerda do centro
            posicao_x_cano = self.rect.centerx - offset_x_arma
        
        # Ajusta a posição Y para a altura da arma
        # A arma está próxima ao centro vertical, ligeiramente acima do centro
        # Usa centery como base e ajusta para cima (offset negativo)
        offset_y_arma = int(self.rect.height * 0.10)  # 10% da altura (offset para cima do centro)
        posicao_y_cano = self.rect.centery - offset_y_arma  # Ligeiramente acima do centro
        
        velocidade = 8
        return ProjetilInimigo(posicao_x_cano, posicao_y_cano, direcao_x, direcao_y, velocidade, self.scale)
    
    def take_damage(self, dano=1):
        """Inflige dano ao Careca"""
        if self.is_dying or not self.alive:
            return
        
        self.health -= dano
        
        if self.health <= 0:
            # CRÍTICO: Preserva a posição Y ANTES de iniciar a animação de morte
            # Isso garante que o inimigo morre na mesma posição onde estava
            if hasattr(self, 'rect') and self.rect is not None:
                self._death_base_y = self.rect.bottom
            else:
                self._death_base_y = None
            
            self.is_dying = True
            self.alive = False
            self.frame_index = 0
            self.animation_timer = 0.0
            self.dead_timer = 0.0
            self._was_dying = False  # Reseta para detectar morte no próximo frame
    
    def update(self, delta_tempo, camera_x, protagonista_pos=None):
        """Atualiza o Careca"""
        # Se está morrendo, mostra animação de morte
        if self.is_dying:
            self._atualizar_animacao_morte(delta_tempo, camera_x)
            return
        
        if not self.alive:
            return
        
        # Atualiza cooldowns
        if self.shoot_cooldown > 0:
            self.shoot_cooldown -= delta_tempo
        
        # Decrementa shot_timer (apenas para controle interno, não afeta a animação)
        if self.shot_timer > 0:
            self.shot_timer -= delta_tempo
            # Garante que não fica negativo
            if self.shot_timer < 0:
                self.shot_timer = 0.0
        else:
            self.shot_timer = 0.0
        
        # Comportamento: fica parado e atira
        if protagonista_pos:
            alvo_x, alvo_y = protagonista_pos
            distancia = self.calcular_distancia(alvo_x, alvo_y)
            
            # Sempre atualiza a direção para olhar para o protagonista
            self.atualizar_direcao(alvo_x, camera_x)
        
        # CRÍTICO: Sempre usa animação de shot (nunca muda para idle)
        # Isso evita problemas de transição e mantém a animação consistente
        # A animação de shot será repetida em loop continuamente
        quadros = self.shot_frames if self.shot_frames else self.idle_frames
        tempo_quadro = max(0.08, self.animation_speed)  # Velocidade normal para shot
        
        # Calcula a posição na tela primeiro
        centro_x_tela = int(self.world_x - camera_x)
        
        # Preserva posições ANTES de atualizar a animação (importante para manter posição fixa)
        # IMPORTANTE: Preserva o bottom ANTES de qualquer atualização para manter posição Y fixa
        if hasattr(self, 'rect') and self.rect is not None:
            base_anterior = self.rect.bottom
        else:
            # Se não tem rect ainda (primeira vez), usa uma posição padrão
            # O rect foi criado no __init__ com center=(x, y), então o bottom está definido
            base_anterior = self.rect.bottom if hasattr(self, 'rect') else 550  # CHAO_Y padrão
        
        # Como sempre usamos shot_frames, não há mudança de animação
        # Mas verificamos se os quadros mudaram (não deveria acontecer, mas por segurança)
        quadros_mudou = not hasattr(self, '_ultimos_quadros') or id(self._ultimos_quadros) != id(quadros)
        
        # Se os quadros mudaram (não deveria acontecer), reseta apenas para segurança
        if quadros_mudou:
            self.frame_index = 0
            self.animation_timer = 0.0
            self._ultimos_quadros = quadros
            # Garante que o frame_index está válido para a nova lista de quadros
            if len(quadros) > 0 and self.frame_index >= len(quadros):
                self.frame_index = 0
        
        # Atualiza animação normalmente (apenas o frame_index, não a posição)
        # IMPORTANTE: Garante que quadros não está vazio antes de atualizar
        if len(quadros) == 0:
            # Se não há frames, não atualiza a animação
            self.frame_index = 0
        else:
            # Garante que frame_index está dentro dos limites antes de atualizar
            if self.frame_index < 0:
                self.frame_index = 0
            elif self.frame_index >= len(quadros):
                self.frame_index = len(quadros) - 1
            
            # Atualiza animação normalmente (sempre em loop, sem transições)
            self.animation_timer += delta_tempo
            if self.animation_timer >= tempo_quadro:
                passos = int(self.animation_timer / tempo_quadro)
                self.animation_timer -= passos * tempo_quadro
                # Atualiza frame_index usando módulo para garantir que está dentro dos limites
                # O módulo garante que a animação fica em loop contínuo
                self.frame_index = (self.frame_index + passos) % len(quadros)
                # Garante que frame_index está válido após a atualização
                if self.frame_index < 0:
                    self.frame_index = 0
                elif self.frame_index >= len(quadros):
                    self.frame_index = len(quadros) - 1
        
        # SEMPRE atualiza a imagem e rect para garantir que está correto
        # Garante que frame_index está dentro dos limites válidos
        if len(quadros) > 0:
            # Garante que frame_index está dentro dos limites válidos [0, len(quadros)-1]
            if self.frame_index < 0:
                self.frame_index = 0
            elif self.frame_index >= len(quadros):
                self.frame_index = len(quadros) - 1
            frame_idx = self.frame_index
        else:
            frame_idx = 0
            self.frame_index = 0
        
        # Verifica se o índice é válido antes de acessar
        # IMPORTANTE: Garante que frame_idx está dentro dos limites válidos ANTES de acessar
        if len(quadros) == 0:
            # Se não há frames, usa fallback
            quadro = self._superficie_fallback(self.scale)
            self.frame_index = 0
        elif frame_idx < 0 or frame_idx >= len(quadros):
            # Se o índice for inválido, usa o primeiro frame como fallback
            frame_idx = 0
            self.frame_index = 0
            try:
                quadro_original = quadros[frame_idx]
                quadro = quadro_original.copy()
            except (IndexError, TypeError, AttributeError) as e:
                # Se ainda houver erro, usa fallback
                print(f"Erro ao acessar frame {frame_idx} de {len(quadros)} frames: {e}")
                quadro = self._superficie_fallback(self.scale)
                self.frame_index = 0
        else:
            # Pega o quadro e cria uma cópia para evitar problemas de referência
            # IMPORTANTE: Sempre pega o quadro original e cria uma nova cópia
            try:
                quadro_original = quadros[frame_idx]
                # Verifica se o quadro é válido
                if quadro_original is None:
                    raise ValueError("Quadro é None")
                quadro = quadro_original.copy()
            except (IndexError, TypeError, AttributeError, ValueError) as e:
                # Se houver erro ao acessar o frame, usa fallback
                print(f"Erro ao acessar frame {frame_idx} de {len(quadros)} frames na animação: {e}")
                if len(quadros) > 0:
                    try:
                        quadro_original = quadros[0]
                        quadro = quadro_original.copy()
                        self.frame_index = 0
                    except:
                        # Se até o primeiro frame falhar, usa fallback
                        quadro = self._superficie_fallback(self.scale)
                        self.frame_index = 0
                else:
                    # Se não há frames disponíveis, usa fallback
                    quadro = self._superficie_fallback(self.scale)
                    self.frame_index = 0
        
        # Aplica flip apenas uma vez se necessário
        direcao_atual = self.facing
        if direcao_atual == "left":
            quadro = pygame.transform.flip(quadro, True, False)
        
        # Atualiza image (garante que é uma nova referência)
        self.image = quadro
        
        # CRÍTICO: Cria um novo rect baseado na nova imagem
        # Mas SEMPRE usa as mesmas coordenadas para centerx e bottom
        # Isso garante que o sprite nunca se move durante QUALQUER animação (idle ou shot)
        # Como todos os frames foram normalizados para terem o mesmo tamanho,
        # a posição será sempre consistente, independente do frame atual.
        self.rect = self.image.get_rect()
        
        # SEMPRE define a posição exatamente da mesma forma, independente do frame ou animação
        # centerx sempre baseado em world_x (nunca muda durante animação)
        # bottom sempre preservado (nunca muda durante animação)
        # Isso funciona tanto para idle quanto para shot porque ambos foram normalizados
        self.rect.centerx = centro_x_tela
        self.rect.bottom = base_anterior
    
    def _atualizar_animacao_morte(self, delta_tempo, camera_x):
        """Atualiza a animação de morte do Careca"""
        if not self.dead_frames or len(self.dead_frames) == 0:
            self.kill()
            return
        
        # Calcula a posição na tela primeiro
        centro_x_tela = int(self.world_x - camera_x)
        
        # CRÍTICO: Preserva a posição Y ANTES de atualizar qualquer coisa
        # Isso garante que o inimigo morre na mesma posição onde estava
        # Usa a posição preservada quando take_damage foi chamado, ou a posição atual do rect
        if self._death_base_y is not None:
            # Usa a posição preservada quando a morte começou
            base_anterior = self._death_base_y
        elif hasattr(self, 'rect') and self.rect is not None:
            # Fallback: usa a posição atual do rect
            base_anterior = self.rect.bottom
        else:
            # Se não tem rect, usa uma posição padrão
            base_anterior = 550  # CHAO_Y padrão
        
        total_quadros = len(self.dead_frames)
        indice_ultimo_quadro = total_quadros - 1
        
        # Garante que frame_index está válido
        if self.frame_index < 0:
            self.frame_index = 0
        elif self.frame_index >= total_quadros:
            self.frame_index = indice_ultimo_quadro
        
        if self.frame_index == indice_ultimo_quadro:
            self.dead_timer += delta_tempo
            if self.dead_timer >= self.dead_last_frame_duration:
                self.kill()
                return
            quadro = self.dead_frames[indice_ultimo_quadro]
        else:
            self.animation_timer += delta_tempo
            tempo_quadro = self.animation_speed
            
            if self.animation_timer >= tempo_quadro:
                passos = int(self.animation_timer / tempo_quadro)
                self.animation_timer -= passos * tempo_quadro
                self.frame_index = min(self.frame_index + passos, indice_ultimo_quadro)
                quadro = self.dead_frames[self.frame_index]
            else:
                quadro = self.dead_frames[self.frame_index]
        
        # Cria uma cópia do quadro antes de aplicar flip
        quadro_copia = quadro.copy()
        if self.facing == "left":
            quadro_copia = pygame.transform.flip(quadro_copia, True, False)
        
        self.image = quadro_copia
        
        # CRÍTICO: Cria um novo rect baseado na nova imagem
        # Mas SEMPRE usa as mesmas coordenadas para centerx e bottom
        # Como os frames de morte foram normalizados, todos têm o mesmo tamanho
        # Isso garante que a posição não muda durante a animação de morte
        self.rect = self.image.get_rect()
        
        # SEMPRE define a posição exatamente da mesma forma
        # centerx sempre baseado em world_x (nunca muda)
        # bottom sempre preservado (nunca muda)
        # Isso garante que o inimigo morre na mesma posição onde estava
        self.rect.centerx = centro_x_tela
        self.rect.bottom = base_anterior


class ProjetilInimigo(pygame.sprite.Sprite):
    """Projétil disparado pelos inimigos"""
    def __init__(self, x, y, direcao_x, direcao_y, velocidade, escala=1.0):
        super().__init__()
        # Usa o mesmo sprite de projétil do protagonista
        try:
            imagem = pygame.image.load(bullet_path).convert_alpha()
        except Exception:
            # fallback simples se não conseguir carregar
            imagem = pygame.Surface((6, 2), pygame.SRCALPHA)
            imagem.fill((255, 200, 40))
        
        nova_largura = max(1, int(round(imagem.get_width() * escala)))
        nova_altura = max(1, int(round(imagem.get_height() * escala)))
        self.image = pygame.transform.scale(imagem, (nova_largura, nova_altura))
        
        
        self.rect = self.image.get_rect(center=(x, y))
        
        self.direction_x = direcao_x
        self.direction_y = direcao_y
        self.speed = velocidade
        
    def update(self, delta_tempo):
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
    posicao_y_spawn = player_y  # Mesma altura do player
    
    if lado == "esquerda":
        if x_offset > 0:
            posicao_x_spawn = camera_x - x_offset
        else:
            posicao_x_spawn = camera_x + abs(x_offset)
    else:
        if x_offset >= 0:
            posicao_x_spawn = camera_x + screen_width + x_offset
        else:
            posicao_x_spawn = camera_x + screen_width + x_offset
    
    # None = detecta automaticamente o número de frames
    # Scale 1.5 para tornar o Careca menor
    return Careca(posicao_x_spawn, posicao_y_spawn, scale=1.5, idle_count=None, shot_count=None)


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
        
        self.image = self.frames[self.frame_index] if self.frames else self._superficie_fallback()
        self.rect = self.image.get_rect(center=(x, y))
        
        # Área de colisão: apenas uma linha vertical estreita no centro (mesmo X)
        # Largura muito pequena (5% da largura) mas altura total
        largura_colisao = max(5, int(self.rect.width * 0.05))
        altura_colisao = self.rect.height
        self.collision_rect = pygame.Rect(0, 0, largura_colisao, altura_colisao)
        self.collision_rect.center = self.rect.center
        
        # Posição no mundo (para seguir a câmera)
        self.world_x = x
        self.world_y = y
        
        # Dano ao player
        self.damage_cooldown = 0.0
        self.damage_interval = 0.5  # Dano a cada 0.5 segundos
    
    def _superficie_fallback(self):
        superficie = pygame.Surface((32, 32), pygame.SRCALPHA)
        superficie.fill((255, 100, 0))
        return superficie
    
    def _load_fire_frames(self, escala):
        """Carrega os frames do efeito de fogo"""
        quadros = []
        for caminho in fire_frames_paths:
            try:
                imagem = pygame.image.load(caminho).convert_alpha()
                nova_largura = max(1, int(round(imagem.get_width() * escala)))
                nova_altura = max(1, int(round(imagem.get_height() * escala)))
                quadro = pygame.transform.scale(imagem, (nova_largura, nova_altura))
                quadros.append(quadro)
            except Exception:
                pass
        
        return quadros if quadros else [self._superficie_fallback()]
    
    def update(self, delta_tempo, camera_x):
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
            self.damage_cooldown -= delta_tempo
        
        # Atualiza animação (loop contínuo)
        self.animation_timer += delta_tempo
        if self.animation_timer >= self.animation_speed:
            self.animation_timer = 0.0
            self.frame_index = (self.frame_index + 1) % len(self.frames)
            
            # Atualiza frame
            centro_x_anterior = self.rect.centerx
            base_anterior = self.rect.bottom
            
            self.image = self.frames[self.frame_index]
            self.rect = self.image.get_rect()
            self.rect.centerx = centro_x_anterior
            self.rect.bottom = base_anterior
            
            # Atualiza o rect de colisão após mudar o frame
            # Largura muito pequena (5% da largura) mas altura total
            largura_colisao = max(5, int(self.rect.width * 0.05))
            altura_colisao = self.rect.height
            self.collision_rect.width = largura_colisao
            self.collision_rect.height = altura_colisao
            self.collision_rect.center = self.rect.center
    
    def is_fire_on(self):
        """Verifica se o fogo está aceso (não apagado) baseado no frame atual"""
        if not self.frames or len(self.frames) == 0:
            return False
        # Os primeiros 70% dos frames são considerados "acesos"
        # Os últimos 30% são considerados "apagados"
        limite = int(len(self.frames) * 0.7)
        return self.frame_index < limite
    
    def can_damage(self):
        """Verifica se pode causar dano (cooldown acabou E fogo está aceso)"""
        return self.damage_cooldown <= 0.0 and self.is_fire_on()
    
    def apply_damage(self):
        """Aplica dano e reseta cooldown"""
        self.damage_cooldown = self.damage_interval


class Plataforma(pygame.sprite.Sprite):
    """Plataforma cinza claro que aparece antes das colunas de fogo"""
    def __init__(self, x, y, largura=200, altura=20):
        super().__init__()
        self.width = largura
        self.height = altura
        
        # Cria uma superfície cinza claro
        self.image = pygame.Surface((largura, altura))
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
    def __init__(self, x, y, escala=1.0):
        super().__init__()
        
        # Tamanho fixo de 30x30 pixels
        tamanho_alvo = 30
        
        # Carrega a imagem do coração
        try:
            imagem = pygame.image.load(heart_path).convert_alpha()
            # Redimensiona para 30x30 pixels
            self.image = pygame.transform.scale(imagem, (tamanho_alvo, tamanho_alvo))
        except Exception:
            # Fallback: cria uma superfície vermelha simples
            self.image = pygame.Surface((tamanho_alvo, tamanho_alvo), pygame.SRCALPHA)
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
    
    def update(self, delta_tempo, camera_x):
        """Atualiza a posição do coração baseada na câmera e animação"""
        # Atualiza posição baseada na câmera
        self.rect.x = int(self.world_x - camera_x)
        
        # Animação de flutuação (mantém o bottom no chão)
        self.animation_timer += delta_tempo * self.animation_speed
        self.float_offset = math.sin(self.animation_timer) * 3  # Flutua 3 pixels para cima/baixo
        # Mantém o bottom no chão (world_y) e aplica a flutuação
        self.rect.bottom = int(self.world_y + self.float_offset)

