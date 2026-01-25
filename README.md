# ♠♥ Manager Gry 1000 (Game Scorekeeper)

**Wersja:** 0.9.1
**Autor:** KlapkiSzatana

Aplikacja desktopowa do zarządzania wynikami w popularnej grze karcianej **Tysiąc**. Program zastępuje kartkę i długopis, automatyzując liczenie punktów, pilnowanie zasad oraz prowadzenie statystyk graczy.

Aplikacja posiada interfejs graficzny oparty o bibliotekę **Qt (PySide6)** oraz wbudowaną bazę danych **SQLite**, dzięki czemu żadna rozgrywka nie zostanie utracona.

---

## 🚀 Główne Funkcje

### 🎮 Rozgrywka
* **Wsparcie dla wielu graczy:** Elastyczne dodawanie graczy (2-4 osoby).
* **Automatyczna matematyka:** Program sam zaokrągla punkty (zgodnie z zasadami Tysiąca) i sumuje wyniki.
* **Obsługa Meldunków:** Dedykowane przełączniki dla meldunków (40 ♠, 60 ♣, 80 ♦, 100 ♥) z walidacją (np. gracz nie może zgłosić dwóch meldunków w jednym kolorze w jednym rozdaniu).
* **Gra "Pod Deklarację":** Specjalny tryb, w którym wpisuje się zadeklarowaną kwotę. System automatycznie sprawdza, czy gracz "ugrał" (dodaje punkty) czy "wtopił" (odejmuje punkty).
* **Wskazywanie rozdającego:** Ikonka 🎴 automatycznie przesuwa się na kolejnego gracza co rundę.

### 💾 Baza Danych i Historia
* **Auto-zapis:** Każde rozdanie jest natychmiast zapisywane w lokalnej bazie `tysiac.db`.
* **Wznawianie gier:** Przerwałeś grę w połowie? Możesz ją wznowić w dowolnym momencie z menu "Wstrzymane Gry".
* **Pełne Archiwum:** Przeglądaj historię zakończonych meczów wraz ze szczegółowym raportem (kto, ile punktów, w której rundzie).

## 🏆 Statystyki i Rankingi
Aplikacja śledzi osiągnięcia graczy w czasie rzeczywistym:
* **Mistrzowie:** Ranking wygranych meczów.
* **Królowie Meldunków:** Kto najczęściej melduje.
* **Łowcy "Setek":** Kto najczęściej zgłasza meldunek 100 pkt (♥).

---

### 🛠️ Technologie

Projekt został stworzony w języku **Python** przy użyciu bibliotek:
* **GUI:** `PySide6` (Qt for Python) - zapewnia natywny wygląd i płynność działania.
* **Baza Danych:** `sqlite3` - lekka, bezserwerowa baza danych.

---

### 📥 Instalacja i Uruchomienie

## Wymagania
* Python 3.8 lub nowszy
* System: Linux / Windows / macOS

## Instrukcja krok po kroku

**1. Pobranie kodu**
```bash
git clone [https://github.com/KlapkiSzatana/TysiacManager.git](https://github.com/KlapkiSzatana/TysiacManager.git)
cd TysiacManager
```
**2. Przygotowanie środowiska**
**Linux / macOS**
```bash
python -m venv venv
source venv/bin/activate
```
**Windows**
```bash
python -m venv venv
venv\Scripts\activate
```
**3. Instalacja bibliotek**
```bash
pip install PySide6
```
**4. Uruchomienie aplikacji**
```bash
python tysiac.py
```
---

## 🏗️ Budowanie i Instalacja (Linux)

Aplikacja jest przystosowana do działania na systemach Linux (testowano na CachyOS oraz pop_OS). Projekt zawiera skrypt automatyzujący proces budowania samodzielnej paczki (standalone) przy użyciu **Nuitka**.

## 🚀 Opcja 1: Automatyczna budowa i instalacja (Zalecana)

Skrypt `build.sh` automatycznie:
1. Wykrywa wersję Pythona.
2. Tworzy środowisko wirtualne i pobiera zależności.
3. Kompiluje grę do wersji binarnej.
4. **(Opcjonalnie)** Instaluje grę w systemie (`/opt`), dodając skrót do menu aplikacji.

**Instrukcja:**

1. Nadaj uprawnienia do uruchamiania skryptu:
   ```bash
   chmod +x build.sh
   ```
   
2. Uruchom budowanie:
   ```
   ./build.sh
   ```
Postępuj zgodnie z instrukcjami w terminalu.

## ⚙️ Opcja 2: Budowanie ręczne

Jeśli wolisz pełną kontrolę nad procesem, wykonaj poniższe kroki w terminalu:

1. Przygotuj środowisko:
   Dla Ubuntu/Debian użyj python3, dla Arch użyj python
   ```bash
   python -m venv venv
   source venv/bin/activate
   pip install pyside6 nuitka zstandard
   ```
   
2. Skompiluj aplikację:
   ```bash
   python -m nuitka \
    --standalone \
    --enable-plugin=pyside6 \
    --include-data-file=tysiac.png=tysiac.png \
    --static-libpython=no \
    --output-dir=dist \
    --linux-icon=tysiac.png \
    --output-filename=TysiacManager \
    --remove-output \
    tysiac.py
    ```
3. Gotowa aplikacja pojawi się w folderze dist/TysiacManager.dist

---

## 📦 Instalacja z gotowej paczki (Linux)

1. Pobierz plik `.zip` lub `.tar.gz` z zakładki **Releases**.
2. Rozpakuj archiwum.
3. Wejdź do folderu i uruchom instalator:
   ```bash
   ./install.sh
   ```

## 🗑️ Odinstalowanie (Linux)

Jeśli zainstalowałeś w systemie używając skryptu `install.sh`, możesz ją łatwo usunąć.

## Metoda 1: Użycie skryptu (jeśli nadal masz folder pobrany z Releases)
W katalogu z aplikacją uruchom:
```bash
./uninstall.sh
```

##ℹ️ Ważne informacje

    Baza Danych: Niezależnie od sposobu instalacji, baza danych oraz logi są przechowywane w katalogu domowym użytkownika: ~/Tysiac_Manager/ (Dzięki temu nie są wymagane uprawnienia roota do zapisu wyników).

    Wymagania: Do poprawnego zbudowania aplikacji, w folderze głównym musi znajdować się plik ikony tysiac.png.


**Projekt jest rozwijany hobbystycznie metodą "AI-Assisted Development"**

©️ 2025 KlapkiSzatana. Projekt Open Source.
