import pygame
import random
import math
import os
from Personagens import Protagonista
from plano_de_fundo import carregar_camadas, desenhar_parallax
from Inimigos import InimigoCyborg, spawn_inimigo_cyborg, Careca, spawn_careca, ProjetilInimigo, ColunaFogo, Plataforma, Coracao, InimigoFinal
from assets import heart_path, musica_fundo, musica_fundo2, musica_fundo3, musica_fundo4, musica_final, som_tiro_careca_path, som_tiro_shelby_path, intro_capa_path

pygame.init()
pygame.mixer.init()  # Inicializa o mixer de áudio

# --- Configurações da tela ---
# Obtém o tamanho da tela para modo fullscreen
info_tela = pygame.display.Info()
LARGURA_TELA, ALTURA_TELA = info_tela.current_w, info_tela.current_h
tela = pygame.display.set_mode((LARGURA_TELA, ALTURA_TELA), pygame.FULLSCREEN)
pygame.display.set_caption("THOMAS VELOZES & SHELBYS FURIOSOS")
relogio = pygame.time.Clock()
FPS = 60

# --- Carrega arquivos de áudio ---
# Músicas e sons importados de assets.py

# Carrega os sons
# Músicas de fundo (usa pygame.mixer.music)
try:
    pygame.mixer.music.load(musica_fundo)
    musica_fundo_carregada = True
except Exception as e:
    print(f"Erro ao carregar música de fundo: {e}")
    musica_fundo_carregada = False

try:
    # Verifica se o arquivo existe
    if os.path.exists(musica_fundo2):
        musica_fundo2_carregada = True
    else:
        print(f"Arquivo não encontrado: {musica_fundo2}")
        musica_fundo2_carregada = False
except Exception as e:
    print(f"Erro ao verificar música de fundo 2: {e}")
    musica_fundo2_carregada = False

try:
    # Verifica se o arquivo existe
    if os.path.exists(musica_fundo3):
        musica_fundo3_carregada = True
    else:
        print(f"Arquivo não encontrado: {musica_fundo3}")
        musica_fundo3_carregada = False
except Exception as e:
    print(f"Erro ao verificar música de fundo 3: {e}")
    musica_fundo3_carregada = False

try:
    # Verifica se o arquivo existe
    if os.path.exists(musica_fundo4):
        musica_fundo4_carregada = True
    else:
        print(f"Arquivo não encontrado: {musica_fundo4}")
        musica_fundo4_carregada = False
except Exception as e:
    print(f"Erro ao verificar música de fundo 4: {e}")
    musica_fundo4_carregada = False

try:
    # Verifica se o arquivo existe
    if os.path.exists(musica_final):
        musica_final_carregada = True
    else:
        print(f"Arquivo não encontrado: {musica_final}")
        musica_final_carregada = False
except Exception as e:
    print(f"Erro ao verificar música final: {e}")
    musica_final_carregada = False

# Variáveis para controle de sequência de música
contador_cyberpunk = 0  # Conta quantas vezes cyberpunk-street.mp3 foi tocada
estado_musica = "cyberpunk"  # Estados: "cyberpunk", "som2", "som3" (som4 toca apenas quando o jogador morre)

# Sons de efeito (usam pygame.mixer.Sound)
try:
    som_tiro_careca = pygame.mixer.Sound(som_tiro_careca_path)
except Exception as e:
    print(f"Erro ao carregar som de tiro do Careca: {e}")
    som_tiro_careca = None

try:
    som_tiro_shelby = pygame.mixer.Sound(som_tiro_shelby_path)
except Exception as e:
    print(f"Erro ao carregar som de tiro do Shelby: {e}")
    som_tiro_shelby = None

# --- Tela de Introdução ---
def mostrar_tela_introducao():
    """Mostra a tela de introdução por 5 segundos"""
    # Tenta carregar a imagem
    try:
        imagem_intro = pygame.image.load(intro_capa_path).convert()
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
historico_jogadores = []  # Lista de dicionários: [{"nome": str, "tempo": float}, ...]

# --- Timer do jogo ---
tempo_jogo = 0.0  # Tempo total decorrido desde o início do jogo (em segundos)
tempo_final = None  # Tempo quando o Homeless foi derrotado (None se ainda não foi derrotado)
timer_parado = False  # Flag para indicar se o timer está parado

# --- Função para obter nome do usuário ---
def obter_nome_usuario():
    """Mostra pop-up para o usuário digitar seu nome"""
    global nome_usuario
    
    # Carrega a imagem de introdução (para mostrar de fundo)
    try:
        imagem_fundo = pygame.image.load(intro_capa_path).convert()
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
# Toca cyberpunk-street.mp3 primeiro (será tocada duas vezes antes de alternar)
if musica_fundo_carregada:
    try:
        pygame.mixer.music.play(0)  # 0 = toca uma vez (não loop)
        contador_cyberpunk = 1  # Primeira vez tocando
        estado_musica = "cyberpunk"
    except Exception as e:
        print(f"Erro ao tocar música de fundo: {e}")

# --- Fundo ---
camadas_fundo = carregar_camadas(ALTURA_TELA)
camera_x = 0.0

# --- Altura do chão visual (personagem pisa sobre o cenário) ---
# Calcula dinamicamente baseado na altura da tela (mantém proporção de ~91.67% da altura)
CHAO_Y = int(ALTURA_TELA * 0.9167)   

# --- Fator de escala global para personagens e obstáculos ---
# Baseado na altura da tela (altura original era 600)
ALTURA_ORIGINAL = 600
ESCALA_GLOBAL = ALTURA_TELA / ALTURA_ORIGINAL

# --- Jogador ---
# Posição inicial do jogador: centro X e 150 pixels acima do chão (proporcional)
offset_y_jogador = int(150 * ESCALA_GLOBAL)
posicao_y_jogador = CHAO_Y - offset_y_jogador
scale_jogador = 1.5 * ESCALA_GLOBAL
jogador = Protagonista(LARGURA_TELA // 2, posicao_y_jogador, scale=scale_jogador,
                      idle_count=6, run_count=10, jump_count=10, double_count=10)
# Inicializa a posição do mundo do jogador
jogador.world_x = float(LARGURA_TELA // 2)
jogador.world_y = float(jogador.rect.bottom)  # world_y representa o bottom do personagem

grupo_jogador = pygame.sprite.Group(jogador)
projeteis = pygame.sprite.Group()  # Projéteis do protagonista

# --- Inimigos ---
inimigos = pygame.sprite.Group()
projeteis_inimigos = pygame.sprite.Group()  # Projéteis dos inimigos

# --- Inimigo Final (Boss) ---
inimigo_final = None  # Será criado quando inimigos_mortos >= 150
inimigo_final_spawnado = False  # Flag para evitar spawn múltiplo

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
    # Espaçamento proporcional ao tamanho do coração (mantém proporção)
    espacamento = max(1, int(tamanho_coracao / 6))  # Espaçamento entre corações (proporcional)
    
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
    global nome_usuario, tempo_final, historico_jogadores, inimigos_mortos
    
    # Salva se tiver um nome (tanto se derrotou o chefe quanto se morreu)
    if nome_usuario:
        # Verifica se o último jogador salvo já é o mesmo (evita duplicatas)
        if len(historico_jogadores) > 0:
            ultimo = historico_jogadores[-1]
            # Verifica duplicata considerando nome, tempo e mortes
            if (ultimo["nome"] == nome_usuario and 
                ultimo.get("tempo") == tempo_final and 
                ultimo.get("mortes", 0) == inimigos_mortos):
                # Já foi salvo, não salva novamente
                return
        
        # Salva com tempo (se derrotou o chefe) e número de mortes
        jogador_data = {
            "nome": nome_usuario,
            "mortes": inimigos_mortos
        }
        if tempo_final is not None:
            jogador_data["tempo"] = tempo_final
        
        historico_jogadores.append(jogador_data)
        # NÃO limita mais - mantém TODOS os jogadores para poder mostrar os top 5

# --- Função para reiniciar o jogo ---
def reiniciar_jogo():
    """Reinicia todas as variáveis do jogo para o estado inicial"""
    global camera_x, jogador, grupo_jogador, projeteis, inimigos, projeteis_inimigos
    global colunas_fogo, plataformas, coracoes
    global temporizador_spawn, temporizador_spawn_fogo, temporizador_spawn_coracao
    global inimigos_mortos, inimigo_final, inimigo_final_spawnado
    global tempo_jogo, tempo_final, timer_parado
    
    # NÃO salva aqui porque já foi salvo quando o jogador morreu ou quando pressionou R
    # A função salvar_jogador_atual() já foi chamada antes de reiniciar_jogo()
    
    # Reseta câmera
    camera_x = 0.0
    
    # Recria o jogador (usa mesma posição inicial proporcional)
    offset_y_jogador = int(150 * ESCALA_GLOBAL)
    posicao_y_jogador = CHAO_Y - offset_y_jogador
    scale_jogador = 1.5 * ESCALA_GLOBAL
    jogador = Protagonista(LARGURA_TELA // 2, posicao_y_jogador, scale=scale_jogador,
                          idle_count=6, run_count=10, jump_count=10, double_count=10)
    # Inicializa a posição do mundo do jogador
    jogador.world_x = float(LARGURA_TELA // 2)
    jogador.world_y = float(jogador.rect.bottom)  # world_y representa o bottom do personagem
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
    
    # Reseta inimigo final
    inimigo_final = None
    inimigo_final_spawnado = False
    
    # Reseta timer
    tempo_jogo = 0.0
    tempo_final = None
    timer_parado = False

# --- Estado de Game Over ---
game_over = False
game_over_timer = 0.0
mostrando_popup = False
jogador_morreu_nao_detectado = True  # Flag para detectar quando o jogador morre pela primeira vez

# --- Estado de Vitória (quando o Homeless morre) ---
victory_sequence = False  # Flag para indicar que está na sequência de vitória
victory_timer = 0.0  # Timer para controlar a sequência de vitória
fade_alpha = 0  # Alpha para fade out do fundo (0 = transparente, 255 = opaco)
fade_duration = 5.0  # Duração do fade out em segundos

# --- Loop principal ---
rodando = True
while rodando:
    delta_tempo = relogio.tick(FPS) / 1000.0  # segundos desde o último frame
    
    # Atualiza timer do jogo (só se não estiver parado e não estiver em game over)
    if not timer_parado and not game_over and not jogador.is_dying:
        tempo_jogo += delta_tempo

    # --- Controle de sequência de música ---
    # Verifica se a música atual terminou e alterna para a próxima
    # Sequência: cyberpunk-street.mp3 (2x) → som2.mp3 (1x) → som3.mp3 (1x) → repete
    # (som4.mp3 toca apenas quando o jogador morre)
    if not pygame.mixer.music.get_busy() and not game_over:
        if estado_musica == "cyberpunk":
            # Estava tocando cyberpunk-street.mp3
            if contador_cyberpunk < 2:
                # Ainda precisa tocar mais uma vez
                contador_cyberpunk += 1
                try:
                    pygame.mixer.music.load(musica_fundo)
                    pygame.mixer.music.play(0)  # Toca uma vez
                except Exception as e:
                    print(f"Erro ao tocar cyberpunk-street.mp3: {e}")
            else: 
                # Já tocou duas vezes, agora toca som2.mp3
                if musica_fundo2_carregada:
                    try:
                        pygame.mixer.music.load(musica_fundo2)
                        pygame.mixer.music.play(0)  # Toca uma vez
                        estado_musica = "som2"
                    except Exception as e:
                        print(f"Erro ao tocar som2.mp3: {e}")
        elif estado_musica == "som2":
            # Estava tocando som2.mp3, agora toca som3.mp3
            if musica_fundo3_carregada:
                try:
                    pygame.mixer.music.load(musica_fundo3)
                    pygame.mixer.music.play(0)  # Toca uma vez
                    estado_musica = "som3"
                except Exception as e:
                    print(f"Erro ao tocar som3.mp3: {e}")
        else:  # estado_musica == "som3"
            # Estava tocando som3.mp3, agora volta para cyberpunk-street.mp3 (reinicia sequência)
            if musica_fundo_carregada:
                try:
                    pygame.mixer.music.load(musica_fundo)
                    pygame.mixer.music.play(0)  # Toca uma vez
                    contador_cyberpunk = 1  # Primeira vez da nova sequência
                    estado_musica = "cyberpunk"
                except Exception as e:
                    print(f"Erro ao tocar cyberpunk-street.mp3: {e}")

    for evento in pygame.event.get():
        if evento.type == pygame.QUIT:
            rodando = False
        elif evento.type == pygame.KEYDOWN:
            # Detecta tecla R para reiniciar quando estiver no pop-up (game over ou vitória)
            if (mostrando_popup and (game_over or victory_sequence)) and evento.key == pygame.K_r:
                # NÃO salva aqui porque já foi salvo quando o jogador morreu
                # A função salvar_jogador_atual() já foi chamada quando detectou a morte
                
                # Para a música de fundo antes de reiniciar (se ainda estiver tocando)
                if musica_fundo_carregada or musica_fundo2_carregada or musica_fundo3_carregada or musica_fundo4_carregada:
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
                
                # Reinicia o jogo e toca música de fundo novamente (sequência recomeça)
                reiniciar_jogo()
                if musica_fundo_carregada:
                    try:
                        pygame.mixer.music.load(musica_fundo)
                        pygame.mixer.music.play(0)  # Toca uma vez
                        contador_cyberpunk = 1  # Primeira vez da nova sequência
                        estado_musica = "cyberpunk"
                    except Exception as e:
                        print(f"Erro ao tocar música de fundo: {e}")
                game_over = False
                game_over_timer = 0.0
                mostrando_popup = False
                jogador_morreu_nao_detectado = True
                victory_sequence = False
                victory_timer = 0.0
                fade_alpha = 0
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
        # Jogador acabou de morrer - para o timer e inicia game over
        timer_parado = True
        # Salva o jogador no histórico mesmo sem derrotar o Homeless (com número de mortes)
        salvar_jogador_atual()
        # Para a música de fundo atual e toca som4.mp3 quando o jogador morre
        if musica_fundo_carregada or musica_fundo2_carregada or musica_fundo3_carregada or musica_fundo4_carregada:
            try:
                pygame.mixer.music.stop()
                # Toca som4.mp3 quando o jogador morre
                if musica_fundo4_carregada:
                    pygame.mixer.music.load(musica_fundo4)
                    pygame.mixer.music.play(0)  # Toca uma vez
            except Exception as e:
                print(f"Erro ao parar/tocar música de fundo: {e}")
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
    
    # --- Atualização da sequência de vitória ---
    if victory_sequence:
        victory_timer += delta_tempo
        # Calcula o alpha do fade out (0 = transparente, 255 = opaco)
        # O fade começa em 0 e vai até 255 ao longo de fade_duration segundos
        fade_progress = min(victory_timer / fade_duration, 1.0)
        fade_alpha = int(255 * fade_progress)
        
        # O ranking já é mostrado imediatamente quando victory_sequence começa
        # (mostrando_popup é definido como True quando a animação de morte termina após 2 segundos)
    
    #  Movimento horizontal - só funciona se o jogador estiver vivo e não estiver em game over
    # Bloqueia movimento se o personagem estiver atirando
    # BLOQUEIA movimento da câmera quando o Homeless estiver spawnado, mas permite movimento do personagem
    delta_x = 0
    if not jogador.is_dying and not game_over:
        # Durante a sequência de vitória, o jogador anda automaticamente para a direita
        if victory_sequence:
            # Move lentamente para a direita (velocidade reduzida)
            delta_x = jogador.speed * 0.3  # 30% da velocidade normal
            jogador.facing = "right"
        else:
            teclas = pygame.key.get_pressed()
            # Só permite movimento se não estiver atirando
            if jogador.shot_timer <= 0:
                if teclas[pygame.K_LEFT]:
                    delta_x = -jogador.speed
                if teclas[pygame.K_RIGHT]:
                    delta_x = jogador.speed
                if teclas[pygame.K_RIGHT] and teclas[pygame.K_LEFT]:
                    delta_x=0
        #Atualiza câmera e direção (continua normalmente mesmo com o Homeless)
        if delta_x != 0:
            # Move a câmera normalmente
            camera_x += delta_x
            if not victory_sequence:  # Só atualiza facing se não estiver na sequência de vitória
                jogador.facing = "right" if delta_x > 0 else "left"
    
    # Atualiza a posição na tela do personagem (sempre no centro)
    jogador.rect.centerx = LARGURA_TELA // 2
    # Atualiza world_x para seguir a câmera (mantém posição relativa)
    jogador.world_x = camera_x + jogador.rect.centerx
    
    # --- Bloqueia atualizações do jogo durante game over ---
    if not game_over:
        # Atualiza plataformas ANTES de verificar colisões (para ter rects atualizados)
        try:
            for plataforma in plataformas:
                plataforma.update(camera_x)
        except Exception as e:
            print(f"Erro ao atualizar plataformas: {e}")
            import traceback
            traceback.print_exc()
    
    # Aplica gravidade ANTES de verificar colisões (só se não estiver em game over)
    if not game_over:
        jogador.vel_y += jogador.gravidade
        jogador.world_y += jogador.vel_y
        jogador.rect.bottom = int(jogador.world_y)
    
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
                topo_plataforma = plataforma.world_y
                
                # Se o bottom do jogador está entre o topo da plataforma (com tolerância)
                # Aumenta a tolerância superior para manter o jogador na plataforma
                if base_jogador >= topo_plataforma - 10 and base_jogador <= topo_plataforma + 25:
                    # Se está caindo, parado, ou ligeiramente acima (mas ainda dentro da tolerância)
                    if jogador.vel_y >= -2:  # Permite pequena velocidade para cima mas ainda considera em cima
                        # Coloca em cima da plataforma
                        jogador.world_y = float(topo_plataforma)
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
            if jogador.world_y >= CHAO_Y:
                jogador.world_y = float(CHAO_Y)
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
    # Usa world_x e world_y diretamente quando disponíveis
    try:
        if inimigo_final_spawnado:
            # Durante a fase do boss, usa world_x diretamente
            posicao_mundo_x_jogador = jogador.world_x
            posicao_mundo_y_jogador = jogador.world_y
        else:
            # Modo normal: calcula baseado na câmera
            posicao_mundo_x_jogador = camera_x + jogador.rect.centerx
            posicao_mundo_y_jogador = jogador.world_y
    except Exception as e:
        print(f"Erro ao calcular posição do jogador: {e}")
        # Fallback: usa camera_x normal
        posicao_mundo_x_jogador = camera_x + jogador.rect.centerx
        posicao_mundo_y_jogador = jogador.world_y if hasattr(jogador, 'world_y') else jogador.rect.centery
    
    # --- Bloqueia atualizações do jogo durante game over ---
    if not game_over:
        # Atualiza os projéteis do jogador primeiro
        projeteis.update(delta_tempo)
        
        # Atualiza projéteis dos inimigos (passa camera_x para atualizar posição corretamente)
        for projetil in projeteis_inimigos:
            projetil.update(delta_tempo, camera_x)
        
        # Atualiza colunas de fogo
        for coluna_fogo in colunas_fogo:
            coluna_fogo.update(delta_tempo, camera_x)
        
        # Atualiza corações
        for coracao in coracoes:
            coracao.update(delta_tempo, camera_x)
        
        # --- Sistema de Inimigos ---
        # Atualiza inimigos PRIMEIRO para ter rects atualizados
        for inimigo in inimigos:
            # Pula o Homeless se ele estiver no grupo (ele tem lógica especial de atualização)
            if isinstance(inimigo, InimigoFinal):
                continue  # O Homeless é atualizado separadamente mais abaixo
            
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
                        # Passa camera_x para o método shoot para calcular coordenadas do mundo corretamente
                        projetil = inimigo.shoot(posicao_mundo_x_jogador, posicao_mundo_y_jogador, camera_x)
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
            
            # Homeless soca quando perto - só causa dano se o jogador estiver vivo
            # (Verificado no loop de inimigos, mas o Homeless também é verificado separadamente abaixo)
        
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
        
        # --- Colisões de projéteis do jogador com o Inimigo Final ---
        if inimigo_final is not None and inimigo_final.alive and not inimigo_final.is_dying:
            for bala in list(projeteis):
                if bala.rect.colliderect(inimigo_final.rect):
                    # Remove o projétil
                    bala.kill()
                    # Aplica dano ao inimigo final
                    inimigo_final.take_damage(3)  # Mesmo dano que outros inimigos
                    break  # Apenas um projétil pode acertar por frame
        
        # Remove inimigos que saíram muito atrás ou à frente da câmera
        # Se o Homeless estiver spawnado, remove apenas os inimigos normais (não o Homeless)
        if inimigo_final_spawnado:
            # Se o Homeless estiver spawnado, remove apenas os inimigos normais (não o Homeless)
            for inimigo in list(inimigos):
                # Não remove o Homeless
                if isinstance(inimigo, InimigoFinal):
                    continue
                inimigo.kill()
        else:
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
        # CRÍTICO: Verifica colisão usando rects que correspondem exatamente ao tamanho visual do projétil
        # O rect do projétil já está do tamanho exato da imagem (sem áreas transparentes extras)
        for projetil in list(projeteis_inimigos):
            # Verifica colisão usando o rect do projétil (que é do tamanho exato da imagem)
            # O rect.centerx e rect.centery já estão atualizados no update() com base em world_x e camera_x
            if projetil.rect.colliderect(jogador.rect) and not jogador.is_dying:
                # Remove o projétil
                projetil.kill()
                # Aplica dano ao jogador (o sistema de invencibilidade impede múltiplos danos)
                jogador.take_damage(1)
                break  # Apenas um projétil pode acertar por frame
        
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
        
        # Remove colunas de fogo que saíram da tela ou se o Homeless estiver spawnado
        if inimigo_final_spawnado:
            # Se o Homeless estiver spawnado, remove TODAS as colunas de fogo
            for coluna_fogo in list(colunas_fogo):
                coluna_fogo.kill()
            colunas_fogo.empty()
        else:
            # Remove colunas de fogo que saíram da tela
            for coluna_fogo in list(colunas_fogo):
                if coluna_fogo.world_x < camera_x - LARGURA_TELA:
                    coluna_fogo.kill()
                elif coluna_fogo.world_x > camera_x + LARGURA_TELA * 2:
                    coluna_fogo.kill()
        
        # Remove plataformas que saíram da tela (mas mantém as da batalha final se o Homeless estiver spawnado)
        # Não removemos plataformas quando o Homeless estiver spawnado, pois elas são necessárias para a batalha
        if not inimigo_final_spawnado:
            for plataforma in list(plataformas):
                if plataforma.world_x < camera_x - LARGURA_TELA:
                    plataforma.kill()
                elif plataforma.world_x > camera_x + LARGURA_TELA * 2:
                    plataforma.kill()
        
        # --- Spawn do Inimigo Final quando o jogador mata 150 inimigos ---
        # O Homeless aparece como um inimigo normal, correndo pela direita
        if inimigos_mortos >= 150 and not inimigo_final_spawnado and inimigo_final is None:
            try:
                # Remove todas as plataformas existentes quando o Homeless aparece
                for plataforma in list(plataformas):
                    plataforma.kill()
                plataformas.empty()
                
                # Spawna o Homeless vindo pela direita, como um inimigo normal
                # Posição: fora da tela à direita, no chão
                posicao_x_boss = camera_x + LARGURA_TELA + 100  # Fora da tela à direita, com offset de 100 pixels
                posicao_y_boss = CHAO_Y  # No chão
                # Escala reduzida em 40%: 4.0 * 0.6 = 2.4
                scale_boss = 2.4 * ESCALA_GLOBAL  # Escala reduzida em 40%
                inimigo_final = InimigoFinal(posicao_x_boss, posicao_y_boss, scale=scale_boss, idle_count=6)
                # Adiciona o Homeless ao grupo de inimigos para que ele apareça correndo como os outros
                inimigos.add(inimigo_final)
                inimigo_final_spawnado = True
                print(f"Homeless spawnado vindo pela direita! Posição: {posicao_x_boss}. Inimigos mortos: {inimigos_mortos}")
            except Exception as e:
                print(f"ERRO CRÍTICO ao spawnar Homeless: {e}")
                import traceback
                traceback.print_exc()
                # Define flag mesmo com erro para evitar loop infinito
                inimigo_final_spawnado = True
        
        # Atualiza o Inimigo Final se ele existir
        # O Homeless não atira mais - apenas persegue o jogador
        if inimigo_final is not None:
            # Aplica física (gravidade e colisão com plataformas) ao inimigo final PRIMEIRO
            # Isso garante que world_y esteja atualizado antes do update
            if not inimigo_final.is_dying:
                # Aplica gravidade (mesmo durante animação special)
                inimigo_final.vel_y += inimigo_final.gravidade
                inimigo_final.world_y += inimigo_final.vel_y
                
                # Atualiza rect temporariamente para verificar colisões
                try:
                    camera_x_para_fisica = camera_x
                    centro_x_tela_boss_temp = int(inimigo_final.world_x - camera_x_para_fisica)
                    inimigo_final.rect.centerx = centro_x_tela_boss_temp
                    inimigo_final.rect.bottom = int(inimigo_final.world_y)
                except Exception as e:
                    print(f"Erro ao atualizar rect do Homeless: {e}")
                    import traceback
                    traceback.print_exc()
                
                # Verifica colisão com plataformas
                em_plataforma_boss = False
                for plataforma in plataformas:
                    if inimigo_final.rect.colliderect(plataforma.rect):
                        base_boss = inimigo_final.rect.bottom
                        topo_plataforma = plataforma.world_y
                        if base_boss >= topo_plataforma - 10 and base_boss <= topo_plataforma + 15:
                            if inimigo_final.vel_y >= 0:
                                inimigo_final.world_y = topo_plataforma
                                inimigo_final.vel_y = 0.0
                                em_plataforma_boss = True
                                inimigo_final.no_chao = True
                                break
                
                # Se não está em plataforma, verifica chão
                if not em_plataforma_boss:
                    if inimigo_final.world_y >= CHAO_Y:
                        inimigo_final.world_y = CHAO_Y
                        inimigo_final.vel_y = 0.0
                        inimigo_final.no_chao = True
                    else:
                        inimigo_final.no_chao = False
            
            # Atualiza o inimigo final (calcula movimento horizontal e atualiza animação)
            # O update atualiza world_x e o rect baseado em world_x e world_y
            try:
                inimigo_final.update(delta_tempo, camera_x, (posicao_mundo_x_jogador, posicao_mundo_y_jogador))
                
                # Homeless soca quando perto - só causa dano se o jogador estiver vivo
                if inimigo_final.alive and not inimigo_final.is_dying and inimigo_final.punch_timer > 0:
                    # O inimigo.rect já foi atualizado no update() com centerx correto
                    # Usa o rect diretamente para verificar colisão
                    if inimigo_final.rect.colliderect(jogador.rect) and not jogador.is_dying:
                        # Aplica dano ao jogador (com cooldown de invencibilidade)
                        jogador.take_damage(1)
            except Exception as e:
                print(f"Erro ao atualizar Homeless: {e}")
                import traceback
                traceback.print_exc()
                # Tenta continuar mesmo com erro
                pass
            # Se o inimigo final morreu, para o timer e salva o tempo
            if not inimigo_final.alive:
                if tempo_final is None:  # Só salva uma vez
                    tempo_final = tempo_jogo
                    timer_parado = True
                    print(f"Homeless derrotado! Tempo: {tempo_final:.2f} segundos")
                    # Salva o resultado no histórico
                    salvar_jogador_atual()
                
                # Toca a música final EXATAMENTE quando o Homeless morre (is_dying = True)
                if inimigo_final.is_dying and not hasattr(inimigo_final, '_musica_tocada'):
                    # Marca que a música já foi tocada para não tocar novamente
                    inimigo_final._musica_tocada = True
                    print("Homeless morreu! Tocando música final e mostrando ranking!")
                    # Para a música atual e toca a música final
                    try:
                        pygame.mixer.music.stop()
                        if musica_final_carregada:
                            pygame.mixer.music.load(musica_final)
                            pygame.mixer.music.play(0)  # Toca uma vez
                            print(f"Música final tocando: {musica_final}")
                        else:
                            print(f"AVISO: Música final não foi carregada! Caminho: {musica_final}")
                    except Exception as e:
                        print(f"Erro ao tocar música final: {e}")
                        import traceback
                        traceback.print_exc()
                    # Inicia a sequência de vitória e mostra o ranking imediatamente
                    if not victory_sequence:
                        victory_sequence = True
                        victory_timer = 0.0
                        fade_alpha = 0
                        mostrando_popup = True  # Mostra o ranking imediatamente quando a música começa
                        print("Ranking sendo exibido!")
                
                # Verifica se a animação de morte terminou (após 2 segundos no último frame)
                if inimigo_final.death_animation_finished:
                    # Animação de morte terminou (2 segundos se passaram)
                    inimigo_final = None
                # Se ainda está em is_dying, mantém o sprite para mostrar a animação (2 segundos)
        
        # Spawn de novos inimigos (Cyborg ou Careca) - apenas se o jogador estiver vivo E o boss não estiver spawnado
        if jogador.is_alive() and not jogador.is_dying and not inimigo_final_spawnado:
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
                    novo_inimigo = spawn_careca(posicao_x_spawn, posicao_y_spawn, LARGURA_TELA, jogador.rect.centery, x_offset=0, lado=lado, escala_global=ESCALA_GLOBAL)
                else:
                    novo_inimigo = spawn_inimigo_cyborg(posicao_x_spawn, posicao_y_spawn, LARGURA_TELA, jogador.rect.centery, x_offset=0, lado=lado, escala_global=ESCALA_GLOBAL)
                
                # Ajusta a posição Y do inimigo se estiver em uma plataforma
                if spawnar_em_plataforma and plataforma_escolhida:
                    novo_inimigo.rect.bottom = plataforma_escolhida.world_y
                    novo_inimigo.world_x = posicao_x_spawn
                
                inimigos.add(novo_inimigo)
        
        # Spawn de colunas de fogo - apenas se o jogador estiver vivo E o boss não estiver spawnado
        if jogador.is_alive() and not jogador.is_dying and not inimigo_final_spawnado:
            temporizador_spawn_fogo += delta_tempo
            if temporizador_spawn_fogo >= intervalo_spawn_fogo:
                temporizador_spawn_fogo = 0.0
                # Spawna coluna de fogo à frente do jogador
                posicao_x_fogo = camera_x + LARGURA_TELA + random.randint(200, 400)
                # A coluna será posicionada no chão (o rect.bottom será ajustado no update)
                posicao_y_fogo = CHAO_Y
                scale_coluna_fogo = 3.0 * ESCALA_GLOBAL
                coluna_fogo = ColunaFogo(posicao_x_fogo, posicao_y_fogo, scale=scale_coluna_fogo)
                # Ajusta o bottom da coluna para ficar no chão
                coluna_fogo.rect.bottom = CHAO_Y
                coluna_fogo.world_y = CHAO_Y
                colunas_fogo.add(coluna_fogo)
                
                # Spawna plataforma antes da coluna de fogo
                # Verifica se há plataformas muito próximas antes de criar
                largura_plataforma = int(200 * ESCALA_GLOBAL)
                altura_plataforma = int(20 * ESCALA_GLOBAL)
                posicao_x_plataforma = posicao_x_fogo - largura_plataforma - int(50 * ESCALA_GLOBAL)  # Escalado antes da coluna
                posicao_y_plataforma = CHAO_Y - int(150 * ESCALA_GLOBAL)  # Escalado acima do chão
                
                # Verifica se há plataformas muito próximas (mesma altura Y com tolerância de 50 pixels)
                distancia_minima_plataformas = int(300 * ESCALA_GLOBAL)  # Distância mínima entre plataformas
                pode_criar_plataforma = True
                
                for plataforma_existente in plataformas:
                    # Calcula distância horizontal entre as plataformas
                    distancia_x = abs(plataforma_existente.world_x - posicao_x_plataforma)
                    # Verifica se está na mesma altura (com tolerância de 50 pixels em Y)
                    distancia_y = abs(plataforma_existente.world_y - posicao_y_plataforma)
                    
                    # Se está muito perto horizontalmente E na mesma altura, não cria
                    if distancia_x < distancia_minima_plataformas and distancia_y < 50:
                        pode_criar_plataforma = False
                        break
                
                # Só cria a plataforma se não houver plataformas muito próximas
                plataforma_criada = None
                if pode_criar_plataforma:
                    plataforma_criada = Plataforma(posicao_x_plataforma, posicao_y_plataforma, largura_plataforma, altura_plataforma, plataformas)
                    plataformas.add(plataforma_criada)
                    
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
                            novo_inimigo = spawn_careca(posicao_x_inimigo, posicao_y_inimigo, LARGURA_TELA, jogador.rect.centery, x_offset=0, lado="direita", escala_global=ESCALA_GLOBAL)
                        else:
                            novo_inimigo = spawn_inimigo_cyborg(posicao_x_inimigo, posicao_y_inimigo, LARGURA_TELA, jogador.rect.centery, x_offset=0, lado="direita", escala_global=ESCALA_GLOBAL)
                        
                        # Ajusta a posição Y para ficar no topo da plataforma
                        novo_inimigo.rect.bottom = posicao_y_plataforma
                        novo_inimigo.world_x = posicao_x_inimigo
                        inimigos.add(novo_inimigo)
        
        # Spawn de corações - apenas se o jogador estiver vivo, não houver muitos corações na tela E o boss não estiver spawnado
        if jogador.is_alive() and not jogador.is_dying and not inimigo_final_spawnado:
            temporizador_spawn_coracao += delta_tempo
            if temporizador_spawn_coracao >= intervalo_spawn_coracao:
                # Só spawna se não houver muitos corações na tela
                if len(coracoes) < MAX_CORACOES_NA_TELA:
                    temporizador_spawn_coracao = 0.0
                    # Spawna coração mais longe do jogador (no chão) - à frente da tela visível
                    posicao_x_coracao = camera_x + random.randint(LARGURA_TELA + 200, LARGURA_TELA * 2)  # Spawna longe, à frente do jogador
                    escala_coracao = 1.0 * ESCALA_GLOBAL
                    coracao = Coracao(posicao_x_coracao, CHAO_Y, escala=escala_coracao)
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
        
        # Remove corações que saíram da tela ou se o Homeless estiver spawnado
        if inimigo_final_spawnado:
            # Se o Homeless estiver spawnado, remove TODOS os corações
            for coracao in list(coracoes):
                coracao.kill()
            coracoes.empty()
        else:
            # Remove corações que saíram da tela
            for coracao in list(coracoes):
                if coracao.world_x < camera_x - LARGURA_TELA:  # Remove quando sair da tela à esquerda
                    coracao.kill()
                elif coracao.world_x > camera_x + LARGURA_TELA * 2:  # Remove quando sair da tela à direita
                    coracao.kill()

    #Desenha fundo e personagem
    # Parallax continua normalmente mesmo com o Homeless
    try:
        desenhar_parallax(tela, camadas_fundo, camera_x, LARGURA_TELA)
    except Exception as e:
        print(f"Erro ao desenhar parallax: {e}")
        import traceback
        traceback.print_exc()
        # Desenha um fundo simples em caso de erro
        try:
            tela.fill((30, 30, 50))
        except:
            pass
    
    # Desenha inimigos (incluindo os que estão morrendo)
    for inimigo in inimigos:
        # Pula o Homeless se ele estiver no grupo (ele é desenhado separadamente)
        if isinstance(inimigo, InimigoFinal):
            continue  # O Homeless é desenhado separadamente mais abaixo
        
        # O inimigo.rect já foi atualizado no update() com centerx correto
        # Verifica se o inimigo está dentro da área visível da tela usando centerx
        centro_x_tela_inimigo = inimigo.rect.centerx
        
        # Verifica se o inimigo está dentro da área visível da tela
        if -100 <= centro_x_tela_inimigo <= LARGURA_TELA + 100:  # Margem de 100px
            # Usa o rect diretamente que já está correto (centerx já foi atualizado)
            tela.blit(inimigo.image, inimigo.rect)
    
    # Desenha o Inimigo Final se ele existir (vivo ou morrendo)
    # Agora ele pode estar no grupo de inimigos OU como inimigo_final separado
    if inimigo_final is not None and (inimigo_final.alive or inimigo_final.is_dying):
        # Verifica se o inimigo final está dentro da área visível da tela
        centro_x_tela_boss = inimigo_final.rect.centerx
        if -100 <= centro_x_tela_boss <= LARGURA_TELA + 100:  # Margem de 100px
            tela.blit(inimigo_final.image, inimigo_final.rect)
    
    # Desenha projéteis
    projeteis.draw(tela)  # Projéteis do protagonista
    # Desenha projéteis dos inimigos usando render_rect (para mostrar a imagem completa)
    for projetil in projeteis_inimigos:
        tela.blit(projetil.image, projetil.render_rect)
    
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
    
    # Desenha corações de vida
    tamanho_coracao_vida = int(30 * ESCALA_GLOBAL)
    pos_x_coracao_vida = int(20 * ESCALA_GLOBAL)
    pos_y_coracao_vida = int(20 * ESCALA_GLOBAL)
    desenhar_coracoes_vida(tela, jogador, x=pos_x_coracao_vida, y=pos_y_coracao_vida, tamanho_coracao=tamanho_coracao_vida)
    
    # Desenha timer no canto superior direito
    tempo_para_exibir = tempo_final if tempo_final is not None else tempo_jogo
    minutos = int(tempo_para_exibir // 60)
    segundos = int(tempo_para_exibir % 60)
    texto_timer = f"{minutos:02d}:{segundos:02d}"
    fonte_timer = obter_fonte_arcade(int(24 * ESCALA_GLOBAL))
    texto_renderizado_timer = fonte_timer.render(texto_timer, False, (255, 255, 255))
    # Posiciona no canto superior direito
    pos_x_timer = LARGURA_TELA - texto_renderizado_timer.get_width() - int(20 * ESCALA_GLOBAL)
    pos_y_timer = int(20 * ESCALA_GLOBAL)
    tela.blit(texto_renderizado_timer, (pos_x_timer, pos_y_timer))
    
    # Aplica fade out durante a sequência de vitória (sobre corações de vida e timer, mas ATRÁS do personagem)
    if victory_sequence:
        # Cria uma superfície preta com alpha para fazer fade out em tela cheia
        # Obtém o tamanho atual da tela para garantir que cubra tudo
        largura_atual, altura_atual = tela.get_size()
        fade_surface = pygame.Surface((largura_atual, altura_atual))
        # Preenche toda a superfície com preto
        fade_surface.fill((0, 0, 0))
        # Define o alpha da superfície inteira
        fade_surface.set_alpha(fade_alpha)
        # Blita na posição (0, 0) para cobrir toda a tela
        tela.blit(fade_surface, (0, 0))
    
    # Desenha protagonista (com efeito de piscar mais rápido quando sofre dano)
    # O personagem é desenhado DEPOIS do fade para ficar na frente do fade escuro
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
    
    # --- Desenha ranking durante sequência de vitória ---
    if victory_sequence and mostrando_popup:
        # Mostra pop-up de ranking durante a sequência de vitória
        popup_largura = 400
        popup_altura = 400
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
        
        # Desenha "Ranking de Jogadores" no topo do pop-up
        fonte_titulo = obter_fonte_arcade(28)
        # Verifica se há jogadores que derrotaram o chefe
        jogadores_com_chefe = [j for j in historico_jogadores if j.get("tempo") is not None]
        if jogadores_com_chefe:
            texto_ranking = fonte_titulo.render("Ranking - Melhores Tempos", False, (255, 255, 255))
        else:
            texto_ranking = fonte_titulo.render("Ranking - Mais Mortes", False, (255, 255, 255))
        rect_ranking = texto_ranking.get_rect(center=(LARGURA_TELA // 2, popup_y + 40))
        tela.blit(texto_ranking, rect_ranking)
        
        # Ordena histórico: se houver jogadores que derrotaram o chefe, ordena por tempo
        # Caso contrário, ordena por número de mortes (decrescente)
        if jogadores_com_chefe:
            # Ordena por tempo (crescente - menor tempo = melhor)
            historico_ordenado = sorted(historico_jogadores, key=lambda x: x.get("tempo", float('inf')))
            historico_ordenado = historico_ordenado[:5]  # Apenas os 5 melhores tempos
        else:
            # Ordena por número de mortes (decrescente - mais mortes = melhor)
            historico_ordenado = sorted(historico_jogadores, key=lambda x: x.get("mortes", 0), reverse=True)
            historico_ordenado = historico_ordenado[:5]  # Apenas os 5 com mais mortes
        
        # Desenha os top 5 jogadores
        fonte_resultado = obter_fonte_arcade(20)
        y_offset = 80
        for i, jogador_info in enumerate(historico_ordenado):
            nome_jogador = jogador_info.get("nome", "Desconhecido")
            mortes_jogador = jogador_info.get("mortes", 0)
            tempo_jogador = jogador_info.get("tempo")
            
            # Monta o texto: nome - mortes (e tempo se houver)
            if tempo_jogador is not None:
                minutos = int(tempo_jogador // 60)
                segundos = int(tempo_jogador % 60)
                tempo_formatado = f"{minutos:02d}:{segundos:02d}"
                texto_resultado = f"{nome_jogador} - {mortes_jogador} mortes - {tempo_formatado}"
            else:
                texto_resultado = f"{nome_jogador} - {mortes_jogador} mortes"
            
            texto_renderizado = fonte_resultado.render(texto_resultado, False, (255, 255, 255))
            rect_resultado = texto_renderizado.get_rect(center=(LARGURA_TELA // 2, popup_y + y_offset))
            tela.blit(texto_renderizado, rect_resultado)
            y_offset += 30
        
        # Se não houver histórico, mostra o jogador atual (se tiver derrotado o Homeless)
        if len(historico_ordenado) == 0 and nome_usuario and tempo_final is not None:
            fonte_resultado = obter_fonte_arcade(20)
            minutos = int(tempo_final // 60)
            segundos = int(tempo_final % 60)
            tempo_formatado = f"{minutos:02d}:{segundos:02d}"
            mortes_atual = inimigos_mortos if 'inimigos_mortos' in globals() else 0
            texto_resultado = f"{nome_usuario} - {mortes_atual} mortes - {tempo_formatado}"
            texto_renderizado = fonte_resultado.render(texto_resultado, False, (255, 255, 255))
            rect_resultado = texto_renderizado.get_rect(center=(LARGURA_TELA // 2, popup_y + 80))
            tela.blit(texto_renderizado, rect_resultado)
        
        # Desenha "PRESSIONE ( R ) PARA RECOMEÇAR" na parte de baixo do pop-up
        fonte_instrucao = obter_fonte_arcade(18)
        texto_recomecar = fonte_instrucao.render("PRESSIONE ( R ) PARA RECOMEÇAR", False, (255, 255, 255))
        rect_recomecar = texto_recomecar.get_rect(center=(LARGURA_TELA // 2, popup_y + popup_altura - 50))
        tela.blit(texto_recomecar, rect_recomecar)
    
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
            # Título do ranking
            texto_ranking = fonte_titulo.render("Ranking", False, (255, 255, 255))
            rect_ranking = texto_ranking.get_rect(center=(LARGURA_TELA // 2, popup_y + 40))
            tela.blit(texto_ranking, rect_ranking)
            
            # Ordena histórico: se houver jogadores que derrotaram o chefe, ordena por tempo
            # Caso contrário, ordena por número de mortes (decrescente)
            if jogadores_com_chefe:
                # Ordena por tempo (crescente - menor tempo = melhor)
                historico_ordenado = sorted(historico_jogadores, key=lambda x: x.get("tempo", float('inf')))
                historico_ordenado = historico_ordenado[:5]  # Apenas os 5 melhores tempos
            else:
                # Ordena por número de mortes (decrescente - mais mortes = melhor)
                historico_ordenado = sorted(historico_jogadores, key=lambda x: x.get("mortes", 0), reverse=True)
                historico_ordenado = historico_ordenado[:5]  # Apenas os 5 com mais mortes
            
            # Desenha os top 5 jogadores
            fonte_resultado = obter_fonte_arcade(20)
            y_offset = 80
            for i, jogador_info in enumerate(historico_ordenado):
                nome_jogador = jogador_info.get("nome", "Desconhecido")
                mortes_jogador = jogador_info.get("mortes", 0)
                tempo_jogador = jogador_info.get("tempo")
                
                # Monta o texto: nome - mortes (e tempo se houver)
                if tempo_jogador is not None:
                    minutos = int(tempo_jogador // 60)
                    segundos = int(tempo_jogador % 60)
                    tempo_formatado = f"{minutos:02d}:{segundos:02d}"
                    texto_resultado = f"{nome_jogador} - {mortes_jogador} mortes - {tempo_formatado}"
                else:
                    texto_resultado = f"{nome_jogador} - {mortes_jogador} mortes"
                
                texto_renderizado = fonte_resultado.render(texto_resultado, False, (255, 255, 255))
                rect_resultado = texto_renderizado.get_rect(center=(LARGURA_TELA // 2, popup_y + y_offset))
                tela.blit(texto_renderizado, rect_resultado)
                y_offset += 30
            
            # Se não houver histórico, mostra o jogador atual (se tiver derrotado o Homeless)
            if len(historico_ordenado) == 0 and nome_usuario and tempo_final is not None:
                fonte_resultado = obter_fonte_arcade(20)
                minutos = int(tempo_final // 60)
                segundos = int(tempo_final % 60)
                tempo_formatado = f"{minutos:02d}:{segundos:02d}"
                mortes_atual = inimigos_mortos if 'inimigos_mortos' in globals() else 0
                texto_resultado = f"{nome_usuario} - {mortes_atual} mortes - {tempo_formatado}"
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
