#!/bin/bash

# --- KONFIGURACJA ---
# Musi być taka sama jak w install.sh
INSTALL_DIR="/opt/tysiac_manager"
DESKTOP_FILE="/usr/share/applications/TysiacManager.desktop"

# Kolory
YELLOW='\033[1;33m'
GREEN='\033[0;32m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${YELLOW}🗑️  Odinstalowywanie Tysiąc Manager...${NC}"

# 1. Sprawdzenie uprawnień (sudo)
if [ "$EUID" -ne 0 ]; then
    echo -e "${YELLOW}🔑 Wymagane uprawnienia administratora do usunięcia plików systemowych.${NC}"
    exec sudo "$0" "$@"
    exit
fi

# 2. Usuwanie plików aplikacji
if [ -d "$INSTALL_DIR" ]; then
    echo -e "📂 Usuwanie katalogu aplikacji ($INSTALL_DIR)..."
    rm -rf "$INSTALL_DIR"
else
    echo -e "${RED}⚠️  Katalog aplikacji nie istnieje (może już usunięto?).${NC}"
fi

# 3. Usuwanie skrótu z menu
if [ -f "$DESKTOP_FILE" ]; then
    echo -e "📝 Usuwanie skrótu z menu..."
    rm -f "$DESKTOP_FILE"

    # Odświeżenie bazy ikon
    if command -v update-desktop-database &> /dev/null; then
        update-desktop-database &> /dev/null
    fi
else
    echo -e "⚠️  Skrót w menu nie został znaleziony."
fi

echo -e "${GREEN}✅ Odinstalowano pomyślnie.${NC}"
echo -e "ℹ️  Twoje wyniki gier i baza danych POZOSTAŁY w: ~/Tysiac_Manager/"
echo -e "   (Możesz usunąć ten folder ręcznie, jeśli chcesz skasować historię)."
