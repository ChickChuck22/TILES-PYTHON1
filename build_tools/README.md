# 🛠️ Build Tools

This folder contains scripts and configurations to build **Titanium Piano** for Windows and Android.

## 🪟 Windows (.exe)

We use **PyInstaller** to create a standalone executable.

### Prerequisites
```bash
pip install pyinstaller
```

### How to Build
Run the build script from the project root or any folder:

```bash
python build_tools/windows/build.py
```

The executable will be generated in the `dist` folder at the project root.

---

## 🤖 Android (.apk) - Guia Completo

Criar aplicativos Android com Python requer um ambiente Linux. Se você está no Windows, precisará usar o **WSL (Windows Subsystem for Linux)** ou uma Máquina Virtual.

### Passo 1: Instalar o WSL (Se não tiver)
1. Abra o **PowerShell como Administrador**.
2. Digite: `wsl --install`
3. Reinicie o computador.
4. Após reiniciar, abra o "Ubuntu" no menu iniciar e crie seu usuário/senha.

### Passo 2: Preparar o Ambiente Linux
Abra o seu terminal **Ubuntu** (ou WSL) e rode os comandos abaixo, um por um:

```bash
# 1. Atualizar o sistema
sudo apt update && sudo apt upgrade -y

# 2. Instalar dependências essenciais do Buildozer
sudo apt install -y git zip unzip openjdk-17-jdk python3-pip autoconf libtool pkg-config zlib1g-dev libncurses5-dev libncursesw5-dev libtinfo5 cmake libffi-dev libssl-dev

# 3. Adicionar ferramentas ao PATH (importante!)
echo 'export PATH=$PATH:~/.local/bin' >> ~/.bashrc
source ~/.bashrc

# 4. Instalar o Buildozer
pip3 install --user buildozer
```

### Passo 3: Conectar seu Projeto ao Linux
O WSL consegue acessar seus arquivos do Windows na pasta `/mnt/c/`.
Navegue até a pasta do seu projeto (exemplo):

```bash
# Ajuste o caminho conforme onde seu projeto está
cd /mnt/d/Source/repos/TILES-PYTHON
cd build_tools/android
```

### Passo 4: Gerar o APK
Agora rode o comando mágico:

```bash
buildozer android debug
```

- **A primeira vez demora muito** (ele vai baixar o Android NDK/SDK sozinho). Pode ir tomar um café. ☕
- Se der erro de "missing dependency", leia o erro e instale o que faltar com `sudo apt install`.

### Passo 5: Instalar no Celular
O arquivo `.apk` final aparecerá na pasta `bin` dentro de `build_tools/android`.
- Copie esse arquivo para seu celular e instale.

---

> **⚠️ AVISO IMPORTANTE SOBRE PYQT5**
> O `PyQt5` (usado no menu deste jogo) **NÃO funciona nativamente no Android** com Buildozer.
> O Buildozer usa Kivy/SDL2.
>
> **Para o jogo funcionar no celular, você precisará:**
> 1. Editar o `main.py`.
> 2. Pular a parte do `run_menu()` (que usa Qt).
> 3. Iniciar direto no Pygame ou fazer um menu simples em Pygame.
>
> Se você tentar rodar o APK atual, ele vai fechar logo ao abrir porque não encontrará o Qt.

### 📂 Onde ficam os Arquivos (Assets) no Android?
Quando o APK é instalado, o Buildozer descompacta seus arquivos (`.py`, `.png`, `assets/`) em uma pasta privada interna do Android.
- O caminho base (`./`) é configurado automaticamente para a raiz do seu app.
- Portando, o código `os.path.join("assets", ...)` **funciona normalmente**, desde que você não use caminhos absolutos do Windows (como `C:\...`).

### 📱 Toque na Tela vs. Mouse/Teclado
Verifiquei o código atual e aqui está a situação técnica para Mobile:

1.  **Menu (PyQt5)**:
    - O Qt converte toques simples em "Cliques de Mouse" automaticamente. Se o menu abrisse, botões funcionariam.
    - *Porém*, como mencionado, o Qt é problemático no Android.

2.  **Gameplay (Pygame)**:
    - **Atual**: O jogo escuta apenas o **Teclado** (`pygame.KEYDOWN` nas teclas D, F, J, K).
    - **Android**: O toque na tela gera eventos de Mouse (`MOUSEBUTTONDOWN`) ou Dedo (`FINGERDOWN`).
    - **O que precisa mudar**: Para o jogo funcionar no celular, você precisará editar o `src/gameplay/engine.py` para detectar onde o dedo tocou na tela (Coordenada X) e disparar a nota da trilha correspondente.
    - *Nota*: "Simular mouse" nativo do Android funciona apenas para 1 toque (single touch). Para **Multitouch** (tocar em duas notas ao mesmo tempo), é **obrigatório** implementar a leitura de eventos `pygame.FINGERDOWN`, pois o mouse só existe um por vez.
