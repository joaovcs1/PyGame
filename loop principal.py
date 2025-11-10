import pygame
import random
import math
from Personagens import Protagonista
from plano_de_fundo import carregar_camadas, desenhar_parallax
from Inimigos import InimigoCyborg, spawn_inimigo_cyborg, Careca, spawn_careca, ProjetilInimigo, ColunaFogo, Plataforma, Coracao
from assets import heart_path

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
enemy_bullets = pygame.sprite.Group()  # Projéteis dos inimigos

# --- Obstáculos ---
fire_columns = pygame.sprite.Group()  # Colunas de fogo como obstáculos
platforms = pygame.sprite.Group()  # Plataformas antes das colunas de fogo

# --- Itens ---
hearts = pygame.sprite.Group()  # Corações que restauram vida

# Controle de spawn
spawn_timer = 0.0
spawn_interval = 4.0  # Spawna um inimigo a cada 4 segundos

# Controle de spawn de colunas de fogo
fire_spawn_timer = 0.0
fire_spawn_interval = 6.0  # Spawna uma coluna de fogo a cada 6 segundos

# Controle de spawn de corações
heart_spawn_timer = 0.0
heart_spawn_interval = 15.0  # Spawna um coração a cada 15 segundos
MAX_HEARTS_ON_SCREEN = 3  # Máximo de corações na tela simultaneamente

# --- Carrega imagens dos corações uma vez (otimização de performance) ---
_heart_img_cache = None
_heart_img_empty_cache = None
_heart_img_half_cache = None
_heart_size_cache = None

def _get_heart_images(heart_size=30):
    """Carrega e cacheia as imagens dos corações (só carrega uma vez)"""
    global _heart_img_cache, _heart_img_empty_cache, _heart_img_half_cache, _heart_size_cache
    
    # Se já carregou e o tamanho é o mesmo, reutiliza
    if _heart_img_cache is not None and _heart_size_cache == heart_size:
        return _heart_img_cache, _heart_img_empty_cache, _heart_img_half_cache
    
    # Carrega a imagem do coração uma vez
    try:
        heart_img = pygame.image.load(heart_path).convert_alpha()
        heart_img = pygame.transform.scale(heart_img, (heart_size, heart_size))
    except Exception:
        # Fallback: cria um coração simples
        heart_img = pygame.Surface((heart_size, heart_size), pygame.SRCALPHA)
        heart_img.fill((255, 0, 0))
    
    # Cria versão vazia (cinza) uma vez
    empty_heart = heart_img.copy()
    empty_heart.fill((100, 100, 100), special_flags=pygame.BLEND_RGBA_MULT)
    
    # Cria versão meio coração (transparente) uma vez
    half_heart = heart_img.copy()
    half_heart.set_alpha(128)
    
    # Cacheia
    _heart_img_cache = heart_img
    _heart_img_empty_cache = empty_heart
    _heart_img_half_cache = half_heart
    _heart_size_cache = heart_size
    
    return heart_img, empty_heart, half_heart

# --- Função para desenhar corações de vida ---
def desenhar_coracoes_vida(screen, player, x=20, y=20, heart_size=30):
    """Desenha corações de vida (5 corações, cada um vale 2 vidas)"""
    # Usa imagens em cache (não carrega a cada frame)
    heart_img, empty_heart, half_heart = _get_heart_images(heart_size)
    
    # Total de corações: 5 (cada um vale 2 vidas)
    total_hearts = 5
    hearts_per_row = 5
    spacing = 5  # Espaçamento entre corações
    
    # Calcula quantos corações cheios e meio corações
    health = player.health
    full_hearts = health // 2  # Corações completos (2 vidas cada)
    has_half_heart = (health % 2) == 1  # Meio coração se tiver 1 vida restante
    
    for i in range(total_hearts):
        # Calcula posição do coração
        row = i // hearts_per_row
        col = i % hearts_per_row
        heart_x = x + col * (heart_size + spacing)
        heart_y = y + row * (heart_size + spacing)
        
        if i < full_hearts:
            # Coração cheio
            screen.blit(heart_img, (heart_x, heart_y))
        elif i == full_hearts and has_half_heart:
            # Meio coração (usa versão em cache)
            screen.blit(half_heart, (heart_x, heart_y))
        else:
            # Coração vazio (usa a versão em cache)
            screen.blit(empty_heart, (heart_x, heart_y))

# --- Loop principal ---
rodando = True
while rodando:
    dt = clock.tick(FPS) / 1000.0  # segundos desde o último frame

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            rodando = False

    # definindo o pulo - só funciona se o player estiver vivo
        elif event.type == pygame.KEYDOWN:
            if not player.is_dying:
                if event.key == pygame.K_UP:
                    player.jump()
                elif event.key == pygame.K_SPACE:
                    proj = player.shoot()
                    if proj:
                        bullets.add(proj)

    #  Movimento horizontal - só funciona se o player estiver vivo
    # Bloqueia movimento se o personagem estiver atirando
    dx = 0
    if not player.is_dying:
        keys = pygame.key.get_pressed()
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

    # Mantém o personagem no centro
    player.rect.centerx = SCREEN_WIDTH // 2
    
    # Atualiza plataformas ANTES de verificar colisões (para ter rects atualizados)
    for platform in platforms:
        platform.update(camera_x)
    
    # Aplica gravidade ANTES de verificar colisões
    player.vel_y += player.gravidade
    player.rect.y += int(player.vel_y)
    
    # Verifica colisão com plataformas PRIMEIRO
    on_platform = False
    for platform in platforms:
        # Verifica se o player está horizontalmente sobre a plataforma
        player_centerx = player.rect.centerx
        platform_left = platform.rect.left
        platform_right = platform.rect.right
        
        if player_centerx >= platform_left and player_centerx <= platform_right:
            # Verifica se o player está verticalmente próximo do topo da plataforma
            player_bottom = player.rect.bottom
            platform_top = platform.rect.top
            
            # Se o bottom do player está entre o topo da plataforma (com tolerância)
            # Aumenta a tolerância superior para manter o player na plataforma
            if player_bottom >= platform_top - 10 and player_bottom <= platform_top + 25:
                # Se está caindo, parado, ou ligeiramente acima (mas ainda dentro da tolerância)
                if player.vel_y >= -2:  # Permite pequena velocidade para cima mas ainda considera em cima
                    # Coloca em cima da plataforma
                    player.rect.bottom = platform_top
                    if player.vel_y > 0:  # Só zera velocidade se estava caindo
                        player.vel_y = 0.0
                    on_platform = True
                    player.no_chao = True
                    player.can_double_jump = True
                    player.used_double = False
                    break
    
    # Se não está em plataforma, verifica chão
    if not on_platform:
        if player.rect.bottom >= CHAO_Y:
            player.rect.bottom = CHAO_Y
            player.vel_y = 0.0
            player.no_chao = True
            player.can_double_jump = True
            player.used_double = False
        else:
            player.no_chao = False
    
    # Agora atualiza a animação (já com no_chao correto)
    player.update(dt, moving=(dx != 0))
    
    # Posição do protagonista no mundo (para os inimigos)
    player_world_x = camera_x + player.rect.centerx
    player_world_y = player.rect.centery
    
    # Atualiza os projéteis do player primeiro
    bullets.update(dt)
    
    # Atualiza projéteis dos inimigos
    enemy_bullets.update(dt)
    
    # Atualiza colunas de fogo
    for fire_column in fire_columns:
        fire_column.update(dt, camera_x)
    
    # Atualiza corações
    for heart in hearts:
        heart.update(dt, camera_x)
    
    # --- Sistema de Inimigos ---
    # Atualiza inimigos PRIMEIRO para ter rects atualizados
    for enemy in enemies:
         # Aplica gravidade e verifica colisão com plataformas
        enemy.vel_y += enemy.gravidade
        enemy.rect.y += int(enemy.vel_y)
        
        # Verifica colisão com plataformas
        enemy_on_platform = False
        for platform in platforms:
            if enemy.rect.colliderect(platform.rect):
                # Verifica se o inimigo está em cima da plataforma
                enemy_bottom = enemy.rect.bottom
                platform_top = platform.world_y
                # Tolerância para detectar quando está em cima
                if enemy_bottom >= platform_top - 10 and enemy_bottom <= platform_top + 15:
                    # Se está caindo ou parado, coloca em cima da plataforma
                    if enemy.vel_y >= 0:
                        enemy.rect.bottom = platform_top
                        enemy.vel_y = 0.0
                        enemy_on_platform = True
                        enemy.no_chao = True
                        break
        
        # Se não está em plataforma, verifica chão
        if not enemy_on_platform:
            if enemy.rect.bottom >= CHAO_Y:
                enemy.rect.bottom = CHAO_Y
                enemy.vel_y = 0.0
                enemy.no_chao = True
            else:
                enemy.no_chao = False
        
        enemy.update(dt, camera_x, (player_world_x, player_world_y))
        
        # Cyborg soca quando perto - só causa dano se o player estiver vivo
        if isinstance(enemy, InimigoCyborg):
            if enemy.alive and not enemy.is_dying and enemy.punch_timer > 0:
                # O enemy.rect já foi atualizado no update() com centerx correto
                # Usa o rect diretamente para verificar colisão
                if enemy.rect.colliderect(player.rect) and not player.is_dying:
                    # Aplica dano ao player (com cooldown de invencibilidade)
                    if player.take_damage(1):
                        print(f"Player recebeu dano! Vida: {player.health}/{player.max_health}")
                        if player.is_dying:
                            print("Player morreu! Mostrando animação de morte...")
        
        # Careca atira quando detecta o player
        elif isinstance(enemy, Careca):
            if enemy.alive and not enemy.is_dying and not player.is_dying:
                if enemy.pode_atirar(player_world_x, player_world_y):
                    proj = enemy.shoot(player_world_x, player_world_y)
                    if proj:
                        enemy_bullets.add(proj)
    
    # --- Colisões de projéteis do player com inimigos ---
    # Verifica colisões DEPOIS de atualizar inimigos para ter rects corretos
    for bullet in list(bullets):
        # Verifica se a bala ainda existe (pode ter sido removida em iteração anterior)
        if bullet not in bullets:
            continue
            
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
                # Remove o projétil IMEDIATAMENTE para evitar que acerte outros inimigos
                bullet.kill()
                # Aplica dano apenas ao primeiro inimigo acertado
                hit_enemy.take_damage(3)  # Dano aumentado para 3
                break  # Para imediatamente após encontrar e processar colisão
    
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
    
    # Projéteis dos inimigos acertam o player
    player_hits = pygame.sprite.spritecollide(player, enemy_bullets, True)
    if player_hits and not player.is_dying:
        # Aplica dano ao player (o sistema de invencibilidade impede múltiplos danos)
        if player.take_damage(1):
            print(f"Player recebeu dano de projétil! Vida: {player.health}/{player.max_health}")
    
    # Colisão do player com corações
    heart_collisions = pygame.sprite.spritecollide(player, hearts, True)
    for heart in heart_collisions:
        if not player.is_dying:
            if player.heal(2):  # Restaura 2 de vida
                print(f"Player coletou coração! Vida: {player.health}/{player.max_health}")
    
    # Colisão do player com colunas de fogo (apenas se estiver no mesmo X)
    for fire_column in fire_columns:
        # Verifica se o player está no mesmo X (com pequena tolerância)
        player_centerx = player.rect.centerx
        fire_centerx = fire_column.rect.centerx
        x_distance = abs(player_centerx - fire_centerx)
        
        # Tolerância muito pequena: apenas 10 pixels de diferença em X
        if x_distance <= 10:
            # Verifica se está entre o chão (bottom da coluna) e uma altura específica acima
            fire_bottom = fire_column.rect.bottom
            fire_centery = fire_column.rect.centery
            altura_dano = fire_centery - 30  # Do chão até 30 pixels acima do centro
            
            # Player deve estar entre o chão e a altura máxima de dano
            # Verifica se qualquer parte do player está na área de dano (do chão até altura_dano)
            # O player está na área se seu bottom está acima do chão E seu top está abaixo da altura máxima
            if player.rect.bottom >= fire_bottom and player.rect.top <= altura_dano:
                if fire_column.can_damage() and not player.is_dying:
                    if player.take_damage(1):
                        fire_column.apply_damage()
                        print(f"Player recebeu dano de coluna de fogo! Vida: {player.health}/{player.max_health}")
    
    # Remove colunas de fogo que saíram da tela
    for fire_column in list(fire_columns):
        if fire_column.world_x < camera_x - SCREEN_WIDTH:
            fire_column.kill()
        elif fire_column.world_x > camera_x + SCREEN_WIDTH * 2:
            fire_column.kill()
    
    # Remove plataformas que saíram da tela
    for platform in list(platforms):
        if platform.world_x < camera_x - SCREEN_WIDTH:
            platform.kill()
        elif platform.world_x > camera_x + SCREEN_WIDTH * 2:
            platform.kill()
    
    # Spawn de novos inimigos (Cyborg ou Careca) - apenas se o player estiver vivo
    if player.is_alive() and not player.is_dying:
        spawn_timer += dt
        if spawn_timer >= spawn_interval:
            spawn_timer = 0.0
            # Alterna entre spawnar pela direita e esquerda
            lado = random.choice(["direita", "esquerda"])
            # Alterna aleatoriamente entre Cyborg e Careca
            tipo_inimigo = random.choice(["cyborg", "careca"])
            
            # Spawna apenas no chão (inimigos em plataformas são spawnados junto com a plataforma)
            spawn_y = CHAO_Y
            spawn_x = camera_x + SCREEN_WIDTH if lado == "direita" else camera_x - SCREEN_WIDTH
            spawn_on_platform = False
            chosen_platform = None
            
            if tipo_inimigo == "careca":
                novo_inimigo = spawn_careca(spawn_x, spawn_y, SCREEN_WIDTH, player.rect.centery, x_offset=0, lado=lado)
            else:
                novo_inimigo = spawn_inimigo_cyborg(spawn_x, spawn_y, SCREEN_WIDTH, player.rect.centery, x_offset=0, lado=lado)
            
            # Ajusta a posição Y do inimigo se estiver em uma plataforma
            if spawn_on_platform and chosen_platform:
                novo_inimigo.rect.bottom = chosen_platform.world_y
                novo_inimigo.world_x = spawn_x
            
            enemies.add(novo_inimigo)
    
    # Spawn de colunas de fogo - apenas se o player estiver vivo
    if player.is_alive() and not player.is_dying:
        fire_spawn_timer += dt
        if fire_spawn_timer >= fire_spawn_interval:
            fire_spawn_timer = 0.0
            # Spawna coluna de fogo à frente do player
            fire_x = camera_x + SCREEN_WIDTH + random.randint(200, 400)
            # A coluna será posicionada no chão (o rect.bottom será ajustado no update)
            fire_y = CHAO_Y
            fire_column = ColunaFogo(fire_x, fire_y, scale=3.0)  # Aumentado para 3.0
            # Ajusta o bottom da coluna para ficar no chão
            fire_column.rect.bottom = CHAO_Y
            fire_column.world_y = CHAO_Y
            fire_columns.add(fire_column)
            
            # Spawna plataforma antes da coluna de fogo
            platform_width = 200
            platform_height = 20
            platform_x = fire_x - platform_width - 50  # 50 pixels antes da coluna
            platform_y = CHAO_Y - 150  # 150 pixels acima do chão
            platform = Plataforma(platform_x, platform_y, platform_width, platform_height)
            platforms.add(platform)
            
            # Spawna inimigos na plataforma (sempre spawna pelo menos 1, 50% de chance de 2)
            chance_inimigo = random.random()
            num_inimigos = 1  # Sempre pelo menos 1 inimigo
            if chance_inimigo < 0.5:
                num_inimigos = 2  # 50% de chance de 2 inimigos
            
            for i in range(num_inimigos):
                # Posiciona inimigo na plataforma com variação
                enemy_x = platform_x + random.randint(20, platform_width - 20)
                enemy_y = platform_y  # Topo da plataforma
                
                # Escolhe tipo de inimigo aleatoriamente
                tipo_inimigo = random.choice(["cyborg", "careca"])
                if tipo_inimigo == "careca":
                    novo_inimigo = spawn_careca(enemy_x, enemy_y, SCREEN_WIDTH, player.rect.centery, x_offset=0, lado="direita")
                else:
                    novo_inimigo = spawn_inimigo_cyborg(enemy_x, enemy_y, SCREEN_WIDTH, player.rect.centery, x_offset=0, lado="direita")
                
                # Ajusta a posição Y para ficar no topo da plataforma
                novo_inimigo.rect.bottom = platform_y
                novo_inimigo.world_x = enemy_x
                enemies.add(novo_inimigo)
    
    # Spawn de corações - apenas se o player estiver vivo e não houver muitos corações na tela
    if player.is_alive() and not player.is_dying:
        heart_spawn_timer += dt
        if heart_spawn_timer >= heart_spawn_interval:
            # Só spawna se não houver muitos corações na tela
            if len(hearts) < MAX_HEARTS_ON_SCREEN:
                heart_spawn_timer = 0.0
                # Spawna coração mais longe do player (no chão) - à frente da tela visível
                heart_x = camera_x + random.randint(SCREEN_WIDTH + 200, SCREEN_WIDTH * 2)  # Spawna longe, à frente do player
                heart = Coracao(heart_x, CHAO_Y, scale=1.0)  # Tamanho fixo de 30x30 pixels
                # Ajusta o bottom do coração para ficar no chão
                heart.world_y = CHAO_Y
                # Atualiza a posição baseada na câmera (o update vai ajustar o rect)
                heart.update(0, camera_x)  # Atualiza uma vez para posicionar corretamente
                # Garante que o bottom está no chão (corrige qualquer problema de posicionamento)
                heart.rect.bottom = CHAO_Y
                hearts.add(heart)
            else:
                # Se já há muitos corações, reseta o timer mas não spawna
                heart_spawn_timer = 0.0
    
    # Remove corações que saíram da tela
    for heart in list(hearts):
        if heart.world_x < camera_x - SCREEN_WIDTH:  # Remove quando sair da tela à esquerda
            heart.kill()
        elif heart.world_x > camera_x + SCREEN_WIDTH * 2:  # Remove quando sair da tela à direita
            heart.kill()

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
    
    # Desenha protagonista (com efeito de piscar mais rápido quando sofre dano)
    if player.is_dying:
        # Quando morto, mostra a animação de morte sem piscar
        screen.blit(player.image, player.rect)
    elif player.invincibility_timer > 0:
        # Pisca o personagem rapidamente quando invencível (animação de dano mais rápida)
        # Multiplicador maior = piscar mais rápido (75 cria um efeito 1.5x mais rápido)
        visible = math.sin(player.invincibility_timer * 75) > 0
        if visible:
            screen.blit(player.image, player.rect)
    else:
        screen.blit(player.image, player.rect)
    
    # Desenha projéteis
    bullets.draw(screen)  # Projéteis do protagonista
    enemy_bullets.draw(screen)  # Projéteis dos inimigos
    
    # Desenha plataformas
    for platform in platforms:
        # Verifica se a plataforma está dentro da área visível da tela
        if -100 <= platform.rect.centerx <= SCREEN_WIDTH + 200:
            screen.blit(platform.image, platform.rect)
    
    # Desenha colunas de fogo
    for fire_column in fire_columns:
        # Verifica se a coluna está dentro da área visível da tela
        if -100 <= fire_column.rect.centerx <= SCREEN_WIDTH + 100:
            screen.blit(fire_column.image, fire_column.rect)
    
    # Desenha corações
    for heart in hearts:
        # Verifica se o coração está dentro da área visível da tela
        if -50 <= heart.rect.centerx <= SCREEN_WIDTH + 50:  # Margem de 50px
            screen.blit(heart.image, heart.rect)
    
    # Desenha corações de vida por último para ficar sempre visível
    desenhar_coracoes_vida(screen, player, x=20, y=20, heart_size=30)

    pygame.display.flip()
    screen.fill((0, 0, 0))

pygame.quit()
