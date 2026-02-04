# 🎹 Titanium Piano Tiles

![Titanium Piano Banner](https://img.shields.io/badge/Titanium_Piano-V9.0-00B8D4?style=for-the-badge&logo=pygame)
![Python Version](https://img.shields.io/badge/Python-3.10+-FFD600?style=for-the-badge&logo=python)
![PyQt5](https://img.shields.io/badge/PyQt5-GUI-green?style=for-the-badge&logo=qt)

**Titanium Piano** é um jogo de ritmo avançado desenvolvido em Python, combinando a precisão da detecção de batidas de áudio com uma interface moderna e efeitos visuais imersivos. Capaz de transformar qualquer arquivo MP3 em uma fase desafiadora em tempo real.

---

## 🚀 Principais Recursos

- **⚡ Detecção de Batidas em Tempo Real**: Algoritmo avançado que analisa frequências e intensidades do áudio para gerar tiles sincronizados.
- **🖥️ Expansão Vertical Dinâmica (V9)**: O jogo detecta a resolução do seu monitor e maximiza a área de jogo para dar mais tempo de reação.
- **🎼 Mecânicas Avançadas**:
  - **Chords**: Acordes de 2 a 3 notas simultâneas.
  - **Holds**: Notas seguradas com "cauda" visual que encolhe com o tempo.
  - **Anti-Collision**: Garantia de fluidez física entre notas consecutivas.
- **🎨 UI de Alta Performance**: Menu Dashboard em **PyQt5** com biblioteca de músicas, sliders de customização e progressão visual.
- **🔥 Modos Extremos**: De "Easy" até "Beyond", com controle total de velocidade e densidade de notas.
- **🤣 Combo Shoutouts**: Mensagens animadas e físicas que aparecem ao atingir marcos de combo.

---

## 🛠️ Instalação

### Pré-requisitos
- Python 3.10 ou superior
- Pip (Gerenciador de pacotes)

### Passos
1. Clone este repositório:
   ```bash
   git clone https://github.com/ChickChuck22/TILES-PYTHON.git
   cd TILES-PYTHON
   ```

2. Instale as dependências:
   ```bash
   pip install -r requirements.txt
   ```

3. Adicione suas músicas:
   - Coloque seus arquivos `.mp3` na pasta `assets/music/`.

4. Execute o jogo:
   ```bash
   python main.py
   ```

---

## 🎮 Como Jogar

| Tecla | Função |
| :---: | :--- |
| **D** | Tecla da Trilhas 1 (Esquerda) |
| **F** | Tecla da Trilhas 2 |
| **J** | Tecla da Trilhas 3 |
| **K** | Tecla da Trilhas 4 (Direita) |
| **ESC** | Sair do jogo |

---

## 🛠️ Estrutura do Projeto

```text
├── assets/             # Músicas, Fontes e Efeitos
├── src/
│   ├── core/           # Constantes, Gerenciador de Áudio e Beat Detector
│   ├── gameplay/       # Engine do Jogo, Lógica de Tiles e Física
│   └── ui/             # Dashboard em PyQt5 e Menu Principal
└── main.py             # Ponto de entrada do sistema
```

---

## 🌟 Customização de Dificuldade

O **Titanium Piano** introduziu um painel inovador onde você pode:
- **Scroll Speed**: De 300 a 2500 pixels/segundo.
- **Chord Probability**: Controla a chance de aparecerem notas triplas.
- **Hold Probability**: Controla a frequência de notas longas.

---

*Desenvolvido com ❤️ pela equipe de Advanced Agentic Coding.*
