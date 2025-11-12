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
idle_careca = os.path.join(base_2,"Idle_2.png")  # Sprite sheet com 7 frames
shot_careca = os.path.join(base_2,"Shot.png")  # Sprite sheet com 11 frames
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

#vilão final (homeless 3)
base_homeless3 = os.path.normpath("assets/Imagens/Homeless_3")
homeless3_idle = os.path.join(base_homeless3, "Idle.png")
homeless3_idle2 = os.path.join(base_homeless3, "Idle_2.png")
homeless3_run = os.path.join(base_homeless3, "Run.png")
homeless3_walk = os.path.join(base_homeless3, "Walk.png")
homeless3_jump = os.path.join(base_homeless3, "Jump.png")
homeless3_attack1 = os.path.join(base_homeless3, "Attack_1.png")
homeless3_attack2 = os.path.join(base_homeless3, "Attack_2.png")
homeless3_special = os.path.join(base_homeless3, "Special.png")
homeless3_hurt = os.path.join(base_homeless3, "Hurt.png")
homeless3_dead = os.path.join(base_homeless3, "Dead.png")

#efeitos de fogo
base_fire = os.path.normpath("assets/Imagens/pack_effect_fire_column/fire_column_medium")
fire_frames_paths = [
    os.path.join(base_fire, f"fire_column_medium_{i}.png") for i in range(1, 15)
]

#item coração
heart_path = os.path.normpath("assets/Imagens/Vida.png")