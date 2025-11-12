import pygame
import os
from assets import *

def carregar_camadas(screen_height):
   
    camadas = []
    for caminho, fator in caminhos:
        caminho = os.path.normpath(caminho)
        try:
            img = pygame.image.load(caminho).convert_alpha()
        except Exception:
            # Usa a altura da tela para criar fallback proporcional
            largura_fallback = int(screen_height * (4/3))  # Mantém proporção 4:3
            img = pygame.Surface((largura_fallback, screen_height), pygame.SRCALPHA)
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
        # Garante que não desenha além da largura da tela
        while x < screen_width:
            # Só desenha se a imagem estiver dentro ou parcialmente dentro da tela
            if x + largura_img > 0:  # Se a imagem começa antes do fim da tela
                screen.blit(img, (x, 0))
            x += largura_img
            # Para o loop se já passou da tela
            if x >= screen_width:
                break
