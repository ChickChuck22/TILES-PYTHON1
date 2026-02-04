# 🎹 Titanium Piano Tiles

![Titanium Piano Banner](https://img.shields.io/badge/Titanium_Piano-V9.0-00B8D4?style=for-the-badge&logo=pygame)
![Windows](https://img.shields.io/badge/Windows-10/11-0078D6?style=for-the-badge&logo=windows)
![Android](https://img.shields.io/badge/Android-10+-3DDC84?style=for-the-badge&logo=android)
![Python](https://img.shields.io/badge/Python-3.10+-FFD600?style=for-the-badge&logo=python)
![PyQt5](https://img.shields.io/badge/PyQt5-Desktop_UI-green?style=for-the-badge&logo=qt)

**Titanium Piano** é um jogo de ritmo avançado desenvolvido em Python, capaz de transformar **qualquer arquivo MP3** em uma fase desafiadora em tempo real. O projeto utiliza uma arquitetura híbrida para entregar a melhor experiência em cada plataforma: **PyQt5** para menus ricos no Desktop e **Pygame/Kivy** para compatibilidade total no Android.

---

## 🚀 Principais Recursos

- **⚡ Detecção de Batidas em Tempo Real**: Algoritmo que analisa frequências (Beat Detection) para criar tiles perfeitamente sincronizados.
- **❄️ Sistema de Partículas & Física**: Efeitos de neve pulsante e partículas de colisão que reagem à intensidade da música.
- **📱 Suporte Híbrido (PC & Mobile)**:
  - **PC**: Interface Dashboard Premium em Qt5.
  - **Android**: Interface Otimizada em Pygame com suporte a multitoque.
- **⏸️ Menu de Pausa Inteligente**: Pausa com congelamento total e retomada com contagem regressiva de segurança (3s).
- **🖥️ Expansão Dinâmica**: O jogo ajusta automaticamente a área de gameplay (altura da pista) baseada na resolução da tela.
- **� Mecânicas de Ritmo**:
  - **Chords**: Acordes simultâneos.
  - **Holds**: Notas de sustentação dinâmicas.
- **🔥 Modos e Dificuldades**:
  - Personalize velocidade (Scroll Speed), chance de acordes e holds.
  - Presets de "Easy" a "Beyond" (Velocidades insanas).

---

## 🛠️ Instalação e Execução (Windows/Linux)

### 1. Pré-requisitos
Certifique-se de ter **Python 3.10+** instalado.

### 2. Instalação
```bash
git clone https://github.com/ChickChuck22/TILES-PYTHON.git
cd TILES-PYTHON
pip install -r requirements.txt
```

### 3. Jogando
Adicione suas músicas `.mp3` na pasta `assets/music/` e execute:
```bash
python main.py
```

---

## 📱 Compilação para Android (.apk)

O projeto está configurado para o **Buildozer**. Devido a limitações do Qt no Android, o jogo detecta o ambiente e muda automaticamente para o modo Mobile (Menu Pygame).

1. **Ambiente Required**: Linux ou WSL (Windows Subsystem for Linux).
2. **Setup**:
   Confira o guia detalhado em `build_tools/README.md`.
3. **Comando Rápido** (na pasta do projeto):
   ```bash
   buildozer android debug
   ```

---

## 🪟 Compilação para Windows (.exe)

Você pode criar um executável standalone usando o script incluso.
1. Execute:
   ```bash
   python build_tools/windows/build.py
   ```
2. O executável será gerado na pasta `dist/`.

---

## 🎮 Como Jogar

| Ação | Comando PC | Comando Touch (Android) |
| :---: | :---: | :---: |
| **Trilha 1** | Tecla **D** | Toque na Raia 1 |
| **Trilha 2** | Tecla **F** | Toque na Raia 2 |
| **Trilha 3** | Tecla **J** | Toque na Raia 3 |
| **Trilha 4** | Tecla **K** | Toque na Raia 4 |
| **Pausar** | Clique no botão **||** | Toque no botão **||** |
| **Select Song** | Mouse / Teclado | Toque na Lista |

---

## � Estrutura do Projeto

```text
TILES-PYTHON/
├── assets/                 # Músicas, Áudios, Fontes, Ícones
├── build_tools/            # Scripts de Build (Android/Windows)
│   ├── android/            # buildozer.spec e configs
│   └── windows/            # Script PyInstaller
├── src/
│   ├── core/               # Lógica Central (Audio, Beat Detect, State)
│   ├── gameplay/           # Engine do Jogo (Notas, Física, Particles)
│   └── ui/                 # Interfaces (Qt e Pygame)
│       ├── menu_qt.py      # Menu Desktop
│       └── menu_pygame.py  # Menu Mobile
├── main.py                 # Entry Point (Launcher Híbrido)
├── requirements.txt        # Dependências do Python
└── README.md               # Documentação
```

---

## ⚙️ Dependências Principais

- **pygame-ce** (Core Engine)
- **PyQt5** (Desktop UI)
- **librosa** (Análise de Áudio Avançada - Opcional)
- **mutagen** (Metadados MP3)
- **numpy** (Matemática)

---

*Desenvolvido com ❤️ pela equipe de Advanced Agentic Coding.*
