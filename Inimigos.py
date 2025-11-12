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
        self.speed = 5.0  # Aumentado de 3.575 para 5.0 (aproximadamente 40% mais rápido)
        self.facing = "left"  # Inimigos começam olhando para esquerda por padrão
        
        # Física vertical
        self.vel_y = 0.0
        self.gravidade = 0.65  # Aumentado de 0.45 para 0.65 (aproximadamente 44% mais rápido)
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


def spawn_inimigo_cyborg(camera_x, chao_y, screen_width, player_y, x_offset=0, lado="direita", escala_global=1.0):
    """
    Spawna um Cyborg em uma posição relativa à câmera
    
    Args:
        camera_x: Posição atual da câmera
        chao_y: Altura do chão
        screen_width: Largura da tela
        player_y: Altura Y do player (para spawnar na mesma altura)
        x_offset: Offset em relação à câmera (0 = próximo à câmera, positivo = mais à frente/atrás)
        lado: "direita" para spawnar à direita, "esquerda" para spawnar à esquerda
        escala_global: Fator de escala global para ajustar o tamanho (padrão 1.0)
    
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
    # Scale 3.2 * escala_global para tornar o Cyborg maior proporcionalmente
    scale_cyborg = 3.2 * escala_global
    return InimigoCyborg(posicao_x_spawn, posicao_y_spawn, scale=scale_cyborg, idle_count=None, run_count=None, punch_count=None)


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
        self.gravidade = 0.65  # Aumentado de 0.45 para 0.65 (aproximadamente 44% mais rápido)
        self.no_chao = True
        
        # Sistema de tiro (atirador de longe)
        # Variação aleatória inicial no cooldown para evitar sincronização
        self.shoot_cooldown = random.uniform(0.0, 1.2)  # Cooldown inicial aleatório entre 0 e 1.2 segundos
        self.shoot_interval = 1.2  # Atira a cada 1.2 segundos
        self.detection_range = 800  # Detecta o player de longe
        self.shoot_range = 700  # Alcance de tiro máximo (muito longe)
        self.shoot_range_min = 300  # Alcance de tiro mínimo (só atira se estiver a pelo menos esta distância)
        
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
        return (distancia >= self.shoot_range_min and  # Distância mínima (não atira muito perto)
                distancia <= self.shoot_range and      # Distância máxima
                self.shoot_cooldown <= 0.0 and 
                self.shot_timer <= 0.0)
    
    def shoot(self, alvo_x, alvo_y, camera_x=0):
        """Dispara um projétil horizontal direcionado ao alvo"""
        if not self.alive or not self.pode_atirar(alvo_x, alvo_y):
            return None
        
        self.shot_timer = self.shot_duration
        self.shoot_cooldown = self.shoot_interval
        
        # CRÍTICO: Reseta a animação para sincronizar o projétil com a animação de ataque
        # Isso garante que o projétil saia no momento correto da animação
        self.frame_index = 0
        self.animation_timer = 0.0
        
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
        
        # CRÍTICO: Calcula a posição do cano em coordenadas do MUNDO (não da tela)
        # A arma está próxima ao centro horizontal do sprite, com um pequeno offset na direção do tiro
        # Offset horizontal da arma em relação ao centro do sprite (em pixels do mundo)
        offset_x_arma = 15 * self.scale  # Offset horizontal da arma em relação ao centro
        
        # Calcula world_x do cano baseado no world_x do inimigo
        if self.facing == "right":
            # Arma está ligeiramente à direita do centro
            world_x_cano = self.world_x + offset_x_arma
        else:
            # Arma está ligeiramente à esquerda do centro
            world_x_cano = self.world_x - offset_x_arma
        
        # Ajusta a posição Y para a altura da arma
        # A arma está próxima ao centro vertical, mas ligeiramente abaixo do centro
        # Usa rect.centery e ajusta ligeiramente para baixo (offset positivo pequeno)
        offset_y_arma = int(self.rect.height * 0.05)  # 5% da altura para baixo (arma está ligeiramente abaixo do centro)
        pos_y_cano_tela = self.rect.centery + offset_y_arma
        
        # Converte para coordenada Y do mundo
        # Como a câmera não se move em Y, a coordenada Y da tela é a mesma do mundo
        world_y_cano = float(pos_y_cano_tela)
        
        velocidade = 11  # Aumentado de 8 para 11 (aproximadamente 40% mais rápido)
        return ProjetilInimigo(world_x_cano, world_y_cano, direcao_x, direcao_y, velocidade, self.scale, camera_x)
    
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
            # Se não tem rect ainda (primeira vez), usa uma posição padrão calculada dinamicamente
            # O rect foi criado no __init__ com center=(x, y), então o bottom está definido
            # Calcula CHAO_Y dinamicamente baseado na altura da tela (~91.67% da altura)
            try:
                screen = pygame.display.get_surface()
                if screen:
                    screen_height = screen.get_height()
                    chao_y_dinamico = int(screen_height * 0.9167)
                else:
                    chao_y_dinamico = 550  # Fallback se não conseguir obter a tela
            except:
                chao_y_dinamico = 550  # Fallback em caso de erro
            base_anterior = self.rect.bottom if hasattr(self, 'rect') else chao_y_dinamico
        
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
            # Se não tem rect, usa uma posição padrão calculada dinamicamente
            # Calcula CHAO_Y dinamicamente baseado na altura da tela (~91.67% da altura)
            try:
                screen = pygame.display.get_surface()
                if screen:
                    screen_height = screen.get_height()
                    chao_y_dinamico = int(screen_height * 0.9167)
                else:
                    chao_y_dinamico = 550  # Fallback se não conseguir obter a tela
            except:
                chao_y_dinamico = 550  # Fallback em caso de erro
            base_anterior = chao_y_dinamico
        
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
    def __init__(self, world_x, world_y, direcao_x, direcao_y, velocidade, escala=1.0, camera_x=0):
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
        
        # CRÍTICO: Coordenadas do mundo (não da tela)
        self.world_x = float(world_x)  # Posição X no mundo
        self.world_y = float(world_y)  # Posição Y no mundo (fixa, projétil horizontal)
        
        # CRÍTICO: Cria um rect de colisão que corresponde exatamente ao tamanho visual da bala
        # A área de colisão deve ser exatamente do tamanho da imagem, sem se estender abaixo
        largura_imagem = self.image.get_width()
        altura_imagem = self.image.get_height()
        
        # O rect de colisão deve ter o tamanho exato da imagem
        # Isso garante que a área de dano seja exatamente do tamanho visual da bala
        self.rect = pygame.Rect(0, 0, largura_imagem, altura_imagem)
        
        # Rect para renderização (mesmo tamanho da imagem)
        self.render_rect = pygame.Rect(0, 0, largura_imagem, altura_imagem)
        
        # Posiciona ambos os rects na tela baseado nas coordenadas do mundo
        # IMPORTANTE: world_y representa o centro Y do cano, então centralizamos o rect nesse ponto
        # Isso garante que a área de colisão seja exatamente do tamanho da bala, sem se estender abaixo
        pos_x_tela = int(self.world_x - camera_x)
        pos_y_tela = int(self.world_y)
        self.rect.centerx = pos_x_tela
        self.rect.centery = pos_y_tela  # Centraliza verticalmente no ponto de disparo
        self.render_rect.centerx = pos_x_tela
        self.render_rect.centery = pos_y_tela
        
        self.direction_x = direcao_x
        self.direction_y = direcao_y
        self.speed = velocidade
        self.escala = escala
        
    def update(self, delta_tempo, camera_x=0):
        """Atualiza a posição do projétil no mundo e na tela"""
        # Move no mundo (não na tela)
        self.world_x += self.direction_x * self.speed
        
        # CRÍTICO: Atualiza a posição na tela baseada na câmera
        # Atualiza rect de colisão (tamanho exato da imagem, sem se estender abaixo)
        pos_x_tela = int(self.world_x - camera_x)
        pos_y_tela = int(self.world_y)
        self.rect.centerx = pos_x_tela
        self.rect.centery = pos_y_tela  # Centraliza verticalmente, área de colisão exata da bala
        
        # Atualiza rect de renderização (para desenhar a imagem completa)
        self.render_rect.centerx = pos_x_tela
        self.render_rect.centery = pos_y_tela
        
        # Remove projéteis que saem da tela
        # Usa world_x para verificar se saiu do mundo visível
        # Calcula limites da tela dinamicamente
        try:
            screen = pygame.display.get_surface()
            if screen:
                screen_height = screen.get_height()
                screen_width = screen.get_width()
                limite_superior_tela = screen_height + 100  # Margem de 100px abaixo da tela
            else:
                limite_superior_tela = 700  # Fallback
                screen_width = 1000
        except:
            limite_superior_tela = 700  # Fallback
            screen_width = 1000
        
        if (self.world_x < camera_x - 200 or self.world_x > camera_x + screen_width + 200 or
            self.rect.bottom < -100 or self.rect.top > limite_superior_tela):
            self.kill()


def spawn_careca(camera_x, chao_y, screen_width, player_y, x_offset=0, lado="direita", escala_global=1.0):
    """
    Spawna um Careca em uma posição relativa à câmera
    
    Args:
        camera_x: Posição atual da câmera
        chao_y: Altura do chão
        screen_width: Largura da tela
        player_y: Altura Y do player (para spawnar na mesma altura)
        x_offset: Offset em relação à câmera (0 = próximo à câmera, positivo = mais à frente/atrás)
        lado: "direita" para spawnar à direita, "esquerda" para spawnar à esquerda
        escala_global: Fator de escala global para ajustar o tamanho (padrão 1.0)
    
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
    # Scale 1.5 * escala_global para tornar o Careca proporcional
    scale_careca = 1.5 * escala_global
    return Careca(posicao_x_spawn, posicao_y_spawn, scale=scale_careca, idle_count=None, shot_count=None)


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
    """Plataforma preta com brilho vermelho que aparece antes das colunas de fogo"""
    def __init__(self, x, y, largura=200, altura=20, plataformas_grupo=None):
        super().__init__()
        self.width = largura
        self.height = altura
        self.plataformas_grupo = plataformas_grupo  # Referência ao grupo de plataformas para verificar duplas
        
        # Cria uma superfície maior para incluir o brilho vermelho
        espessura_brilho = 3  # Espessura do brilho em pixels
        largura_com_brilho = largura + (espessura_brilho * 2)
        altura_com_brilho = altura + (espessura_brilho * 2)
        
        self.image = pygame.Surface((largura_com_brilho, altura_com_brilho), pygame.SRCALPHA)
        
        # Verifica se há plataformas próximas (duplas) para não desenhar brilho lateral entre elas
        tem_plataforma_esquerda = False
        tem_plataforma_direita = False
        
        if self.plataformas_grupo:
            distancia_maxima = 50  # Distância máxima para considerar plataformas como "duplas"
            for outra_plataforma in self.plataformas_grupo:
                if outra_plataforma == self:
                    continue
                # Verifica se está na mesma altura Y (com tolerância)
                if abs(outra_plataforma.world_y - y) < 10:
                    # Verifica se está à esquerda
                    if outra_plataforma.world_x < x and abs(outra_plataforma.world_x + outra_plataforma.width - x) < distancia_maxima:
                        tem_plataforma_esquerda = True
                    # Verifica se está à direita
                    elif outra_plataforma.world_x > x and abs(outra_plataforma.world_x - (x + largura)) < distancia_maxima:
                        tem_plataforma_direita = True
        
        # Desenha o brilho vermelho ao redor (outline)
        # Desenha várias camadas para criar um efeito de brilho
        cor_vermelho_brilho = (255, 0, 0)  # Vermelho puro
        cor_vermelho_escuro = (200, 0, 0)  # Vermelho mais escuro para profundidade
        
        # Camada externa (mais escura) - apenas onde não há plataforma adjacente
        if not tem_plataforma_esquerda:
            pygame.draw.rect(self.image, cor_vermelho_escuro, 
                            (0, 0, espessura_brilho, altura_com_brilho))  # Lado esquerdo
        if not tem_plataforma_direita:
            pygame.draw.rect(self.image, cor_vermelho_escuro, 
                            (largura_com_brilho - espessura_brilho, 0, espessura_brilho, altura_com_brilho))  # Lado direito
        # Topo e fundo sempre têm brilho
        pygame.draw.rect(self.image, cor_vermelho_escuro, 
                        (0, 0, largura_com_brilho, espessura_brilho))  # Topo
        pygame.draw.rect(self.image, cor_vermelho_escuro, 
                        (0, altura_com_brilho - espessura_brilho, largura_com_brilho, espessura_brilho))  # Fundo
        
        # Camada interna (mais brilhante) - apenas onde não há plataforma adjacente
        if not tem_plataforma_esquerda:
            pygame.draw.rect(self.image, cor_vermelho_brilho,
                            (espessura_brilho // 2, espessura_brilho // 2,
                             espessura_brilho, altura_com_brilho - espessura_brilho))  # Lado esquerdo
        if not tem_plataforma_direita:
            pygame.draw.rect(self.image, cor_vermelho_brilho,
                            (largura_com_brilho - espessura_brilho - (espessura_brilho // 2), espessura_brilho // 2,
                             espessura_brilho, altura_com_brilho - espessura_brilho))  # Lado direito
        # Topo e fundo sempre têm brilho
        pygame.draw.rect(self.image, cor_vermelho_brilho,
                        (espessura_brilho // 2, espessura_brilho // 2,
                         largura_com_brilho - espessura_brilho, espessura_brilho))  # Topo
        pygame.draw.rect(self.image, cor_vermelho_brilho,
                        (espessura_brilho // 2, altura_com_brilho - espessura_brilho - (espessura_brilho // 2),
                         largura_com_brilho - espessura_brilho, espessura_brilho))  # Fundo
        
        # Desenha a plataforma preta no centro
        pygame.draw.rect(self.image, (0, 0, 0),  # Preto
                        (espessura_brilho, espessura_brilho, largura, altura))
        
        self.rect = self.image.get_rect()
        self.rect.x = x - espessura_brilho  # Ajusta posição para compensar o brilho
        self.rect.y = y - espessura_brilho
        
        # Posição no mundo (para seguir a câmera)
        self.world_x = x
        self.world_y = y
        self.espessura_brilho = espessura_brilho
    
    def update(self, camera_x):
        """Atualiza a posição da plataforma baseada na câmera"""
        self.rect.x = int(self.world_x - camera_x) - self.espessura_brilho
        self.rect.y = int(self.world_y) - self.espessura_brilho


class Coracao(pygame.sprite.Sprite):
    """Coração que restaura vida do player"""
    def __init__(self, x, y, escala=1.0):
        super().__init__()
        
        # Tamanho base de 30x30 pixels, multiplicado pela escala
        tamanho_alvo = int(30 * escala)
        
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


class InimigoFinal(pygame.sprite.Sprite):
    """Inimigo Final (Boss) - aparece quando o jogador mata 150 inimigos"""
    def __init__(self, x, y, scale=4.0, idle_count=None):
        super().__init__()
        self.scale = float(scale) if scale >= 0.5 else 0.5
        
        # Carrega animações do Inimigo Final
        # Idle.png tem 6 frames (largura 128)
        if idle_count is None:
            idle_count = 6  # Idle.png tem exatamente 6 frames
        self.idle_frames = self._load_frames(homeless3_idle, idle_count, self.scale, frame_width_hint=128)
        
        # Run.png tem 8 frames (largura 128)
        self.run_frames = self._load_frames(homeless3_run, 8, self.scale, frame_width_hint=128)
        
        # Attack_1.png tem 5 frames (largura 128)
        self.attack_frames = self._load_frames(homeless3_attack1, 5, self.scale, frame_width_hint=128)
        
        # Special.png tem 13 frames (largura 128)
        self.special_frames = self._load_frames(homeless3_special, 13, self.scale, frame_width_hint=128)
        
        # Dead.png (animação de morte)
        self.dead_frames = self._load_frames(homeless3_dead, None, self.scale)
        
        # Validação: garante que os frames foram carregados corretamente
        if len(self.idle_frames) == 0:
            print(f"AVISO: Nenhum frame idle foi carregado para InimigoFinal!")
            self.idle_frames = [self._superficie_fallback(self.scale)]
        if len(self.run_frames) == 0:
            self.run_frames = self.idle_frames.copy()
        if len(self.attack_frames) == 0:
            self.attack_frames = self.idle_frames.copy()
        if len(self.special_frames) == 0:
            self.special_frames = self.idle_frames.copy()
        
        # CRÍTICO: Normaliza TODAS as animações com as MESMAS dimensões máximas
        todas_animacoes = []
        if self.idle_frames:
            todas_animacoes.extend(self.idle_frames)
        if self.run_frames:
            todas_animacoes.extend(self.run_frames)
        if self.attack_frames:
            todas_animacoes.extend(self.attack_frames)
        if self.special_frames:
            todas_animacoes.extend(self.special_frames)
        if self.dead_frames:
            todas_animacoes.extend(self.dead_frames)
        
        if todas_animacoes:
            largura_max = max(img.get_width() for img in todas_animacoes)
            altura_max = max(img.get_height() for img in todas_animacoes)
            
            # Redimensiona todas as animações para o mesmo tamanho
            def normalizar_quadros(quadros):
                normalizados = []
                for quadro in quadros:
                    novo_quadro = pygame.Surface((largura_max, altura_max), pygame.SRCALPHA)
                    centro_x = (largura_max - quadro.get_width()) // 2
                    centro_y = (altura_max - quadro.get_height()) // 2
                    novo_quadro.blit(quadro, (centro_x, centro_y))
                    normalizados.append(novo_quadro)
                return normalizados
            
            self.idle_frames = normalizar_quadros(self.idle_frames)
            self.run_frames = normalizar_quadros(self.run_frames)
            self.attack_frames = normalizar_quadros(self.attack_frames)
            if self.special_frames:
                self.special_frames = normalizar_quadros(self.special_frames)
            if self.dead_frames:
                self.dead_frames = normalizar_quadros(self.dead_frames)
        
        # Estado de animação
        self.current_frames = self.idle_frames if self.idle_frames else [self._superficie_fallback(self.scale)]
        self.frame_index = 0
        self.animation_timer = 0.0
        self.animation_speed = 0.12
        self.punch_timer = 0.0  # Timer para animação de soco
        self.punch_duration = 0.5  # Duração do soco (5 frames a 0.1s cada = 0.5s)
        
        # Estado especial (40% de vida)
        self.special_executado = False  # Flag para garantir que executa apenas uma vez
        self.is_special = False  # Flag para indicar que está executando a animação special
        self.special_timer = 0.0  # Timer para controlar a animação special
        self.special_duration = 0.0  # Duração total da animação special (será calculada)
        
        # Movimento e direção
        # Velocidade reduzida em 20% e depois mais 10%: 7.0 * 0.8 * 0.9 = 5.04 (base), será aumentada em 5% após special
        self.base_speed = 5.0  # Velocidade reduzida (menor que o Shelby)
        self.speed = 5.0  # Velocidade reduzida (menor que o Shelby)
        self.facing = "left"  # Inimigos começam olhando para esquerda por padrão
        
        # Estado de morte
        self.is_dying = False
        self.dead_timer = 0.0
        self.dead_last_frame_duration = 2.0  # 2 segundos no último frame
        self._was_dying = False  # Flag para detectar quando acabou de morrer
        self.death_animation_finished = False  # Flag para indicar quando a animação de morte terminou
        
        # Sistema de soco (similar ao Cyborg)
        self.punch_cooldown = random.uniform(0.0, 1.5)  # Cooldown inicial aleatório
        self.punch_interval = 1.5  # Intervalo entre socos
        self.punch_range = 80.0  # Alcance do soco (em pixels do mundo)
        self.detection_range = 1000  # Detecta o player de longe
        
        # Inicializa a imagem corretamente com flip se necessário
        quadro_inicial = self.idle_frames[0] if self.idle_frames else self._superficie_fallback(self.scale)
        quadro_inicial = quadro_inicial.copy()
        if self.facing == "left":
            quadro_inicial = pygame.transform.flip(quadro_inicial, True, False)
        self.image = quadro_inicial
        self.rect = self.image.get_rect(center=(x, y))
        
        # Física vertical
        self.vel_y = 0.0
        self.gravidade = 0.65  # Aumentado de 0.45 para 0.65 (aproximadamente 44% mais rápido)
        self.no_chao = True
        
        # Saúde (boss tem 20x mais vida que o personagem)
        # Personagem tem 10 de vida, então boss tem 200 (dobrado)
        self.health = 200
        self.max_health = 200
        self.alive = True
        self.health_threshold_special = 0.40  # 40% de vida para ativar special
        self.previous_health = 200  # Para detectar quando a vida muda
        
        # Posição no mundo
        self.world_x = float(x)
        self.world_y = float(y)
    
    def _superficie_fallback(self, escala=1):
        superficie = pygame.Surface((32*escala, 48*escala), pygame.SRCALPHA)
        superficie.fill((255, 0, 255))  # Magenta para destacar
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
            if largura_folha % numero_quadros == 0:
                largura_quadro = largura_folha // numero_quadros
            else:
                largura_quadro = largura_folha // numero_quadros
        
        quadros = []
        for i in range(numero_quadros):
            x_inicio = i * largura_quadro
            if i == numero_quadros - 1:
                largura_atual = largura_folha - x_inicio
            else:
                largura_atual = largura_quadro
            
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
    
    def take_damage(self, dano=1):
        """Inflige dano ao Inimigo Final"""
        if self.is_dying or not self.alive:
            return
        
        # Salva a vida anterior para detectar mudança
        self.previous_health = self.health
        self.health -= dano
        
        # Verifica se chegou a 40% de vida e ainda não executou a animação special
        health_percentage = float(self.health) / float(self.max_health)
        previous_health_percentage = float(self.previous_health) / float(self.max_health)
        
        # Se a vida caiu de acima de 40% para abaixo ou igual a 40%, ativa a animação special
        if (previous_health_percentage > self.health_threshold_special and 
            health_percentage <= self.health_threshold_special and 
            not self.special_executado):
            # Ativa a animação special
            self.is_special = True
            self.special_executado = True
            self.special_timer = 0.0
            self.frame_index = 0
            self.animation_timer = 0.0
            # Calcula a duração da animação special (13 frames * 0.12 segundos por frame)
            if self.special_frames:
                self.special_duration = len(self.special_frames) * 0.12
            else:
                self.special_duration = 1.5  # Duração padrão se não houver frames
            print(f"Inimigo Final ativou modo especial! Vida: {self.health}/{self.max_health} ({health_percentage*100:.1f}%)")
        
        if self.health <= 0:
            self.is_dying = True
            self.alive = False
            self.frame_index = 0
            self.animation_timer = 0.0
            self.dead_timer = 0.0
            self._was_dying = False
            self.death_animation_finished = False  # Reseta flag quando começa a morrer
    
    def calcular_distancia(self, alvo_x, alvo_y):
        """Calcula a distância até o alvo"""
        delta_x = alvo_x - self.world_x
        delta_y = alvo_y - self.world_y
        return math.sqrt(delta_x * delta_x + delta_y * delta_y)
    
    def atualizar_direcao(self, alvo_mundo_x, camera_x=0):
        """Atualiza a direção visual do Inimigo Final"""
        alvo_tela_x = alvo_mundo_x - camera_x
        centro_x_tela_inimigo = int(self.world_x - camera_x)

        if alvo_tela_x > centro_x_tela_inimigo:
            self.facing = "right"
        elif alvo_tela_x < centro_x_tela_inimigo:
            self.facing = "left"
    
    def pode_socar(self, alvo_x, alvo_y):
        """Verifica se o Inimigo Final pode socar o alvo"""
        # Não pode socar durante a animação special
        if self.is_special:
            return False
        distancia = self.calcular_distancia(alvo_x, alvo_y)
        return (distancia <= self.punch_range and 
                self.punch_cooldown <= 0.0 and 
                self.punch_timer <= 0.0)
    
    def socar(self, alvo_x, alvo_y):
        """Executa um soco no alvo (ataque corpo-a-corpo, similar ao Cyborg)"""
        if not self.alive or not self.pode_socar(alvo_x, alvo_y):
            return False
        
        self.punch_timer = self.punch_duration
        self.punch_cooldown = self.punch_interval
        # Reseta a animação de ataque para o primeiro frame
        self.frame_index = 0
        self.animation_timer = 0.0
        return True
    
    def update(self, delta_tempo, camera_x, protagonista_pos=None):
        """Atualiza o Inimigo Final"""
        # Se está morrendo, mostra animação de morte
        if self.is_dying:
            if self.dead_frames and len(self.dead_frames) > 0:
                # Atualiza animação de morte
                self.dead_timer += delta_tempo
                tempo_por_frame = 0.1  # Velocidade da animação de morte
                if self.dead_timer >= tempo_por_frame:
                    self.dead_timer = 0.0
                    self.frame_index += 1
                    if self.frame_index >= len(self.dead_frames):
                        # Último frame: mantém por mais tempo
                        self.frame_index = len(self.dead_frames) - 1
                        if not self._was_dying:
                            self._was_dying = True
                            self.dead_timer = 0.0
                        elif self.dead_timer >= self.dead_last_frame_duration:
                            # Marca que a animação de morte terminou antes de remover o sprite
                            self.death_animation_finished = True
                            self.kill()
                            return
                
                # Atualiza frame de morte
                quadro = self.dead_frames[min(self.frame_index, len(self.dead_frames) - 1)].copy()
                if self.facing == "left":
                    quadro = pygame.transform.flip(quadro, True, False)
                self.image = quadro
                
                # Calcula a posição na tela
                centro_x_tela = int(self.world_x - camera_x)
                self.rect = self.image.get_rect()
                self.rect.centerx = centro_x_tela
                self.rect.bottom = int(self.world_y)
            else:
                # Sem animação de morte, marca como terminada e remove
                self.death_animation_finished = True
                self.kill()
            return
        
        if not self.alive:
            return
        
        # Se está executando a animação special, executa apenas ela
        if self.is_special:
            self.special_timer += delta_tempo
            
            # Verifica se a animação terminou
            if self.special_timer >= self.special_duration:
                # Animação special terminou - aumenta estatísticas
                # Aumenta velocidade em 5%
                self.speed = self.base_speed  # Mantém a mesma velocidade (7.0, igual ao Shelby)
                # Desativa modo special
                self.is_special = False
                self.frame_index = 0
                self.animation_timer = 0.0
                print(f"Inimigo Final aumentou poder! Velocidade: {self.speed:.2f}")
                # Continua para o comportamento normal após a animação
            else:
                # Atualiza animação special
                velocidade_animacao_special = 0.12  # Velocidade da animação special
                self.animation_timer += delta_tempo
                if self.animation_timer >= velocidade_animacao_special:
                    self.animation_timer = 0.0
                    self.frame_index += 1
                    if self.frame_index >= len(self.special_frames):
                        # Mantém no último frame até a duração total terminar
                        self.frame_index = len(self.special_frames) - 1
                
                # Mostra frame atual da animação special
                quadro = self.special_frames[min(self.frame_index, len(self.special_frames) - 1)].copy()
                if self.facing == "left":
                    quadro = pygame.transform.flip(quadro, True, False)
                self.image = quadro
                
                # Calcula a posição na tela
                centro_x_tela = int(self.world_x - camera_x)
                self.rect = self.image.get_rect()
                self.rect.centerx = centro_x_tela
                self.rect.bottom = int(self.world_y)
                
                # Durante a animação special, não move nem ataca
                return
        
        # Atualiza cooldowns
        if self.punch_cooldown > 0:
            self.punch_cooldown -= delta_tempo
        if self.punch_timer > 0:
            self.punch_timer -= delta_tempo
        
        # Comportamento: persegue o jogador e soca quando dentro do alcance (igual ao Cyborg)
        movendo = False
        if protagonista_pos:
            alvo_x, alvo_y = protagonista_pos
            distancia = self.calcular_distancia(alvo_x, alvo_y)
            
            # Sempre atualiza a direção para olhar para o protagonista
            self.atualizar_direcao(alvo_x, camera_x)
            
            # Se está socando, não se move
            if self.punch_timer > 0:
                movendo = False
            # Persegue o player quando detecta
            elif distancia <= self.detection_range:
                # Verifica se está na mesma posição X do player (em cima do player)
                distancia_x = abs(alvo_x - self.world_x)
                esta_acima_jogador = distancia_x <= 30  # Tolerância de 30 pixels
                
                # Se está em cima do player, anda para a direita
                if esta_acima_jogador:
                    movendo = True
                    self.world_x += self.speed
                elif distancia > self.punch_range:
                    # Persegue o player
                    movendo = True
                    if alvo_x < self.world_x:
                        self.world_x -= self.speed
                    else:
                        self.world_x += self.speed
                elif self.pode_socar(alvo_x, alvo_y):
                    # Está perto o suficiente, soca (e para de se mover)
                    self.socar(alvo_x, alvo_y)
                    movendo = False
        
        # Determina o estado da animação baseado no comportamento
        if self.punch_timer > 0:
            estado_atual = "attack"
        elif movendo:
            estado_atual = "run"
        else:
            estado_atual = "idle"
        
        # Seleciona animação baseada no estado (prioriza ataque se está socando)
        if self.punch_timer > 0 and self.attack_frames:
            # Está socando - usa animação de ataque
            quadros = self.attack_frames
            velocidade_animacao = 0.1  # Animação de ataque (5 frames a 0.1s cada = 0.5s total)
        elif estado_atual == "run" and self.run_frames:
            quadros = self.run_frames
            velocidade_animacao = 0.1  # Animação de corrida mais rápida
        elif estado_atual == "attack" and self.attack_frames:
            quadros = self.attack_frames
            velocidade_animacao = 0.1  # Animação de ataque
        else:
            quadros = self.idle_frames
            velocidade_animacao = self.animation_speed
        
        # Atualiza animação
        self.animation_timer += delta_tempo
        if self.animation_timer >= velocidade_animacao:
            self.animation_timer = 0.0
            # Se está socando, avança frame mas não loopa (mostra os 5 frames)
            if self.punch_timer > 0:
                if self.frame_index < len(quadros) - 1:
                    self.frame_index += 1
                else:
                    # Mantém no último frame enquanto está socando
                    self.frame_index = len(quadros) - 1
            else:
                # Outras animações fazem loop
                self.frame_index = (self.frame_index + 1) % len(quadros)
        
        # Atualiza frame
        quadro = quadros[self.frame_index].copy()
        if self.facing == "left":
            quadro = pygame.transform.flip(quadro, True, False)
        
        self.image = quadro
        
        # CRÍTICO: Atualiza a posição na tela baseada em world_x e world_y
        # Isso garante que o movimento horizontal seja visível
        # Calcula a posição na tela ANTES de recriar o rect
        centro_x_tela = int(self.world_x - camera_x)
        bottom_y = int(self.world_y)
        
        # Recria o rect com a nova imagem e atualiza a posição
        self.rect = self.image.get_rect()
        self.rect.centerx = centro_x_tela
        self.rect.bottom = bottom_y

