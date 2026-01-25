#!/bin/bash

# --- KONFIGURACJA ---
APP_NAME="tysiac"
EXE_NAME="TysiacManager"
ICON_NAME="tysiac.png"

# Kolory
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${YELLOW}🚀 Rozpoczynam procedurę budowania...${NC}"

# ---------------------------------------------------------
# 1. DETEKCJA PYTHONA (Anty-Python 3.14)
# ---------------------------------------------------------
echo "🔍 Szukanie bezpiecznej wersji Pythona (3.10 - 3.13)..."

# Lista priorytetowa (Nuitka najlepiej działa na 3.11)
CANDIDATES=("python3.11" "python3.12" "python3.10" "python3.13")
SELECTED_PYTHON=""

# Sprawdzamy, czy mamy zainstalowane konkretne wersje
for cand in "${CANDIDATES[@]}"; do
    if command -v $cand &>/dev/null; then
        SELECTED_PYTHON=$cand
        break
    fi
done

# Jeśli nie znaleziono konkretnych, sprawdzamy domyślnego, ale weryfikujemy wersję
if [ -z "$SELECTED_PYTHON" ]; then
    if command -v python3 &>/dev/null; then
        VER=$(python3 --version 2>&1)
        if [[ "$VER" == *"3.14"* ]]; then
            echo -e "${RED}❌ BŁĄD KRYTYCZNY: Twój domyślny 'python3' to wersja 3.14!${NC}"
            echo "   Nuitka nie obsługuje poprawnie Pythona 3.14 (błąd _Py_TriggerGC)."
            echo -e "   Musisz zainstalować starszą wersję, np.: ${GREEN}sudo pacman -S python3.11${NC}"
            exit 1
        else
            SELECTED_PYTHON="python3"
        fi
    fi
fi

# Ostateczne sprawdzenie
if [ -z "$SELECTED_PYTHON" ]; then
    echo -e "${RED}❌ Nie znaleziono żadnego odpowiedniego Pythona! Zainstaluj python3.11.${NC}"
    exit 1
fi

echo -e "✅ Wybrano interpreter: ${GREEN}$SELECTED_PYTHON${NC} ($($SELECTED_PYTHON --version))"

# ---------------------------------------------------------
# 2. PRZYGOTOWANIE ŚRODOWISKA (VENV)
# ---------------------------------------------------------
echo -e "🧹 Czyszczenie starego środowiska i plików build..."
rm -rf venv dist build *.build *.dist

echo -e "📦 Tworzenie środowiska wirtualnego..."
$SELECTED_PYTHON -m venv venv

echo -e "🔌 Aktywacja venv..."
source venv/bin/activate

echo -e "⬇️  Instalacja zależności..."
pip install --upgrade pip --quiet
# Instalujemy świeże pakiety wewnątrz venv (niezależnie od systemu)
pip install pyside6 nuitka zstandard --quiet

if [ -f "requirements.txt" ]; then
    pip install -r requirements.txt --quiet
fi

# ---------------------------------------------------------
# 3. BUDOWANIE (NUITKA)
# ---------------------------------------------------------
echo -e "${YELLOW}🔨 Kompilacja w toku...${NC}"

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

# Sprawdzenie błędu
if [ $? -ne 0 ]; then
    echo -e "${RED}❌ Błąd kompilacji!${NC}"
    exit 1
fi

# ---------------------------------------------------------
# 4. PAKOWANIE SKRYPTÓW
# ---------------------------------------------------------
if [ -d "dist/${APP_NAME}.dist" ]; then
    echo -e "${GREEN}✅ Zbudowano pomyślnie!${NC}"
    echo -e "📜 Kopiowanie install.sh i uninstall.sh..."

    cp install.sh "dist/${APP_NAME}.dist/"
    cp uninstall.sh "dist/${APP_NAME}.dist/"

    chmod +x "dist/${APP_NAME}.dist/install.sh"
    chmod +x "dist/${APP_NAME}.dist/uninstall.sh"

    echo -e "${GREEN}📦 Gotowe! Folder 'dist/${APP_NAME}.dist' jest gotowy do spakowania.${NC}"
else
    echo -e "${RED}❌ Błąd: Brak folderu wynikowego.${NC}"
    exit 1
fi

# ---------------------------------------------------------
# 5. TESTOWA INSTALACJA
# ---------------------------------------------------------
echo ""
read -p "❓ Czy zainstalować grę w systemie (/opt)? [t/N]: " choice
if [[ "$choice" =~ ^[TtYy]$ ]]; then
    cd "dist/${APP_NAME}.dist"
    ./install.sh
fi
