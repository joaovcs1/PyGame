import pygame
import os

def carregar_camadas(screen_height):
    #carregar imagens
    caminhos = [
        ("assets/Imagens/Imagens de fundo/back.png", 0.2),
        ("assets/Imagens/Imagens de fundo/middle.png", 0.4),
        ("assets/Imagens/Imagens de fundo/foreground.png", 1.0)
    ]
    camadas = []
    for caminho, fator in caminhos:
        caminho = os.path.normpath(caminho)
        try:
            img = pygame.image.load(caminho).convert_alpha()
        except Exception as e:
            print(f"Erro ao carregar camada {caminho}: {e}")
            img = pygame.Surface((800, 600), pygame.SRCALPHA)
            img.fill((30, 30, 30))

        # escala proporcional pela altura da tela
        if img.get_height() != screen_height:
            escala = screen_height / img.get_height()
            nova_largura = int(img.get_width() * escala)
            img = pygame.transform.smoothscale(img, (nova_largura, screen_height))

        camadas.append((img, fator))
    return camadas


def desenhar_parallax(screen, camadas, camera_x, screen_width):
# Desenha todas as camadas com parallax horizontal infinito (loop contínuo).
    
    for img, fator in camadas:
        largura_img = img.get_width()
        if largura_img <= 0:
            continue
        offset = int(camera_x * fator) % largura_img
        x = -offset
        while x < screen_width:
            screen.blit(img, (x, 0))
            x += largura_img
