import os

#imagens de personagens
base = os.path.normpath("assets/Imagens/3 Cyborg")
idle_path = os.path.join(base, "Cyborg_idle.png")
run_path = os.path.join(base, "Cyborg_run.png")
jump_path = os.path.join(base, "Cyborg_jump.png")
double_path = os.path.join(base, "Cyborg_doublejump.png")

#imagens do plano de fundo
caminhos = [
        ("assets/Imagens/Imagens de fundo/back.png", 0.2),
        ("assets/Imagens/Imagens de fundo/middle.png", 0.4),
        ("assets/Imagens/Imagens de fundo/foreground.png", 1.0)
    ]
