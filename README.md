# 🎹 Titanium Piano Tiles

![Titanium Piano Banner](https://img.shields.io/badge/Titanium_Piano-V9.0-00B8D4?style=for-the-badge&logo=pygame)
![Windows](https://img.shields.io/badge/Windows-10/11-0078D6?style=for-the-badge&logo=windows)
![Python](https://img.shields.io/badge/Python-3.10+-FFD600?style=for-the-badge&logo=python)
![PyQt5](https://img.shields.io/badge/PyQt5-Desktop_UI-green?style=for-the-badge&logo=qt)

**Titanium Piano** é um jogo de ritmo avançado desenvolvido em Python, capaz de transformar **qualquer arquivo MP3** em uma fase desafiadora em tempo real. O projeto utiliza **PyQt5** para criar uma dashboard moderna e rica para seleção de músicas e configurações.

---

## 🚀 Principais Recursos

- **⚡ Detecção de Batidas em Tempo Real**: Algoritmo que analisa frequências (Beat Detection) para criar tiles perfeitamente sincronizados.
- **❄️ Sistema de Partículas & Física**: Efeitos de neve pulsante e partículas de colisão que reagem à intensidade da música.
- **⏸️ Menu de Pausa Inteligente**: Pausa com congelamento total e retomada com contagem regressiva de segurança (3s).
- **🖥️ Expansão Dinâmica**: O jogo ajusta automaticamente a área de gameplay (altura da pista) baseada na resolução do monitor.
- **🎼 Mecânicas de Ritmo**:
  - **Chords**: Acordes simultâneos.
  - **Holds**: Notas de sustentação dinâmicas.
- **🔥 Modos e Dificuldades**:
  - Personalize velocidade (Scroll Speed), chance de acordes e holds.
  - Presets de "Easy" a "Beyond" (Velocidades insanas).

---

## 🛠️ Instalação e Execução (Windows)

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

## 🎵 Configuração do Spotify (Opcional)

Para habilitar a integração com o Spotify:
1. Renomeie o arquivo `.env.example` para `.env` (se já não o fez).
2. Adicione suas credenciais do Spotify no arquivo `.env`:
   ```env
   SPOTIPY_CLIENT_ID='seu_client_id'
   SPOTIPY_CLIENT_SECRET='seu_client_secret'
   SPOTIPY_REDIRECT_URI='http://127.0.0.1:8888/callback'
   ```
3. O jogo irá carregar suas playlists automaticamente se as credenciais estiverem corretas.

---

## 🎥 Configuração do YouTube (FFmpeg)

Para baixar músicas do YouTube, o jogo precisa do **FFmpeg**.
Se a instalação automática falhar (erro de espaço ou permissão), faça manualmente:

1. Baixe o FFmpeg (Essentials Build): [Download aqui (gyan.dev)](https://www.gyan.dev/ffmpeg/builds/ffmpeg-release-essentials.zip)
2. Abra o arquivo ZIP.
3. Entre na pasta `bin`.
4. Copie os arquivos `ffmpeg.exe` **E** `ffprobe.exe`.
5. Cole na pasta `bin` que eu criei na raiz do projeto.

O jogo precisa de ambos para converter o áudio.

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

| Ação | Tecla |
| :---: | :---: |
| **Trilha 1** | Tecla **D** |
| **Trilha 2** | Tecla **F** |
| **Trilha 3** | Tecla **J** |
| **Trilha 4** | Tecla **K** |
| **Pausar** | Clique no botão **||** |
| **Voltar** | **ESC** (no Menu) |

---

## 📂 Estrutura do Projeto

```text
TILES-PYTHON/
├── assets/                 # Músicas, Áudios, Fontes, Ícones
├── build_tools/            # Scripts de Build (Windows)
│   └── windows/            # Script PyInstaller
├── src/
│   ├── core/               # Lógica Central (Audio, Beat Detect, State)
│   ├── gameplay/           # Engine do Jogo (Notas, Física, Particles)
│   └── ui/                 # Interfaces
│       └── menu_qt.py      # Menu Desktop Dashboard
├── main.py                 # Entry Point
├── requirements.txt        # Dependências do Python
└── README.md               # Documentação
```

---

## ⚙️ Dependências Principais

- **pygame-ce** (Core Engine)
- **PyQt5** (Desktop UI)
- **librosa** (Análise de Áudio Avançada)
- **mutagen** (Metadados MP3)
- **numpy** (Matemática)

---

*Desenvolvido com ❤️ pela equipe de Advanced Agentic Coding.*
