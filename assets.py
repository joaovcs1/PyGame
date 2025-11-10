import os

#imagens de personagens
base = os.path.normpath("assets/Imagens/Shelby")
idle_path = os.path.join(base, "shelby_idle.png")
run_path = os.path.join(base, "shelby_run.png")
jump_path = os.path.join(base, "shelby_jump.png")
# reutiliza o sheet de jump para o double jump
double_path = jump_path

# disparo e projétil
shot_path = os.path.join(base, "shelby_shot.png")
bullet_path = os.path.join(base, "projetil_shelby.png")
# animação de morte
death_path = os.path.join(base, "shelby_dead.png")

#imagens do plano de fundo
caminhos = [
        ("assets/Imagens/Imagens de fundo/back.png", 0.2),
        ("assets/Imagens/Imagens de fundo/middle.png", 0.4),
        ("assets/Imagens/Imagens de fundo/foreground.png", 1.0)
    ]

#inimigo careca
base_2 = os.path.normpath("assets/Imagens/inimigo1")
idle_careca = os.path.join(base_2,"Idle_2.png")
shot_careca = os.path.join(base_2,"Shot.png")  # Sprite sheet com 8 frames (frames 0-2,7 são idle, frames 3-6 são shot)
run_careca = os.path.join(base_2,"Run.png")
dead_careca = os.path.join(base_2,"Dead.png")

#inimigo cyborg
base_cyborg = os.path.normpath("assets/Imagens/3 Cyborg")
cyborg_idle = os.path.join(base_cyborg, "Cyborg_idle.png")
cyborg_run = os.path.join(base_cyborg, "Cyborg_run.png")
cyborg_punch = os.path.join(base_cyborg, "Cyborg_punch.png")
cyborg_attack2 = os.path.join(base_cyborg, "Cyborg_attack2.png")
cyborg_attack3 = os.path.join(base_cyborg, "Cyborg_attack3.png")
cyborg_death = os.path.join(base_cyborg, "Cyborg_death.png")

#efeitos de fogo
base_fire = os.path.normpath("assets/Imagens/pack_effect_fire_column/fire_column_medium")
fire_frames_paths = [
    os.path.join(base_fire, f"fire_column_medium_{i}.png") for i in range(1, 15)
]

#item coração
heart_path = os.path.normpath("assets/Imagens/Vida.png")