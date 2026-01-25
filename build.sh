#!/bin/bash

# --- KONFIGURACJA ---
APP_NAME="tysiac"           # Nazwa pliku .py (bez rozszerzenia)
EXE_NAME="TysiacManager"    # Nazwa pliku wynikowego
ICON_NAME="tysiac.png"      # Nazwa ikony
INSTALL_DIR="/opt/tysiac_manager"

# Kolory dla czytelności
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${YELLOW}🚀 Rozpoczynam proces budowania ${EXE_NAME}...${NC}"

# 1. Wykrywanie Pythona (Arch vs Ubuntu)
if command -v python3 &>/dev/null; then
    PY_CMD="python3"
elif command -v python &>/dev/null; then
    PY_CMD="python"
else
    echo -e "${RED}❌ Nie znaleziono pythona!${NC}"
    exit 1
fi
echo -e "🔧 Wykryto interpreter: ${GREEN}$PY_CMD${NC}"

# 2. Przygotowanie venv
if [ ! -d "venv" ]; then
    echo -e "📦 Tworzenie środowiska wirtualnego..."
    $PY_CMD -m venv venv
fi

echo -e "🔌 Aktywacja venv..."
source venv/bin/activate

# 3. Instalacja zależności
echo -e "⬇️ Instalacja bibliotek (PySide6, Nuitka)..."
# Instalujemy/Aktualizujemy pip, żeby nie marudził
pip install --upgrade pip --quiet
pip install pyside6 nuitka zstandard --quiet

# 4. Budowanie (Nuitka)
echo -e "${YELLOW}🔨 Kompilacja w toku (to może potrwać kilka minut)...${NC}"

# Czyścimy stare buildy
rm -rf dist build ${APP_NAME}.build ${APP_NAME}.dist

# Twoja komenda budująca (dynamiczna)
python -m nuitka \
    --standalone \
    --enable-plugin=pyside6 \
    --include-data-file=${ICON_NAME}=${ICON_NAME} \
    --static-libpython=no \
    --output-dir=dist \
    --linux-icon=${ICON_NAME} \
    --output-filename=${EXE_NAME} \
    --remove-output \
    ${APP_NAME}.py

# 5. Sprzątanie i KOPIOWANIE SKRYPTÓW
echo -e "🧹 Sprzątanie plików tymczasowych..."
rm -rf ${APP_NAME}.build

if [ -d "dist/${APP_NAME}.dist" ]; then
    echo -e "${GREEN}✅ Zbudowano pomyślnie w folderze: dist/${APP_NAME}.dist/${NC}"

    echo -e "📜 Kopiowanie skryptów instalacyjnych do paczki..."

    # uninstall.sh z folderu głównego do folderu dystrybucyjnego
    cp uninstall.sh "dist/${APP_NAME}.dist/"

    # Nadajemy prawa do uruchamiania wewnątrz paczki
    chmod +x "dist/${APP_NAME}.dist/uninstall.sh"
    # -------------------------

else
    echo -e "${RED}❌ Błąd budowania! Plik wynikowy nie istnieje.${NC}"
    exit 1
fi

# 6. Pytanie o instalację
echo ""
read -p "❓ Czy chcesz zainstalować grę w systemie (/opt) i dodać skrót? [t/N]: " choice
if [[ "$choice" =~ ^[TtYy]$ ]]; then

    echo -e "${YELLOW}🔑 Wymagane uprawnienia administratora (sudo)...${NC}"

    # Tworzenie katalogu w /opt
    sudo mkdir -p ${INSTALL_DIR}

    # Kopiowanie plików
    echo "📂 Kopiowanie plików do ${INSTALL_DIR}..."
    sudo cp -r dist/${APP_NAME}.dist/* ${INSTALL_DIR}/

    # Uprawnienia (root jest właścicielem, każdy może uruchomić)
    sudo chown -R root:root ${INSTALL_DIR}
    sudo chmod -R 755 ${INSTALL_DIR}

    # Tworzenie pliku .desktop (Skrót w menu)
    DESKTOP_FILE_PATH="/usr/share/applications/${EXE_NAME}.desktop"

    echo "📝 Tworzenie skrótu w menu: ${DESKTOP_FILE_PATH}..."

    # Treść pliku .desktop
    sudo bash -c "cat > ${DESKTOP_FILE_PATH}" <<EOF
[Desktop Entry]
Name=Menadżer Gry 1000
Comment=Aplikacja do liczenia punktów w Tysiąca
Exec=${INSTALL_DIR}/${EXE_NAME}
Icon=${INSTALL_DIR}/${ICON_NAME}
Terminal=false
Type=Application
Categories=Game;
StartupNotify=true
EOF

    echo -e "${GREEN}🎉 Zainstalowano! Znajdziesz mnie w menu aplikacji.${NC}"
    echo -e "ℹ️  Baza danych gier będzie przechowywana w: ~/Tysiac_Manager/"
else
    echo "👋 Pominięto instalację. Wersja przenośna jest w folderze dist."
fi
