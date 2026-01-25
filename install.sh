#!/bin/bash

# --- KONFIGURACJA ---
APP_NAME="TysiacManager"
DISPLAY_NAME="Menadżer Gry 1000"
ICON_NAME="tysiac.png"
INSTALL_DIR="/opt/tysiac_manager"
DESKTOP_FILE="/usr/share/applications/${APP_NAME}.desktop"

# Kolory
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${YELLOW}🚀 Instalator ${DISPLAY_NAME}${NC}"

# 1. Wstępne sprawdzenie
if [ ! -f "./dist/tysiac.dist/${APP_NAME}" ]; then
    echo -e "${RED}❌ Błąd: Nie jesteś w folderze z grą!${NC}"
    echo "Wejdź do rozpakowanego katalogu i spróbuj ponownie."
    exit 1
fi

# 2. Sudo
if [ "$EUID" -ne 0 ]; then
    echo -e "${YELLOW}🔑 Podaj hasło administratora, aby zainstalować grę...${NC}"
    exec sudo "$0" "$@"
    exit
fi

# 3. Instalacja (Kopiowanie wszystkiego)
echo -e "📂 Instalowanie w ${INSTALL_DIR}..."
mkdir -p "${INSTALL_DIR}"

# Kopiuje: grę, biblioteki, ikonę ORAZ uninstall.sh (bo jest w tym folderze)
cp -r ./dist/tysiac.dist/* "${INSTALL_DIR}/"

# 4. Uprawnienia
echo -e "🔒 Nadawanie uprawnień..."
chown -R root:root "${INSTALL_DIR}"
chmod -R 755 "${INSTALL_DIR}"

# Upewniamy się, że deinstalator jest wykonywalny w systemie
if [ -f "${INSTALL_DIR}/uninstall.sh" ]; then
    chmod +x "${INSTALL_DIR}/uninstall.sh"
fi

# 5. Skrót w menu
echo -e "📝 Tworzenie skrótu..."
cat > "${DESKTOP_FILE}" <<EOF
[Desktop Entry]
Name=${DISPLAY_NAME}
Comment=Aplikacja do liczenia punktów w Tysiąca
Exec=${INSTALL_DIR}/${APP_NAME}
Icon=${INSTALL_DIR}/${ICON_NAME}
Terminal=false
Type=Application
Categories=Game;CardGame;
StartupNotify=true
EOF

if command -v update-desktop-database &> /dev/null; then
    update-desktop-database "${DESKTOP_FILE}" &> /dev/null
fi

echo -e "${GREEN}✅ Gotowe!${NC}"
echo -e "Aby odinstalować, użyj: ${INSTALL_DIR}/uninstall.sh"
