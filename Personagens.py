# Personagens.py
import pygame
import os
from assets import*

class Protagonista(pygame.sprite.Sprite):
    """Jogador controlável: animação, pulo, vida e tiro."""
    def __init__(self, x, y, scale=1.5,
                 idle_count=6, run_count=10, jump_count=10, double_count=6):
        super().__init__()
        self.scale = float(scale) if scale >= 0.5 else 0.5

        self.idle_frames = self._carregar_quadros(idle_path, idle_count, self.scale)
        self.run_frames = self._carregar_quadros(run_path, run_count, self.scale)
        self.jump_frames = self._carregar_quadros(jump_path, jump_count, self.scale)
        self.double_frames = self._carregar_quadros(double_path, double_count, self.scale)
        # animação de tiro (4 frames por padrão)
        self.shot_frames = self._carregar_quadros(shot_path, 4, self.scale)
        # animação de morte
        self.death_frames = self._carregar_quadros(death_path, None, self.scale)

        # estado de animação
        self.current_frames = self.idle_frames if self.idle_frames else [self._superficie_fallback(self.scale)]
        self.frame_index = 0
        self.animation_timer = 0.0
        self.animation_speed = 0.12
        self.shot_timer = 0.0
        self.shot_duration = 0.20  # segundos

        self.image = self.current_frames[self.frame_index]
        self.rect = self.image.get_rect(center=(x, y))

        # movimento horizontal
        self.speed = 7  # Aumentado de 5 para 7 (40% mais rápido)
        self.facing = "right"
        
        # Posição no mundo (para movimento quando a câmera está bloqueada)
        self.world_x = float(x)  # Posição X no mundo (centro X)
        self.world_y = float(self.rect.bottom)  # Posição Y no mundo (bottom do personagem)

        # física vertical (AJUSTAR AQUI PARA CONTROLAR ALTURA DO PULO)

        self.vel_y = 0.0
        self.gravidade = 0.65  # Aumentado de 0.45 para 0.65 (aproximadamente 44% mais rápido)        
        self.jump_force = -15.0      # Aumentado mais para melhor alcance nas plataformas
        self.double_jump_force = -10.0  # Aumentado proporcionalmente
        self.no_chao = True
        self.can_double_jump = True
        self.used_double = False
        
        # Sistema de vida
        self.max_health = 10
        self.health = 10
        self.invincibility_timer = 0.0
        self.invincibility_duration = 0.5  # 0.5 segundos de invencibilidade após tomar dano
        
        # Estado de morte
        self.is_dying = False
        self.dead_timer = 0.0
        self.dead_last_frame_duration = 2.0  # 2 segundos no último frame


    def _superficie_fallback(self, escala=1):
        superficie = pygame.Surface((32*escala, 48*escala), pygame.SRCALPHA)
        superficie.fill((200,80,40))
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

    def _carregar_quadros(self, caminho, numero_quadros, escala):
        caminho = os.path.normpath(caminho)
        try:
            folha = pygame.image.load(caminho).convert_alpha()
        except Exception:
            return [self._superficie_fallback(escala)]

        largura_folha, altura_folha = folha.get_width(), folha.get_height()
        
        # Se numero_quadros é None, detecta automaticamente
        if numero_quadros is None or numero_quadros <= 0:
            numero_quadros, largura_quadro = self._detectar_numero_quadros(folha)
        else:
            largura_quadro = largura_folha // numero_quadros
        
        quadros = []
        for i in range(numero_quadros):
            rect = pygame.Rect(i * largura_quadro, 0, largura_quadro, altura_folha)
            try:
                quadro = folha.subsurface(rect).copy()
                # redimensiona usando escala fracionária
                nova_largura = max(1, int(round(quadro.get_width() * self.scale)))
                nova_altura = max(1, int(round(quadro.get_height() * self.scale)))
                quadro = pygame.transform.scale(quadro, (nova_largura, nova_altura))
                quadros.append(quadro)
            except Exception:
                quadros.append(self._superficie_fallback(escala))
        
        return quadros if quadros else [self._superficie_fallback(escala)]

    def move(self, delta_x):
        if delta_x == 0:
            return
        self.facing = "right" if delta_x > 0 else "left"
        self.rect.x += int(delta_x)

    def jump(self):
        # Não pode pular se estiver morrendo
        if self.is_dying:
            return
        
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

    def update(self, delta_tempo, moving=False):
        # Se está morrendo, atualiza animação de morte
        if self.is_dying:
            self._atualizar_animacao_morte(delta_tempo)
            return
        
        # Atualiza timer de invencibilidade
        if self.invincibility_timer > 0:
            self.invincibility_timer = max(0.0, self.invincibility_timer - delta_tempo)
        
        # escolhe frames por estado (prioridade: ar -> run -> idle)
        if self.shot_timer > 0:
            self.shot_timer = max(0.0, self.shot_timer - delta_tempo)
            quadros = self.shot_frames if self.shot_frames else self.idle_frames
            tempo_quadro = max(0.06, self.animation_speed * 0.8)
        elif not self.no_chao:
            quadros = self.double_frames if (self.used_double and self.double_frames) else self.jump_frames
            tempo_quadro = self.animation_speed
        else:
            quadros = self.run_frames if (moving and self.run_frames) else self.idle_frames
            tempo_quadro = self.animation_speed

        # animação por tempo
        self.animation_timer += delta_tempo
        if self.animation_timer >= tempo_quadro:
            passos = int(self.animation_timer / tempo_quadro)
            self.animation_timer -= passos * tempo_quadro
            self.frame_index = (self.frame_index + passos) % len(quadros)

            # preserva posição vertical (bottom) e centerx ao trocar frame
            centro_x_anterior = self.rect.centerx
            base_anterior = self.rect.bottom

            quadro = quadros[self.frame_index]
            if self.facing == "left":
                quadro = pygame.transform.flip(quadro, True, False)

            self.image = quadro
            self.rect = self.image.get_rect()
            self.rect.centerx = centro_x_anterior
            self.rect.bottom = base_anterior
    
    def _atualizar_animacao_morte(self, delta_tempo):
        """Atualiza a animação de morte do protagonista"""
        if not self.death_frames or len(self.death_frames) == 0:
            # Se não há animação de morte, usa idle
            quadros = self.idle_frames if self.idle_frames else [self._superficie_fallback(self.scale)]
            quadro = quadros[0] if quadros else self._superficie_fallback(self.scale)
            if self.facing == "left":
                quadro = pygame.transform.flip(quadro, True, False)
            self.image = quadro
            return
        
        total_quadros = len(self.death_frames)
        indice_ultimo_quadro = total_quadros - 1
        
        if self.frame_index == indice_ultimo_quadro:
            # Está no último frame, mantém por dead_last_frame_duration
            self.dead_timer += delta_tempo
            quadro = self.death_frames[indice_ultimo_quadro]
        else:
            # Avança para o próximo frame
            self.animation_timer += delta_tempo
            tempo_quadro = self.animation_speed
            
            if self.animation_timer >= tempo_quadro:
                passos = int(self.animation_timer / tempo_quadro)
                self.animation_timer -= passos * tempo_quadro
                self.frame_index = min(self.frame_index + passos, indice_ultimo_quadro)
                quadro = self.death_frames[self.frame_index]
            else:
                quadro = self.death_frames[self.frame_index]
        
        # Preserva posições antes de recriar o rect
        centro_x_anterior = self.rect.centerx
        base_anterior = self.rect.bottom
        
        if self.facing == "left":
            quadro = pygame.transform.flip(quadro, True, False)
        
        self.image = quadro
        self.rect = self.image.get_rect()
        self.rect.centerx = centro_x_anterior
        self.rect.bottom = base_anterior
    
    def take_damage(self, dano=1):
        """Recebe dano do inimigo. Retorna True se o dano foi aplicado."""
        if self.invincibility_timer > 0 or self.is_dying:
            return False  # Ainda está invencível ou já está morrendo
        
        self.health = max(0, self.health - dano)
        
        # Se a vida chegou a zero, inicia animação de morte
        if self.health <= 0:
            self.is_dying = True
            self.frame_index = 0
            self.animation_timer = 0.0
            self.dead_timer = 0.0
            self.invincibility_timer = 0.0  # Remove invencibilidade ao morrer
        else:
            self.invincibility_timer = self.invincibility_duration
        
        return True
    
    def is_alive(self):
        """Verifica se o personagem está vivo"""
        return self.health > 0
    
    def get_health_percentage(self):
        """Retorna a porcentagem de vida (0.0 a 1.0)"""
        return max(0.0, float(self.health) / float(self.max_health))
    
    def heal(self, quantidade=1):
        """Restaura vida do player"""
        if self.is_dying:
            return False  # Não pode curar se está morrendo
        
        vida_anterior = self.health
        self.health = min(self.max_health, self.health + quantidade)
        return self.health > vida_anterior  # Retorna True se curou
 
    def shoot(self):
        """Dispara um projétil e aciona a animação de tiro. Retorna o sprite do projétil."""
        # Não pode atirar se estiver morrendo
        if self.is_dying:
            return None
        
        self.shot_timer = self.shot_duration

        # ponto de origem do cano da arma (ajustado para ficar na ponta da arma)
        imagem = self.image
        # Ajusta a posição X para ficar mais na ponta da arma (aproximadamente 1/3 da largura do sprite)
        offset_x_arma = imagem.get_width() // 3
        if self.facing == "right":
            posicao_x_cano = self.rect.centerx + offset_x_arma
        else:
            posicao_x_cano = self.rect.centerx - offset_x_arma
        # altura do projétil: abaixo do centro Y do personagem (onde a arma normalmente está)
        # Adiciona offset positivo para descer a bala alguns pixels
        offset_y_arma = int(imagem.get_height() * 0.22)  # 22% da altura do sprite para baixo
        posicao_y_cano = self.rect.centery + offset_y_arma
        direcao = 1 if self.facing == "right" else -1
        velocidade = 28  # Aumentada de 20 para 28 (40% mais rápido)
        return Projetil(posicao_x_cano, posicao_y_cano, direcao, velocidade, self.scale)


class Projetil(pygame.sprite.Sprite):
    def __init__(self, x, y, direcao, velocidade, escala=1.0):
        super().__init__()
        try:
            imagem = pygame.image.load(bullet_path).convert_alpha()
        except Exception:
            # fallback simples
            imagem = pygame.Surface((6, 2), pygame.SRCALPHA)
            imagem.fill((255, 200, 40))

        nova_largura = max(1, int(round(imagem.get_width() * escala)))
        nova_altura = max(1, int(round(imagem.get_height() * escala)))
        self.image = pygame.transform.scale(imagem, (nova_largura, nova_altura))
        self.rect = self.image.get_rect(center=(x, y))
        self.direction = 1 if direcao >= 0 else -1
        self.speed = velocidade

    def update(self, delta_tempo):
        self.rect.x += int(self.direction * self.speed)
