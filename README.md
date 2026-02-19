# 🎹 Titanium Piano Tiles

![Titanium Piano Banner](https://img.shields.io/badge/Titanium_Piano-V9.1-00B8D4?style=for-the-badge&logo=pygame)
![Windows](https://img.shields.io/badge/Windows-10/11-0078D6?style=for-the-badge&logo=windows)
![Python](https://img.shields.io/badge/Python-3.10+-FFD600?style=for-the-badge&logo=python)
![PyQt5](https://img.shields.io/badge/PyQt5-Desktop_UI-green?style=for-the-badge&logo=qt)

**Titanium Piano** é um jogo de ritmo avançado desenvolvido em Python, capaz de transformar **qualquer arquivo MP3** em uma fase desafiadora em tempo real. O projeto utiliza **PyQt5** para criar uma dashboard moderna e rica para seleção de músicas e configurações.

---

## 🚀 Principais Recursos

- **⚡ Detecção de Batidas de Alta Precisão**: Algoritmo que utiliza o processamento do **Librosa** para identificar batidas, ritmos e perfis de energia.
- **🎨 Interface Moderna**: Dashboard com efeitos de sombra, animações suaves e **Indicadores Coloridos de Dificuldade** (Stripes) integrados nos cartões.
- **📁 Otimização de Biblioteca**: Sistema de **Refresh Incremental** que adiciona novas músicas instantaneamente sem travar a interface.
- **🏷️ Metadados Reais**: Extração automática de **Artista, Título e Duração** (ID3) via Mutagen.
- **❄️ Sistema de Partículas & Física**: Efeitos de neve pulsante e partículas de colisão que reagem à intensidade da música.
- **⏸️ Menu de Pausa Inteligente**: Pausa com congelamento total e retomada com contagem regressiva de segurança (3s).
- **🖥️ Expansão Dinâmica**: O jogo ajusta automaticamente a área de gameplay baseada na resolução do monitor.
- **🎼 Mecânicas de Ritmo**:
  - **Chords**: Acordes simultâneos.
  - **Holds**: Notas de sustentação dinâmicas baseadas na energia da música.
- **🌐 Integrações**:
  - **Spotify**: Sincronização de playlists.
  - **YouTube**: Download de áudio com metadados automáticos (Uploader -> Artista).
  - **Discord RPC**: Mostre aos amigos o que você está jogando!

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

## 🪟 Compilação e Instalador (.exe)

O projeto conta com um sistema de build profissional para gerar um instalador Windows.

1. **Compilar Executável**:
   ```bash
   python build_tools/windows/build.py
   ```
2. **Gerar Instalador**:
   - O script detectará automaticamente o **Inno Setup**.
   - **Dica Portátil**: Você pode colocar os arquivos do Inno Setup em `build_tools/InnoSetup/` para gerar instaladores em qualquer PC sem precisar instalar nada!
   - O arquivo instalador `.exe` será gerado na pasta `dist/`.

---

## 🎮 Teclas de Atalho

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
├── build_tools/            # Scripts de Build & Instalador (Windows)
├── src/
│   ├── core/               # Lógica Central (Audio, Analysis Manager, Settings)
│   ├── gameplay/           # Engine do Jogo (Notes, Physics, Particles)
│   ├── services/           # Integrações (YouTube, Spotify, Discord)
│   └── ui/                 # Interfaces
│       └── modern_menu.py  # Dashboard Principal (PyQt5)
├── main.py                 # Entry Point (Game Loop)
├── requirements.txt        # Dependências
└── README.md               # Documentação
```

---

## ⚙️ Dependências Ativas

- **pygame-ce** (Engine principal com maior performance)
- **PyQt5** (Dashboard Desktop)
- **librosa** (Análise de áudio avançada)
- **mutagen** (Leitura de tags de música)
- **yt-dlp** (Download do YouTube)
- **python-dotenv** (Configurações seguras)

---

*Desenvolvido com ❤️ pela equipe de Advanced Agentic Coding.*
