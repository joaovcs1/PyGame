import pygame
import random
import math
import os
from Personagens import Protagonista
from plano_de_fundo import carregar_camadas, desenhar_parallax
from Inimigos import InimigoCyborg, spawn_inimigo_cyborg, Careca, spawn_careca, ProjetilInimigo, ColunaFogo, Plataforma, Coracao
from assets import heart_path

pygame.init()
pygame.mixer.init()  # Inicializa o mixer de áudio

# --- Configurações da tela ---
LARGURA_TELA, ALTURA_TELA = 800, 600
tela = pygame.display.set_mode((LARGURA_TELA, ALTURA_TELA))
pygame.display.set_caption("THOMAS VELOZES & SHELBYS FURIOSOS")
relogio = pygame.time.Clock()
FPS = 60

# --- Carrega arquivos de áudio ---
# Música de fundo
caminho_musica_fundo = os.path.normpath("assets/Musicas/cyberpunk-street.mp3")
# Sons de tiro
caminho_som_tiro_careca = os.path.normpath("assets/Musicas/Som Tiro Careca.mp3")
caminho_som_tiro_shelby = os.path.normpath("assets/Musicas/Som Tiro Shelby.mp3")

# Carrega os sons
# Música de fundo (usa pygame.mixer.music, não precisa de variável)
try:
    pygame.mixer.music.load(caminho_musica_fundo)
    musica_fundo_carregada = True
except Exception as e:
    print(f"Erro ao carregar música de fundo: {e}")
    musica_fundo_carregada = False

# Sons de efeito (usam pygame.mixer.Sound)
try:
    som_tiro_careca = pygame.mixer.Sound(caminho_som_tiro_careca)
except Exception as e:
    print(f"Erro ao carregar som de tiro do Careca: {e}")
    som_tiro_careca = None

try:
    som_tiro_shelby = pygame.mixer.Sound(caminho_som_tiro_shelby)
except Exception as e:
    print(f"Erro ao carregar som de tiro do Shelby: {e}")
    som_tiro_shelby = None

# --- Tela de Introdução ---
def mostrar_tela_introducao():
    """Mostra a tela de introdução por 5 segundos"""
    # Caminho da imagem de introdução
    caminho_intro = os.path.normpath("assets/Imagens/Intro/Capa.png")
    
    # Tenta carregar a imagem
    try:
        imagem_intro = pygame.image.load(caminho_intro).convert()
        # Mantém o tamanho original da imagem e centraliza
        largura_img, altura_img = imagem_intro.get_size()
        x_intro = (LARGURA_TELA - largura_img) // 2
        y_intro = (ALTURA_TELA - altura_img) // 2
    except Exception:
        # Se não encontrar a imagem, cria uma tela preta simples
        imagem_intro = pygame.Surface((LARGURA_TELA, ALTURA_TELA))
        imagem_intro.fill((0, 0, 0))
        x_intro = 0
        y_intro = 0
        largura_img = LARGURA_TELA
        altura_img = ALTURA_TELA
    
    # Timer para a tela de introdução
    tempo_intro = 0.0
    duracao_intro = 5.0  # 5 segundos
    
    intro_rodando = True
    while intro_rodando:
        delta_tempo = relogio.tick(FPS) / 1000.0
        
        # Processa eventos
        for evento in pygame.event.get():
            if evento.type == pygame.QUIT:
                return False  # Fecha o jogo
            elif evento.type == pygame.KEYDOWN or evento.type == pygame.MOUSEBUTTONDOWN:
                # Permite pular a introdução pressionando qualquer tecla ou clicando
                intro_rodando = False
        
        # Atualiza timer
        tempo_intro += delta_tempo
        if tempo_intro >= duracao_intro:
            intro_rodando = False
        
        # Desenha a imagem de introdução
        tela.fill((0, 0, 0))  # Fundo preto (barras pretas nas laterais)
        # Desenha a imagem centralizada (as áreas não cobertas pela imagem ficam pretas)
        tela.blit(imagem_intro, (x_intro, y_intro))
        pygame.display.flip()
    
    return True  # Continua para o jogo

# --- Função para obter fonte arcade ---
def obter_fonte_arcade(tamanho):
    """Obtém uma fonte arcade pixelizada (monospace)"""
    try:
        # Tenta usar uma fonte monospace que tem estilo arcade
        # pygame.font.match_font tenta encontrar uma fonte monospace no sistema
        fonte_monospace = pygame.font.match_font('courier') or pygame.font.match_font('monospace')
        if fonte_monospace:
            return pygame.font.Font(fonte_monospace, tamanho)
        else:
            # Fallback para fonte padrão
            return pygame.font.Font(None, tamanho)
    except:
        # Fallback para fonte padrão
        return pygame.font.Font(None, tamanho)

# --- Variáveis globais para nome e contador ---
nome_usuario = ""
inimigos_mortos = 0
historico_jogadores = []  # Lista de dicionários: [{"nome": str, "mortes": int}, ...]

# --- Função para obter nome do usuário ---
def obter_nome_usuario():
    """Mostra pop-up para o usuário digitar seu nome"""
    global nome_usuario
    
    # Caminho da imagem de introdução (para mostrar de fundo)
    caminho_intro = os.path.normpath("assets/Imagens/Intro/Capa.png")
    try:
        imagem_fundo = pygame.image.load(caminho_intro).convert()
        # Mantém o tamanho original da imagem e centraliza
        largura_img, altura_img = imagem_fundo.get_size()
        x_fundo = (LARGURA_TELA - largura_img) // 2
        y_fundo = (ALTURA_TELA - altura_img) // 2
    except Exception:
        imagem_fundo = pygame.Surface((LARGURA_TELA, ALTURA_TELA))
        imagem_fundo.fill((0, 0, 0))
        x_fundo = 0
        y_fundo = 0
        largura_img = LARGURA_TELA
        altura_img = ALTURA_TELA
    
    nome_digitado = ""
    digitando = True
    
    while digitando:
        delta_tempo = relogio.tick(FPS) / 1000.0
        
        for evento in pygame.event.get():
            if evento.type == pygame.QUIT:
                return False  # Fecha o jogo
            elif evento.type == pygame.KEYDOWN:
                if evento.key == pygame.K_RETURN or evento.key == pygame.K_KP_ENTER:
                    # Enter pressionado - inicia o jogo
                    nome_usuario = nome_digitado if nome_digitado else "Jogador"
                    digitando = False
                elif evento.key == pygame.K_BACKSPACE:
                    # Remove último caractere
                    nome_digitado = nome_digitado[:-1]
                else:
                    # Adiciona caractere (limita a 20 caracteres)
                    if len(nome_digitado) < 20 and evento.unicode.isprintable():
                        nome_digitado += evento.unicode
        
        # Desenha fundo
        tela.fill((0, 0, 0))  # Fundo preto (barras pretas nas laterais)
        # Desenha a imagem centralizada (as áreas não cobertas pela imagem ficam pretas)
        tela.blit(imagem_fundo, (x_fundo, y_fundo))
        
        # Desenha pop-up (igual ao pop-up de game over)
        popup_largura = 400
        popup_altura = 300
        popup_x = (LARGURA_TELA - popup_largura) // 2
        popup_y = (ALTURA_TELA - popup_altura) // 2
        espessura_borda = 4
        
        # Desenha borda cinza
        popup_borda = pygame.Surface((popup_largura, popup_altura))
        popup_borda.fill((128, 128, 128))
        tela.blit(popup_borda, (popup_x, popup_y))
        
        # Desenha preenchimento preto
        popup_interno = pygame.Surface((popup_largura - espessura_borda * 2, popup_altura - espessura_borda * 2))
        popup_interno.fill((0, 0, 0))
        tela.blit(popup_interno, (popup_x + espessura_borda, popup_y + espessura_borda))
        
        # Desenha "Nome de Usuário:"
        fonte_titulo = obter_fonte_arcade(24)
        texto_titulo = fonte_titulo.render("Nome de Usuário:", False, (255, 255, 255))
        rect_titulo = texto_titulo.get_rect(center=(LARGURA_TELA // 2, popup_y + 80))
        tela.blit(texto_titulo, rect_titulo)
        
        # Desenha campo de texto (nome digitado)
        fonte_nome = obter_fonte_arcade(20)
        texto_nome = fonte_nome.render(nome_digitado if nome_digitado else "_", False, (255, 255, 255))
        rect_nome = texto_nome.get_rect(center=(LARGURA_TELA // 2, popup_y + 130))
        tela.blit(texto_nome, rect_nome)
        
        # Desenha "Pressione (ENTER) para Iniciar"
        fonte_instrucao = obter_fonte_arcade(18)
        texto_instrucao = fonte_instrucao.render("Pressione (ENTER) para Iniciar", False, (255, 255, 255))
        rect_instrucao = texto_instrucao.get_rect(center=(LARGURA_TELA // 2, popup_y + popup_altura - 50))
        tela.blit(texto_instrucao, rect_instrucao)
        
        pygame.display.flip()
    
    return True  # Continua para o jogo

# Mostra a tela de introdução
if not mostrar_tela_introducao():
    pygame.quit()
    exit()

# Mostra pop-up de nome de usuário
if not obter_nome_usuario():
    pygame.quit()
    exit()

# --- Inicia música de fundo (após pressionar ENTER) ---
if musica_fundo_carregada:
    try:
        pygame.mixer.music.play(-1)  # -1 = loop infinito
    except Exception as e:
        print(f"Erro ao tocar música de fundo: {e}")

# --- Fundo ---
camadas_fundo = carregar_camadas(ALTURA_TELA)
camera_x = 0.0

# --- Altura do chão visual (personagem pisa sobre o cenário) ---
CHAO_Y = 550   

# --- Jogador ---
jogador = Protagonista(LARGURA_TELA // 2, ALTURA_TELA - 150, scale=1.5,
                      idle_count=6, run_count=10, jump_count=10, double_count=10)

grupo_jogador = pygame.sprite.Group(jogador)
projeteis = pygame.sprite.Group()  # Projéteis do protagonista

# --- Inimigos ---
inimigos = pygame.sprite.Group()
projeteis_inimigos = pygame.sprite.Group()  # Projéteis dos inimigos

# --- Obstáculos ---
colunas_fogo = pygame.sprite.Group()  # Colunas de fogo como obstáculos
plataformas = pygame.sprite.Group()  # Plataformas antes das colunas de fogo

# --- Itens ---
coracoes = pygame.sprite.Group()  # Corações que restauram vida

# Controle de spawn
temporizador_spawn = 0.0
intervalo_spawn = 4.0  # Spawna um inimigo a cada 4 segundos

# Controle de spawn de colunas de fogo
temporizador_spawn_fogo = 0.0
intervalo_spawn_fogo = 6.0  # Spawna uma coluna de fogo a cada 6 segundos

# Controle de spawn de corações
temporizador_spawn_coracao = 0.0
intervalo_spawn_coracao = 15.0  # Spawna um coração a cada 15 segundos
MAX_CORACOES_NA_TELA = 3  # Máximo de corações na tela simultaneamente

# --- Carrega imagens dos corações uma vez (otimização de performance) ---
_cache_imagem_coracao = None
_cache_imagem_coracao_vazia = None
_cache_imagem_meio_coracao = None
_cache_tamanho_coracao = None

def _obter_imagens_coracao(tamanho_coracao=30):
    """Carrega e cacheia as imagens dos corações (só carrega uma vez)"""
    global _cache_imagem_coracao, _cache_imagem_coracao_vazia, _cache_imagem_meio_coracao, _cache_tamanho_coracao
    
    # Se já carregou e o tamanho é o mesmo, reutiliza
    if _cache_imagem_coracao is not None and _cache_tamanho_coracao == tamanho_coracao:
        return _cache_imagem_coracao, _cache_imagem_coracao_vazia, _cache_imagem_meio_coracao
    
    # Carrega a imagem do coração uma vez
    try:
        imagem_coracao = pygame.image.load(heart_path).convert_alpha()
        imagem_coracao = pygame.transform.scale(imagem_coracao, (tamanho_coracao, tamanho_coracao))
    except Exception:
        # Fallback: cria um coração simples
        imagem_coracao = pygame.Surface((tamanho_coracao, tamanho_coracao), pygame.SRCALPHA)
        imagem_coracao.fill((255, 0, 0))
    
    # Cria versão vazia (cinza) uma vez
    coracao_vazio = imagem_coracao.copy()
    coracao_vazio.fill((100, 100, 100), special_flags=pygame.BLEND_RGBA_MULT)
    
    # Cria versão meio coração (transparente) uma vez
    meio_coracao = imagem_coracao.copy()
    meio_coracao.set_alpha(128)
    
    # Cacheia
    _cache_imagem_coracao = imagem_coracao
    _cache_imagem_coracao_vazia = coracao_vazio
    _cache_imagem_meio_coracao = meio_coracao
    _cache_tamanho_coracao = tamanho_coracao
    
    return imagem_coracao, coracao_vazio, meio_coracao

# --- Função para desenhar corações de vida ---
def desenhar_coracoes_vida(tela, jogador, x=20, y=20, tamanho_coracao=30):
    """Desenha corações de vida (5 corações, cada um vale 2 vidas)"""
    # Usa imagens em cache (não carrega a cada frame)
    imagem_coracao, coracao_vazio, meio_coracao = _obter_imagens_coracao(tamanho_coracao)
    
    # Total de corações: 5 (cada um vale 2 vidas)
    total_coracoes = 5
    coracoes_por_linha = 5
    espacamento = 5  # Espaçamento entre corações
    
    # Calcula quantos corações cheios e meio corações
    vida = jogador.health
    coracoes_cheios = vida // 2  # Corações completos (2 vidas cada)
    tem_meio_coracao = (vida % 2) == 1  # Meio coração se tiver 1 vida restante
    
    for i in range(total_coracoes):
        # Calcula posição do coração
        linha = i // coracoes_por_linha
        coluna = i % coracoes_por_linha
        x_coracao = x + coluna * (tamanho_coracao + espacamento)
        y_coracao = y + linha * (tamanho_coracao + espacamento)
        
        if i < coracoes_cheios:
            # Coração cheio
            tela.blit(imagem_coracao, (x_coracao, y_coracao))
        elif i == coracoes_cheios and tem_meio_coracao:
            # Meio coração (usa versão em cache)
            tela.blit(meio_coracao, (x_coracao, y_coracao))
        else:
            # Coração vazio (usa a versão em cache)
            tela.blit(coracao_vazio, (x_coracao, y_coracao))

# --- Função para salvar jogador atual no histórico ---
def salvar_jogador_atual():
    """Salva o jogador atual no histórico antes de resetar"""
    global nome_usuario, inimigos_mortos, historico_jogadores
    
    # Só salva se tiver um nome (mesmo que não tenha mortes)
    if nome_usuario:
        # Verifica se o último jogador salvo já é o mesmo (evita duplicatas)
        if len(historico_jogadores) > 0:
            ultimo = historico_jogadores[-1]
            if ultimo["nome"] == nome_usuario and ultimo["mortes"] == inimigos_mortos:
                # Já foi salvo, não salva novamente
                return
        
        historico_jogadores.append({
            "nome": nome_usuario,
            "mortes": inimigos_mortos
        })
        # NÃO limita mais - mantém TODOS os jogadores para poder mostrar os top 5

# --- Função para reiniciar o jogo ---
def reiniciar_jogo():
    """Reinicia todas as variáveis do jogo para o estado inicial"""
    global camera_x, jogador, grupo_jogador, projeteis, inimigos, projeteis_inimigos
    global colunas_fogo, plataformas, coracoes
    global temporizador_spawn, temporizador_spawn_fogo, temporizador_spawn_coracao
    global inimigos_mortos
    
    # NÃO salva aqui porque já foi salvo quando o jogador morreu ou quando pressionou R
    # A função salvar_jogador_atual() já foi chamada antes de reiniciar_jogo()
    
    # Reseta câmera
    camera_x = 0.0
    
    # Recria o jogador
    jogador = Protagonista(LARGURA_TELA // 2, ALTURA_TELA - 150, scale=1.5,
                          idle_count=6, run_count=10, jump_count=10, double_count=10)
    grupo_jogador = pygame.sprite.Group(jogador)
    
    # Limpa todos os grupos
    projeteis.empty()
    inimigos.empty()
    projeteis_inimigos.empty()
    colunas_fogo.empty()
    plataformas.empty()
    coracoes.empty()
    
    # Reseta temporizadores
    temporizador_spawn = 0.0
    temporizador_spawn_fogo = 0.0
    temporizador_spawn_coracao = 0.0
    
    # Reseta contador de mortes
    inimigos_mortos = 0

# --- Estado de Game Over ---
game_over = False
game_over_timer = 0.0
mostrando_popup = False
jogador_morreu_nao_detectado = True  # Flag para detectar quando o jogador morre pela primeira vez

# --- Loop principal ---
rodando = True
while rodando:
    delta_tempo = relogio.tick(FPS) / 1000.0  # segundos desde o último frame

    for evento in pygame.event.get():
        if evento.type == pygame.QUIT:
            rodando = False
        elif evento.type == pygame.KEYDOWN:
            # Detecta tecla R para reiniciar quando estiver no pop-up
            if mostrando_popup and evento.key == pygame.K_r:
                # NÃO salva aqui porque já foi salvo quando o jogador morreu
                # A função salvar_jogador_atual() já foi chamada quando detectou a morte
                
                # Para a música de fundo antes de reiniciar (se ainda estiver tocando)
                if musica_fundo_carregada:
                    try:
                        pygame.mixer.music.stop()
                    except Exception as e:
                        print(f"Erro ao parar música de fundo: {e}")
                
                # Volta ao início: mostra tela de introdução e pop-up de nome
                if not mostrar_tela_introducao():
                    rodando = False
                    continue
                
                if not obter_nome_usuario():
                    rodando = False
                    continue
                
                # Reinicia o jogo e toca música de fundo novamente
                reiniciar_jogo()
                if musica_fundo_carregada:
                    try:
                        pygame.mixer.music.play(-1)  # -1 = loop infinito
                    except Exception as e:
                        print(f"Erro ao tocar música de fundo: {e}")
                game_over = False
                game_over_timer = 0.0
                mostrando_popup = False
                jogador_morreu_nao_detectado = True
            # definindo o pulo e tiro - só funciona se o jogador estiver vivo
            elif not jogador.is_dying and not game_over:
                if evento.key == pygame.K_UP:
                    jogador.jump()
                elif evento.key == pygame.K_SPACE:
                    projetil = jogador.shoot()
                    if projetil:
                        projeteis.add(projetil)
                        # Toca som de tiro do Shelby
                        if som_tiro_shelby is not None:
                            try:
                                som_tiro_shelby.play()
                            except Exception as e:
                                print(f"Erro ao tocar som de tiro do Shelby: {e}")

    # --- Detecção de morte do jogador ---
    if jogador.is_dying and jogador_morreu_nao_detectado:
        # Jogador acabou de morrer - salva no histórico e inicia game over
        salvar_jogador_atual()
        # Para a música de fundo quando o jogador morre
        if musica_fundo_carregada:
            try:
                pygame.mixer.music.stop()
            except Exception as e:
                print(f"Erro ao parar música de fundo: {e}")
        game_over = True
        game_over_timer = 0.0
        mostrando_popup = False
        jogador_morreu_nao_detectado = False
    
    # --- Atualização do timer de game over ---
    if game_over:
        game_over_timer += delta_tempo
        # Após 3 segundos, mostra o pop-up
        if game_over_timer >= 3.0:
            mostrando_popup = True
    
    #  Movimento horizontal - só funciona se o jogador estiver vivo e não estiver em game over
    # Bloqueia movimento se o personagem estiver atirando
    delta_x = 0
    if not jogador.is_dying and not game_over:
        teclas = pygame.key.get_pressed()
        # Só permite movimento se não estiver atirando
        if jogador.shot_timer <= 0:
            if teclas[pygame.K_LEFT]:
                delta_x = -jogador.speed
            if teclas[pygame.K_RIGHT]:
                delta_x = jogador.speed
            if teclas[pygame.K_RIGHT] and teclas[pygame.K_LEFT]:
                delta_x=0
        #Atualiza câmera e direção 
        if delta_x != 0:
            camera_x += delta_x
            jogador.facing = "right" if delta_x > 0 else "left"

    # Mantém o personagem no centro
    jogador.rect.centerx = LARGURA_TELA // 2
    
    # --- Bloqueia atualizações do jogo durante game over ---
    if not game_over:
        # Atualiza plataformas ANTES de verificar colisões (para ter rects atualizados)
        for plataforma in plataformas:
            plataforma.update(camera_x)
    
    # Aplica gravidade ANTES de verificar colisões (só se não estiver em game over)
    if not game_over:
        jogador.vel_y += jogador.gravidade
        jogador.rect.y += int(jogador.vel_y)
    
    # Verifica colisão com plataformas PRIMEIRO (só se não estiver em game over)
    em_plataforma = False
    if not game_over:
        for plataforma in plataformas:
            # Verifica se o jogador está horizontalmente sobre a plataforma
            centro_x_jogador = jogador.rect.centerx
            esquerda_plataforma = plataforma.rect.left
            direita_plataforma = plataforma.rect.right
            
            if centro_x_jogador >= esquerda_plataforma and centro_x_jogador <= direita_plataforma:
                # Verifica se o jogador está verticalmente próximo do topo da plataforma
                base_jogador = jogador.rect.bottom
                topo_plataforma = plataforma.rect.top
                
                # Se o bottom do jogador está entre o topo da plataforma (com tolerância)
                # Aumenta a tolerância superior para manter o jogador na plataforma
                if base_jogador >= topo_plataforma - 10 and base_jogador <= topo_plataforma + 25:
                    # Se está caindo, parado, ou ligeiramente acima (mas ainda dentro da tolerância)
                    if jogador.vel_y >= -2:  # Permite pequena velocidade para cima mas ainda considera em cima
                        # Coloca em cima da plataforma
                        jogador.rect.bottom = topo_plataforma
                        if jogador.vel_y > 0:  # Só zera velocidade se estava caindo
                            jogador.vel_y = 0.0
                        em_plataforma = True
                        jogador.no_chao = True
                        jogador.can_double_jump = True
                        jogador.used_double = False
                        break
        
        # Se não está em plataforma, verifica chão
        if not em_plataforma:
            if jogador.rect.bottom >= CHAO_Y:
                jogador.rect.bottom = CHAO_Y
                jogador.vel_y = 0.0
                jogador.no_chao = True
                jogador.can_double_jump = True
                jogador.used_double = False
            else:
                jogador.no_chao = False
    
    # Agora atualiza a animação (já com no_chao correto)
    jogador.update(delta_tempo, moving=(delta_x != 0))
    
    # Posição do protagonista no mundo (para os inimigos)
    posicao_mundo_x_jogador = camera_x + jogador.rect.centerx
    posicao_mundo_y_jogador = jogador.rect.centery
    
    # --- Bloqueia atualizações do jogo durante game over ---
    if not game_over:
        # Atualiza os projéteis do jogador primeiro
        projeteis.update(delta_tempo)
        
        # Atualiza projéteis dos inimigos
        projeteis_inimigos.update(delta_tempo)
        
        # Atualiza colunas de fogo
        for coluna_fogo in colunas_fogo:
            coluna_fogo.update(delta_tempo, camera_x)
        
        # Atualiza corações
        for coracao in coracoes:
            coracao.update(delta_tempo, camera_x)
        
        # --- Sistema de Inimigos ---
        # Atualiza inimigos PRIMEIRO para ter rects atualizados
        for inimigo in inimigos:
            # CRÍTICO: NÃO aplica física se o inimigo está morrendo
            # Isso garante que a posição seja preservada quando o inimigo morre
            if not inimigo.is_dying:
                # Aplica gravidade e verifica colisão com plataformas
                inimigo.vel_y += inimigo.gravidade
                inimigo.rect.y += int(inimigo.vel_y)
                
                # Verifica colisão com plataformas
                inimigo_em_plataforma = False
                for plataforma in plataformas:
                    if inimigo.rect.colliderect(plataforma.rect):
                        # Verifica se o inimigo está em cima da plataforma
                        base_inimigo = inimigo.rect.bottom
                        topo_plataforma = plataforma.world_y
                        # Tolerância para detectar quando está em cima
                        if base_inimigo >= topo_plataforma - 10 and base_inimigo <= topo_plataforma + 15:
                            # Se está caindo ou parado, coloca em cima da plataforma
                            if inimigo.vel_y >= 0:
                                inimigo.rect.bottom = topo_plataforma
                                inimigo.vel_y = 0.0
                                inimigo_em_plataforma = True
                                inimigo.no_chao = True
                                break
                
                # Se não está em plataforma, verifica chão
                if not inimigo_em_plataforma:
                    if inimigo.rect.bottom >= CHAO_Y:
                        inimigo.rect.bottom = CHAO_Y
                        inimigo.vel_y = 0.0
                        inimigo.no_chao = True
                    else:
                        inimigo.no_chao = False
            
            # Careca: verifica se deve atirar ANTES de atualizar (para que shot_timer seja definido e a animação apareça no mesmo frame)
            if isinstance(inimigo, Careca):
                if inimigo.alive and not inimigo.is_dying and not jogador.is_dying:
                    if inimigo.pode_atirar(posicao_mundo_x_jogador, posicao_mundo_y_jogador):
                        projetil = inimigo.shoot(posicao_mundo_x_jogador, posicao_mundo_y_jogador)
                        if projetil:
                            projeteis_inimigos.add(projetil)
                            # Toca som de tiro do Careca
                            if som_tiro_careca is not None:
                                try:
                                    som_tiro_careca.play()
                                except Exception as e:
                                    print(f"Erro ao tocar som de tiro do Careca: {e}")
            
            # Atualiza o inimigo (agora com shot_timer já definido se o Careca atirou)
            inimigo.update(delta_tempo, camera_x, (posicao_mundo_x_jogador, posicao_mundo_y_jogador))
            
            # Cyborg soca quando perto - só causa dano se o jogador estiver vivo
            if isinstance(inimigo, InimigoCyborg):
                if inimigo.alive and not inimigo.is_dying and inimigo.punch_timer > 0:
                    # O inimigo.rect já foi atualizado no update() com centerx correto
                    # Usa o rect diretamente para verificar colisão
                    if inimigo.rect.colliderect(jogador.rect) and not jogador.is_dying:
                        # Aplica dano ao jogador (com cooldown de invencibilidade)
                        jogador.take_damage(1)
        
        # --- Colisões de projéteis do jogador com inimigos ---
        # Verifica colisões DEPOIS de atualizar inimigos para ter rects corretos
        for bala in list(projeteis):
            # Verifica se a bala ainda existe (pode ter sido removida em iteração anterior)
            if bala not in projeteis:
                continue
                
            inimigo_atingido = None
            
            for inimigo in list(inimigos):
                # Verifica se o inimigo está válido (vivo e não morrendo)
                if not inimigo.alive or inimigo.is_dying:
                    continue

                # Usa o rect do inimigo que já foi atualizado no update()
                # O inimigo.rect.x já está correto (world_x - camera_x)
                # Verifica colisão diretamente com o rect atualizado
                if bala.rect.colliderect(inimigo.rect):
                    inimigo_atingido = inimigo
                    # Remove o projétil IMEDIATAMENTE para evitar que acerte outros inimigos
                    bala.kill()
                    # Verifica se o inimigo estava vivo antes de aplicar dano
                    estava_vivo = inimigo_atingido.alive and not inimigo_atingido.is_dying
                    # Aplica dano apenas ao primeiro inimigo acertado
                    inimigo_atingido.take_damage(3)  # Dano aumentado para 3
                    # Se o inimigo morreu (estava vivo e agora está morrendo), incrementa contador
                    if estava_vivo and inimigo_atingido.is_dying:
                        inimigos_mortos += 1
                    break  # Para imediatamente após encontrar e processar colisão
        
        # Remove inimigos que saíram muito atrás ou à frente da câmera
        # (mas não remove os que estão morrendo, para mostrar a animação)
        for inimigo in list(inimigos):
            if not inimigo.is_dying:  # Só remove se não estiver morrendo
                # Remove se saiu muito atrás da câmera
                if inimigo.world_x < camera_x - LARGURA_TELA:
                    inimigo.kill()
                # Remove se saiu muito à frente da câmera
                elif inimigo.world_x > camera_x + LARGURA_TELA * 2:
                    inimigo.kill()
        
        # Projéteis dos inimigos acertam o jogador
        jogador_atingido = pygame.sprite.spritecollide(jogador, projeteis_inimigos, True)
        if jogador_atingido and not jogador.is_dying:
            # Aplica dano ao jogador (o sistema de invencibilidade impede múltiplos danos)
            jogador.take_damage(1)
        
        # Colisão do jogador com corações
        colisoes_coracao = pygame.sprite.spritecollide(jogador, coracoes, True)
        for coracao in colisoes_coracao:
            if not jogador.is_dying:
                jogador.heal(2)  # Restaura 2 de vida
        
        # Colisão do jogador com colunas de fogo (apenas se estiver no mesmo X)
        for coluna_fogo in colunas_fogo:
            # Verifica se o jogador está no mesmo X (com pequena tolerância)
            centro_x_jogador = jogador.rect.centerx
            centro_x_fogo = coluna_fogo.rect.centerx
            distancia_x = abs(centro_x_jogador - centro_x_fogo)
            
            # Tolerância muito pequena: apenas 10 pixels de diferença em X
            if distancia_x <= 10:
                # Verifica se está entre o chão (bottom da coluna) e uma altura específica acima
                base_fogo = coluna_fogo.rect.bottom
                centro_y_fogo = coluna_fogo.rect.centery
                altura_dano = centro_y_fogo - 30  # Do chão até 30 pixels acima do centro
                
                # Jogador deve estar entre o chão e a altura máxima de dano
                # Verifica se qualquer parte do jogador está na área de dano (do chão até altura_dano)
                # O jogador está na área se seu bottom está acima do chão E seu top está abaixo da altura máxima
                if jogador.rect.bottom >= base_fogo and jogador.rect.top <= altura_dano:
                    if coluna_fogo.can_damage() and not jogador.is_dying:
                        if jogador.take_damage(1):
                            coluna_fogo.apply_damage()
        
        # Remove colunas de fogo que saíram da tela
        for coluna_fogo in list(colunas_fogo):
            if coluna_fogo.world_x < camera_x - LARGURA_TELA:
                coluna_fogo.kill()
            elif coluna_fogo.world_x > camera_x + LARGURA_TELA * 2:
                coluna_fogo.kill()
        
        # Remove plataformas que saíram da tela
        for plataforma in list(plataformas):
            if plataforma.world_x < camera_x - LARGURA_TELA:
                plataforma.kill()
            elif plataforma.world_x > camera_x + LARGURA_TELA * 2:
                plataforma.kill()
        
        # Spawn de novos inimigos (Cyborg ou Careca) - apenas se o jogador estiver vivo
        if jogador.is_alive() and not jogador.is_dying:
            temporizador_spawn += delta_tempo
            if temporizador_spawn >= intervalo_spawn:
                temporizador_spawn = 0.0
                # Alterna entre spawnar pela direita e esquerda
                lado = random.choice(["direita", "esquerda"])
                # Alterna aleatoriamente entre Cyborg e Careca
                tipo_inimigo = random.choice(["cyborg", "careca"])
                
                # Spawna apenas no chão (inimigos em plataformas são spawnados junto com a plataforma)
                posicao_y_spawn = CHAO_Y
                posicao_x_spawn = camera_x + LARGURA_TELA if lado == "direita" else camera_x - LARGURA_TELA
                spawnar_em_plataforma = False
                plataforma_escolhida = None
                
                if tipo_inimigo == "careca":
                    novo_inimigo = spawn_careca(posicao_x_spawn, posicao_y_spawn, LARGURA_TELA, jogador.rect.centery, x_offset=0, lado=lado)
                else:
                    novo_inimigo = spawn_inimigo_cyborg(posicao_x_spawn, posicao_y_spawn, LARGURA_TELA, jogador.rect.centery, x_offset=0, lado=lado)
                
                # Ajusta a posição Y do inimigo se estiver em uma plataforma
                if spawnar_em_plataforma and plataforma_escolhida:
                    novo_inimigo.rect.bottom = plataforma_escolhida.world_y
                    novo_inimigo.world_x = posicao_x_spawn
                
                inimigos.add(novo_inimigo)
        
        # Spawn de colunas de fogo - apenas se o jogador estiver vivo
        if jogador.is_alive() and not jogador.is_dying:
            temporizador_spawn_fogo += delta_tempo
            if temporizador_spawn_fogo >= intervalo_spawn_fogo:
                temporizador_spawn_fogo = 0.0
                # Spawna coluna de fogo à frente do jogador
                posicao_x_fogo = camera_x + LARGURA_TELA + random.randint(200, 400)
                # A coluna será posicionada no chão (o rect.bottom será ajustado no update)
                posicao_y_fogo = CHAO_Y
                coluna_fogo = ColunaFogo(posicao_x_fogo, posicao_y_fogo, scale=3.0)  # Aumentado para 3.0
                # Ajusta o bottom da coluna para ficar no chão
                coluna_fogo.rect.bottom = CHAO_Y
                coluna_fogo.world_y = CHAO_Y
                colunas_fogo.add(coluna_fogo)
                
                # Spawna plataforma antes da coluna de fogo
                largura_plataforma = 200
                altura_plataforma = 20
                posicao_x_plataforma = posicao_x_fogo - largura_plataforma - 50  # 50 pixels antes da coluna
                posicao_y_plataforma = CHAO_Y - 150  # 150 pixels acima do chão
                plataforma = Plataforma(posicao_x_plataforma, posicao_y_plataforma, largura_plataforma, altura_plataforma)
                plataformas.add(plataforma)
                
                # Spawna inimigos na plataforma (sempre spawna pelo menos 1, 50% de chance de 2)
                chance_inimigo = random.random()
                quantidade_inimigos = 1  # Sempre pelo menos 1 inimigo
                if chance_inimigo < 0.5:
                    quantidade_inimigos = 2  # 50% de chance de 2 inimigos
                
                for i in range(quantidade_inimigos):
                    # Posiciona inimigo na plataforma com variação
                    posicao_x_inimigo = posicao_x_plataforma + random.randint(20, largura_plataforma - 20)
                    posicao_y_inimigo = posicao_y_plataforma  # Topo da plataforma
                    
                    # Escolhe tipo de inimigo aleatoriamente
                    tipo_inimigo = random.choice(["cyborg", "careca"])
                    if tipo_inimigo == "careca":
                        novo_inimigo = spawn_careca(posicao_x_inimigo, posicao_y_inimigo, LARGURA_TELA, jogador.rect.centery, x_offset=0, lado="direita")
                    else:
                        novo_inimigo = spawn_inimigo_cyborg(posicao_x_inimigo, posicao_y_inimigo, LARGURA_TELA, jogador.rect.centery, x_offset=0, lado="direita")
                    
                    # Ajusta a posição Y para ficar no topo da plataforma
                    novo_inimigo.rect.bottom = posicao_y_plataforma
                    novo_inimigo.world_x = posicao_x_inimigo
                    inimigos.add(novo_inimigo)
        
        # Spawn de corações - apenas se o jogador estiver vivo e não houver muitos corações na tela
        if jogador.is_alive() and not jogador.is_dying:
            temporizador_spawn_coracao += delta_tempo
            if temporizador_spawn_coracao >= intervalo_spawn_coracao:
                # Só spawna se não houver muitos corações na tela
                if len(coracoes) < MAX_CORACOES_NA_TELA:
                    temporizador_spawn_coracao = 0.0
                    # Spawna coração mais longe do jogador (no chão) - à frente da tela visível
                    posicao_x_coracao = camera_x + random.randint(LARGURA_TELA + 200, LARGURA_TELA * 2)  # Spawna longe, à frente do jogador
                    coracao = Coracao(posicao_x_coracao, CHAO_Y, escala=1.0)  # Tamanho fixo de 30x30 pixels
                    # Ajusta o bottom do coração para ficar no chão
                    coracao.world_y = CHAO_Y
                    # Atualiza a posição baseada na câmera (o update vai ajustar o rect)
                    coracao.update(0, camera_x)  # Atualiza uma vez para posicionar corretamente
                    # Garante que o bottom está no chão (corrige qualquer problema de posicionamento)
                    coracao.rect.bottom = CHAO_Y
                    coracoes.add(coracao)
                else:
                    # Se já há muitos corações, reseta o timer mas não spawna
                    temporizador_spawn_coracao = 0.0
        
        # Remove corações que saíram da tela
        for coracao in list(coracoes):
            if coracao.world_x < camera_x - LARGURA_TELA:  # Remove quando sair da tela à esquerda
                coracao.kill()
            elif coracao.world_x > camera_x + LARGURA_TELA * 2:  # Remove quando sair da tela à direita
                coracao.kill()

    #Desenha fundo e personagem
    desenhar_parallax(tela, camadas_fundo, camera_x, LARGURA_TELA)
    
    # Desenha inimigos (incluindo os que estão morrendo)
    for inimigo in inimigos:
        # O inimigo.rect já foi atualizado no update() com centerx correto
        # Verifica se o inimigo está dentro da área visível da tela usando centerx
        centro_x_tela_inimigo = inimigo.rect.centerx
        
        # Verifica se o inimigo está dentro da área visível da tela
        if -100 <= centro_x_tela_inimigo <= LARGURA_TELA + 100:  # Margem de 100px
            # Usa o rect diretamente que já está correto (centerx já foi atualizado)
            tela.blit(inimigo.image, inimigo.rect)
    
    # Desenha protagonista (com efeito de piscar mais rápido quando sofre dano)
    if jogador.is_dying:
        # Quando morto, mostra a animação de morte sem piscar
        tela.blit(jogador.image, jogador.rect)
    elif jogador.invincibility_timer > 0:
        # Pisca o personagem rapidamente quando invencível (animação de dano mais rápida)
        # Multiplicador maior = piscar mais rápido (75 cria um efeito 1.5x mais rápido)
        visivel = math.sin(jogador.invincibility_timer * 75) > 0
        if visivel:
            tela.blit(jogador.image, jogador.rect)
    else:
        tela.blit(jogador.image, jogador.rect)
    
    # Desenha projéteis
    projeteis.draw(tela)  # Projéteis do protagonista
    projeteis_inimigos.draw(tela)  # Projéteis dos inimigos
    
    # Desenha plataformas
    for plataforma in plataformas:
        # Verifica se a plataforma está dentro da área visível da tela
        if -100 <= plataforma.rect.centerx <= LARGURA_TELA + 200:
            tela.blit(plataforma.image, plataforma.rect)
    
    # Desenha colunas de fogo
    for coluna_fogo in colunas_fogo:
        # Verifica se a coluna está dentro da área visível da tela
        if -100 <= coluna_fogo.rect.centerx <= LARGURA_TELA + 100:
            tela.blit(coluna_fogo.image, coluna_fogo.rect)
    
    # Desenha corações
    for coracao in coracoes:
        # Verifica se o coração está dentro da área visível da tela
        if -50 <= coracao.rect.centerx <= LARGURA_TELA + 50:  # Margem de 50px
            tela.blit(coracao.image, coracao.rect)
    
    # Desenha corações de vida por último para ficar sempre visível
    desenhar_coracoes_vida(tela, jogador, x=20, y=20, tamanho_coracao=30)
    
    # --- Desenha mensagens de Game Over ---
    if game_over:
        # Mostra "Você Morreu" durante os primeiros 3 segundos
        if not mostrando_popup:
            fonte_mensagem = obter_fonte_arcade(48)
            # Cria o texto principal em cinza
            texto_morreu = fonte_mensagem.render("Você Morreu", False, (128, 128, 128))
            rect_texto = texto_morreu.get_rect(center=(LARGURA_TELA // 2, ALTURA_TELA // 2))
            
            # Desenha brilho amarelo ao redor das letras (outline/glow)
            # Renderiza o texto em amarelo várias vezes com pequenos offsets
            cor_amarelo = (255, 255, 0)
            offsets = [(-2, -2), (-2, 0), (-2, 2), (0, -2), (0, 2), (2, -2), (2, 0), (2, 2),
                       (-1, -1), (-1, 1), (1, -1), (1, 1)]
            for offset_x, offset_y in offsets:
                texto_glow = fonte_mensagem.render("Você Morreu", False, cor_amarelo)
                rect_glow = texto_glow.get_rect(center=(LARGURA_TELA // 2 + offset_x, ALTURA_TELA // 2 + offset_y))
                tela.blit(texto_glow, rect_glow)
            
            # Desenha o texto principal por cima do brilho
            tela.blit(texto_morreu, rect_texto)
        else:
            # Mostra pop-up 400x400 centralizado com borda cinza e preenchimento preto
            # Aumentado para 400 para caber os 5 jogadores
            popup_largura = 400
            popup_altura = 400
            popup_x = (LARGURA_TELA - popup_largura) // 2
            popup_y = (ALTURA_TELA - popup_altura) // 2
            espessura_borda = 4  # Espessura da borda cinza
            
            # Desenha borda cinza (retângulo externo)
            popup_borda = pygame.Surface((popup_largura, popup_altura))
            popup_borda.fill((128, 128, 128))
            tela.blit(popup_borda, (popup_x, popup_y))
            
            # Desenha preenchimento preto (retângulo interno)
            popup_interno = pygame.Surface((popup_largura - espessura_borda * 2, popup_altura - espessura_borda * 2))
            popup_interno.fill((0, 0, 0))
            tela.blit(popup_interno, (popup_x + espessura_borda, popup_y + espessura_borda))
            
            # Desenha "Ranking de Jogadores" no topo do pop-up
            fonte_titulo = obter_fonte_arcade(28)
            # Usa antialias=False para fonte pixelizada
            texto_ranking = fonte_titulo.render("Ranking de Jogadores", False, (255, 255, 255))
            rect_ranking = texto_ranking.get_rect(center=(LARGURA_TELA // 2, popup_y + 40))
            tela.blit(texto_ranking, rect_ranking)
            
            # Ordena histórico por mortes (decrescente) e pega os top 5 com mais mortes
            historico_ordenado = sorted(historico_jogadores, key=lambda x: x["mortes"], reverse=True)
            historico_ordenado = historico_ordenado[:5]  # Apenas os 5 com mais mortes
            
            # Desenha os últimos 5 jogadores
            fonte_resultado = obter_fonte_arcade(20)
            y_offset = 80
            for i, jogador_info in enumerate(historico_ordenado):
                texto_resultado = f"{jogador_info['nome']} {jogador_info['mortes']}"
                texto_renderizado = fonte_resultado.render(texto_resultado, False, (255, 255, 255))
                rect_resultado = texto_renderizado.get_rect(center=(LARGURA_TELA // 2, popup_y + y_offset))
                tela.blit(texto_renderizado, rect_resultado)
                y_offset += 30
            
            # Se não houver histórico, mostra o jogador atual
            if len(historico_ordenado) == 0 and nome_usuario:
                fonte_resultado = obter_fonte_arcade(20)
                texto_resultado = f"{nome_usuario} {inimigos_mortos}"
                texto_renderizado = fonte_resultado.render(texto_resultado, False, (255, 255, 255))
                rect_resultado = texto_renderizado.get_rect(center=(LARGURA_TELA // 2, popup_y + 80))
                tela.blit(texto_renderizado, rect_resultado)
            
            # Desenha "PRESSIONE ( R ) PARA RECOMEÇAR" na parte de baixo do pop-up
            fonte_instrucao = obter_fonte_arcade(18)
            # Usa antialias=False para fonte pixelizada
            texto_recomecar = fonte_instrucao.render("PRESSIONE ( R ) PARA RECOMEÇAR", False, (255, 255, 255))
            rect_recomecar = texto_recomecar.get_rect(center=(LARGURA_TELA // 2, popup_y + popup_altura - 50))
            tela.blit(texto_recomecar, rect_recomecar)

    pygame.display.flip()
    tela.fill((0, 0, 0))

pygame.quit()
