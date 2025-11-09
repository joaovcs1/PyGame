import pygame
import random
from Personagens import Protagonista
from plano_de_fundo import carregar_camadas, desenhar_parallax
from Inimigos import InimigoCyborg, spawn_inimigo_cyborg

pygame.init()

# --- Configurações da tela ---
SCREEN_WIDTH, SCREEN_HEIGHT = 800, 600
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Personagem centralizado com pulo (sem chão)")
clock = pygame.time.Clock()
FPS = 60

# --- Fundo ---
camadas_fundo = carregar_camadas(SCREEN_HEIGHT)
camera_x = 0.0

# --- Altura do chão visual (personagem pisa sobre o cenário) ---
CHAO_Y = 550   

# --- Player ---
player = Protagonista(SCREEN_WIDTH // 2, SCREEN_HEIGHT - 150, scale=1.5,
                      idle_count=6, run_count=10, jump_count=10, double_count=10)

player_group = pygame.sprite.Group(player)
bullets = pygame.sprite.Group()  # Projéteis do protagonista

# --- Inimigos ---
enemies = pygame.sprite.Group()

# Controle de spawn
spawn_timer = 0.0
spawn_interval = 4.0  # Spawna um inimigo a cada 4 segundos

# --- Loop principal ---
rodando = True
while rodando:
    dt = clock.tick(FPS) / 1000.0  # segundos desde o último frame

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            rodando = False

    # definindo o pulo
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_UP:
                player.jump()
            elif event.key == pygame.K_SPACE:
                proj = player.shoot()
                if proj:
                    bullets.add(proj)

    #  Movimento horizontal
    # Bloqueia movimento se o personagem estiver atirando
    keys = pygame.key.get_pressed()
    dx = 0
    # Só permite movimento se não estiver atirando
    if player.shot_timer <= 0:
        if keys[pygame.K_LEFT]:
            dx = -player.speed
        if keys[pygame.K_RIGHT]:
            dx = player.speed
        if keys[pygame.K_RIGHT] and keys[pygame.K_LEFT]:
            dx=0
    #Atualiza câmera e direção 
    if dx != 0:
        camera_x += dx
        player.facing = "right" if dx > 0 else "left"

    #Gravidade e animação
    player.aplicar_gravidade(CHAO_Y)
    player.update(dt, moving=(dx != 0))

    # Mantém o personagem no centro
    player.rect.centerx = SCREEN_WIDTH // 2
    
    # Posição do protagonista no mundo (para os inimigos)
    player_world_x = camera_x + player.rect.centerx
    player_world_y = player.rect.centery
    
    # Atualiza os projéteis do player primeiro
    bullets.update(dt)
    
    # --- Sistema de Inimigos ---
    # Atualiza inimigos PRIMEIRO para ter rects atualizados
    for enemy in enemies:
        # Aplica gravidade mesmo quando morrendo (para cair naturalmente)
        enemy.aplicar_gravidade(CHAO_Y)
        enemy.update(dt, camera_x, (player_world_x, player_world_y))
        
        # Cyborg soca quando perto
        if enemy.alive and not enemy.is_dying and enemy.punch_timer > 0:
            # O enemy.rect já foi atualizado no update() com centerx correto
            # Usa o rect diretamente para verificar colisão
            if enemy.rect.colliderect(player.rect):
                # Aqui você pode adicionar sistema de dano ao player
                # Por exemplo: player.take_damage(1)
                pass
    
    # --- Colisões de projéteis do player com inimigos ---
    # Verifica colisões DEPOIS de atualizar inimigos para ter rects corretos
    for bullet in list(bullets):
        hit_enemy = None
        
        for enemy in list(enemies):
            # Verifica se o inimigo está válido (vivo e não morrendo)
            if not enemy.alive or enemy.is_dying:
                continue

            # Usa o rect do inimigo que já foi atualizado no update()
            # O enemy.rect.x já está correto (world_x - camera_x)
            # Verifica colisão diretamente com o rect atualizado
            if bullet.rect.colliderect(enemy.rect):
                hit_enemy = enemy
                break  # Para imediatamente após encontrar colisão
        
        # Se encontrou colisão, remove o projétil IMEDIATAMENTE e aplica dano
        # Isso garante que cada projétil acerta apenas um inimigo
        if hit_enemy:
            bullet.kill()  # Remove o projétil primeiro
            hit_enemy.take_damage(1)  # Depois aplica dano apenas ao inimigo acertado
    
    # Remove inimigos que saíram muito atrás ou à frente da câmera
    # (mas não remove os que estão morrendo, para mostrar a animação)
    for enemy in list(enemies):
        if not enemy.is_dying:  # Só remove se não estiver morrendo
            # Remove se saiu muito atrás da câmera
            if enemy.world_x < camera_x - SCREEN_WIDTH:
                enemy.kill()
            # Remove se saiu muito à frente da câmera
            elif enemy.world_x > camera_x + SCREEN_WIDTH * 2:
                enemy.kill()
    
    # Spawn de novos inimigos (apenas Cyborg)
    spawn_timer += dt
    if spawn_timer >= spawn_interval:
        spawn_timer = 0.0
        # Alterna entre spawnar pela direita e esquerda
        lado = random.choice(["direita", "esquerda"])
        novo_inimigo = spawn_inimigo_cyborg(camera_x, CHAO_Y, SCREEN_WIDTH, player.rect.centery, x_offset=SCREEN_WIDTH, lado=lado)
        enemies.add(novo_inimigo)

    #Desenha fundo e personagem
    desenhar_parallax(screen, camadas_fundo, camera_x, SCREEN_WIDTH)
    
    # Desenha inimigos (incluindo os que estão morrendo)
    for enemy in enemies:
        # O enemy.rect já foi atualizado no update() com centerx correto
        # Verifica se o inimigo está dentro da área visível da tela usando centerx
        enemy_screen_centerx = enemy.rect.centerx
        
        # Verifica se o inimigo está dentro da área visível da tela
        if -100 <= enemy_screen_centerx <= SCREEN_WIDTH + 100:  # Margem de 100px
            # Usa o rect diretamente que já está correto (centerx já foi atualizado)
            screen.blit(enemy.image, enemy.rect)
    
    # Desenha protagonista
    screen.blit(player.image, player.rect)
    
    # Desenha projéteis
    bullets.draw(screen)  # Projéteis do protagonista

    pygame.display.flip()
    screen.fill((0, 0, 0))

pygame.quit()
