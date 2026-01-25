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

### 🏆 Statystyki i Rankingi
Aplikacja śledzi osiągnięcia graczy w czasie rzeczywistym:
* **Mistrzowie:** Ranking wygranych meczów.
* **Królowie Meldunków:** Kto najczęściej melduje.
* **Łowcy "Setek":** Kto najczęściej zgłasza meldunek 100 pkt (♥).

---

## 🛠️ Technologie

Projekt został stworzony w języku **Python** przy użyciu bibliotek:
* **GUI:** `PySide6` (Qt for Python) - zapewnia natywny wygląd i płynność działania.
* **Baza Danych:** `sqlite3` - lekka, bezserwerowa baza danych.

---

## 📥 Instalacja i Uruchomienie

### Wymagania
* Python 3.8 lub nowszy
* System: Linux / Windows / macOS

### Instrukcja krok po kroku

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

**Projekt jest rozwijany hobbystycznie metodą "AI-Assisted Development"**

©️ 2025 KlapkiSzatana. Projekt Open Source.
