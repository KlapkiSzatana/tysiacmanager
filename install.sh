#!/bin/bash

# --- KONFIGURACJA ---
APP_NAME="TysiacManager"
EXE_NAME="TysiacManager"       # Nazwa pliku binarnego (z outputu Nuitki)
DISPLAY_NAME="Menadżer Gry 1000"
ICON_NAME="tysiac.png"
INSTALL_DIR="/opt/tysiac_manager"
DESKTOP_FILE="/usr/share/applications/tysiac-manager.desktop"

# Kolory
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${YELLOW}🚀 Instalator ${DISPLAY_NAME}${NC}"

# ---------------------------------------------------------
# 1. DETEKCJA ŹRÓDŁA PLIKÓW (Smart Detection)
# ---------------------------------------------------------
# Sprawdzamy, gdzie są pliki do skopiowania.

SOURCE_DIR=""

if [ -f "./${EXE_NAME}" ]; then
    # Przypadek A: Jesteśmy wewnątrz folderu dist (np. pobrana paczka)
    SOURCE_DIR="."
    echo "📂 Wykryto instalację z wnętrza paczki."
elif [ -d "dist/tysiac.dist" ] && [ -f "dist/tysiac.dist/${EXE_NAME}" ]; then
    # Przypadek B: Jesteśmy w głównym katalogu projektu (budowanie)
    SOURCE_DIR="dist/tysiac.dist"
    echo "📂 Wykryto instalację z katalogu projektu (folder dist/)."
elif [ -d "dist/${APP_NAME}.dist" ] && [ -f "dist/${APP_NAME}.dist/${EXE_NAME}" ]; then
    # Przypadek C: Alternatywna nazwa folderu Nuitki
    SOURCE_DIR="dist/${APP_NAME}.dist"
    echo "📂 Wykryto instalację z katalogu projektu (folder dist/)."
else
    echo -e "${RED}❌ Błąd: Nie znaleziono plików gry!${NC}"
    echo "Upewnij się, że projekt jest zbudowany (dist/) lub jesteś w folderze z grą."
    exit 1
fi

# ---------------------------------------------------------
# 2. SUDO
# ---------------------------------------------------------
if [ "$EUID" -ne 0 ]; then
    echo -e "${YELLOW}🔑 Podaj hasło administratora, aby zainstalować grę...${NC}"
    exec sudo "$0" "$@"
    exit
fi

# ---------------------------------------------------------
# 3. INSTALACJA
# ---------------------------------------------------------
echo -e "📂 Instalowanie w ${INSTALL_DIR}..."

# Czyścimy starą wersję
if [ -d "${INSTALL_DIR}" ]; then
    rm -rf "${INSTALL_DIR}"
fi
mkdir -p "${INSTALL_DIR}"

# Kopiujemy pliki ze znalezionego SOURCE_DIR
cp -r "$SOURCE_DIR"/* "${INSTALL_DIR}/"


# ---------------------------------------------------------
# 4. UPRAWNIENIA
# ---------------------------------------------------------
echo -e "🔒 Nadawanie uprawnień..."
chown -R root:root "${INSTALL_DIR}"
chmod -R 755 "${INSTALL_DIR}"
chmod +x "${INSTALL_DIR}/${EXE_NAME}" # Upewniamy się, że binary jest wykonywalny

if [ -f "${INSTALL_DIR}/uninstall.sh" ]; then
    chmod +x "${INSTALL_DIR}/uninstall.sh"
fi

# ---------------------------------------------------------
# 5. SKRÓT W MENU
# ---------------------------------------------------------
echo -e "📝 Tworzenie skrótu..."
cat > "${DESKTOP_FILE}" <<EOF
[Desktop Entry]
Name=${DISPLAY_NAME}
Comment=Aplikacja do liczenia punktów w Tysiąca
Exec=${INSTALL_DIR}/${EXE_NAME}
Icon=${INSTALL_DIR}/${ICON_NAME}
Terminal=false
Type=Application
Categories=Game;CardGame;
StartupNotify=true
EOF

if command -v update-desktop-database &> /dev/null; then
    update-desktop-database &> /dev/null
fi

echo -e "${GREEN}✅ Gotowe!${NC}"
echo -e "Aby odinstalować, użyj: ${INSTALL_DIR}/uninstall.sh"
