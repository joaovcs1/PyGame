PyGame

TÍTULO DO PROJETO: THOMAS VELOZES E SHELBYS FURIOSOS  
MEMBROS: Miguel Amantini, Guilherme Terencio e João Santos

Descrição

Um jogo de ação e plataforma em estilo runner onde você controla o personagem Shelby em uma jornada épica. Derrote inimigos, colete corações para recuperar vida e enfrente o chefão final

Instalação e Dependências

    Requisitos
- Python 3.7 ou superior
- pip (gerenciador de pacotes do Python)

    Instalação das Bibliotecas

O jogo utiliza a biblioteca Pygame para renderização gráfica e áudio. Para instalar, execute o seguinte comando no terminal:

```bash
pip install pygame
```

 Nota:  Se você estiver usando Python 3, pode ser necessário usar `pip3` em vez de `pip`:

```bash
pip3 install pygame
```

    Verificação da Instalação

Para verificar se o Pygame foi instalado corretamente, execute:

```bash
python -m pygame --version
```

ou

```bash
python3 -m pygame --version
```

 Como Jogar

 Controles

-  Seta Esquerda (←) : Move o personagem para a esquerda
-  Seta Direita (→) : Move o personagem para a direita
-  Seta Para Cima (↑) : Pula (pode fazer pulo duplo)
-  Espaço (SPACE) : Atira projéteis
-  R : Reinicia o jogo (quando estiver na tela de Game Over ou Vitória)

 Objetivo do Jogo

1.  Sobreviva : Evite inimigos e obstáculos (colunas de fogo)
2.  Elimine Inimigos : Derrote 150 inimigos para desbloquear o boss final
3.  Colete Corações : Corações aparecem aleatoriamente para restaurar sua vida
4.  Derrote o Boss : Enfrente o chefe final e complete o jogo
5.  Melhore seu Tempo : Tente completar o jogo no menor tempo possível para aparecer no ranking!

Mecânicas do Jogo

-  Sistema de Vida : Você tem 5 corações de vida. Perde um coração ao ser atingido por inimigos ou obstáculos
-  Pulo Duplo : Você pode pular duas vezes no ar para alcançar plataformas mais altas
-  Projéteis : Use o espaço para atirar e eliminar inimigos à distância
- Plataformas: Use as plataformas para se mover verticalmente e evitar inimigos
- Ranking: Seus melhores tempos são salvos e exibidos no ranking após derrotar o chefão final

 Como Executar

1. Se todas as dependências estão instaladas
2. Navegue até a pasta do projeto no terminal
3. Execute o arquivo principal:

```bash
python "loop principal.py"
```

ou

```bash
python3 "loop principal.py"
```

 Como Encerrar o jogo

Pressione "Alt" + "Esc"


 Estrutura do Projeto

- loop principal.py: Arquivo principal do jogo (loop de jogo, eventos, renderização)
- Personagens.py: Classe do personagem principal (Shelby)
- Inimigos.py: Classes dos inimigos e boss final
- plano_de_fundo.py: Sistema de parallax e fundo
- assets/: Pasta contendo imagens, músicas e sons do jogo



    Link do vídeo jogando:

https://youtu.be/7VWJ_XcBcu8?si=V1WP27zsoJ9oqVKK

Observação: Para que o vídeo não ficasse muito extenso, alteramos para que o chefão apareça após matar 10 inimigos.



