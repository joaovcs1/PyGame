import os

#imagens de personagens
base = os.path.normpath("assets/Imagens/Shelby")
idle_path = os.path.join(base, "shelby_idle.png")
run_path = os.path.join(base, "shelby_run.png")
jump_path = os.path.join(base, "shelby_jump.png")
# reutiliza o sheet de jump para o double jump
double_path = jump_path

#imagens do plano de fundo
caminhos = [
        ("assets/Imagens/Imagens de fundo/back.png", 0.2),
        ("assets/Imagens/Imagens de fundo/middle.png", 0.4),
        ("assets/Imagens/Imagens de fundo/foreground.png", 1.0)
    ]
