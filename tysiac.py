import sys
import sqlite3
import random
import os
from pathlib import Path
from datetime import datetime
from PySide6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout,
                               QHBoxLayout, QLabel, QLineEdit, QPushButton,
                               QTreeWidget, QTreeWidgetItem, QMessageBox,
                               QComboBox, QGroupBox, QGridLayout, QCheckBox,
                               QTabWidget, QScrollArea, QStackedWidget, QHeaderView,
                               QDialog, QFrame, QStatusBar)
from PySide6.QtCore import Qt, QRegularExpression, QSize
from PySide6.QtGui import QFont, QColor, QRegularExpressionValidator, QIcon

basedir = os.path.dirname(__file__)
icon_path = os.path.join(basedir, "tysiac.png")
# --- KONFIGURACJA APLIKACJI ---
APP_VERSION = "0.9.1"

try:
    import qdarktheme
    HAS_THEME = True
except ImportError:
    HAS_THEME = False

# ==========================================
# BAZA DANYCH
# ==========================================
class TysiacDB:
    def __init__(self, db_name="tysiac.db"):
        user_dir = os.path.expanduser("~/Tysiac_Manager")
        Path(user_dir).mkdir(parents=True, exist_ok=True)
        self.db_path = os.path.join(user_dir, db_name)
        self.conn = sqlite3.connect(self.db_path)
        self.create_tables()
        self.update_schema()

    def create_tables(self):
        cursor = self.conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS matches (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date TEXT,
                winner TEXT,
                status TEXT DEFAULT 'finished',
                initial_dealer_offset INTEGER DEFAULT 0
            )
        ''')
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS rounds (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                match_id INTEGER,
                round_number INTEGER,
                player_name TEXT,
                score_change INTEGER,
                meld_40 INTEGER DEFAULT 0,
                meld_60 INTEGER DEFAULT 0,
                meld_80 INTEGER DEFAULT 0,
                meld_100 INTEGER DEFAULT 0,
                is_declaration INTEGER DEFAULT 0,
                declared_points INTEGER DEFAULT 0,
                FOREIGN KEY(match_id) REFERENCES matches(id)
            )
        ''')
        self.conn.commit()

    def update_schema(self):
        cursor = self.conn.cursor()
        # Aktualizacja dla starych baz danych
        try:
            cursor.execute("SELECT status FROM matches LIMIT 1")
        except sqlite3.OperationalError:
            cursor.execute("ALTER TABLE matches ADD COLUMN status TEXT DEFAULT 'finished'")

        try:
            cursor.execute("SELECT initial_dealer_offset FROM matches LIMIT 1")
        except sqlite3.OperationalError:
            cursor.execute("ALTER TABLE matches ADD COLUMN initial_dealer_offset INTEGER DEFAULT 0")

        # Kolumny meldunków
        try:
            cursor.execute("SELECT meld_40 FROM rounds LIMIT 1")
        except sqlite3.OperationalError:
            cursor.execute("ALTER TABLE rounds ADD COLUMN meld_40 INTEGER DEFAULT 0")
            cursor.execute("ALTER TABLE rounds ADD COLUMN meld_60 INTEGER DEFAULT 0")
            cursor.execute("ALTER TABLE rounds ADD COLUMN meld_80 INTEGER DEFAULT 0")
            cursor.execute("ALTER TABLE rounds ADD COLUMN meld_100 INTEGER DEFAULT 0")

        # NOWE KOLUMNY: DEKLARACJA
        try:
            cursor.execute("SELECT is_declaration FROM rounds LIMIT 1")
        except sqlite3.OperationalError:
            cursor.execute("ALTER TABLE rounds ADD COLUMN is_declaration INTEGER DEFAULT 0")
            cursor.execute("ALTER TABLE rounds ADD COLUMN declared_points INTEGER DEFAULT 0")

        self.conn.commit()

    def save_or_update_game(self, match_id, winner, game_log, status="finished", dealer_offset=0):
        cursor = self.conn.cursor()
        date_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        if match_id is None:
            cursor.execute("INSERT INTO matches (date, winner, status, initial_dealer_offset) VALUES (?, ?, ?, ?)",
                           (date_str, winner, status, dealer_offset))
            match_id = cursor.lastrowid
        else:
            cursor.execute("UPDATE matches SET winner = ?, status = ?, date = ?, initial_dealer_offset = ? WHERE id = ?",
                           (winner, status, date_str, dealer_offset, match_id))
            cursor.execute("DELETE FROM rounds WHERE match_id = ?", (match_id,))

        for log in game_log:
            m = log.get('melds', {'40':0, '60':0, '80':0, '100':0})
            # Obsługa zapisu deklaracji
            is_decl = log.get('is_declaration', 0)
            decl_pts = log.get('declared_points', 0)

            cursor.execute("""
                INSERT INTO rounds (match_id, round_number, player_name, score_change,
                                    meld_40, meld_60, meld_80, meld_100,
                                    is_declaration, declared_points)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (match_id, log['round'], log['player'], log['score'],
                  m['40'], m['60'], m['80'], m['100'],
                  is_decl, decl_pts))

        self.conn.commit()
        return match_id

    def force_finish_match(self, match_id, winner):
        cursor = self.conn.cursor()
        date_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        cursor.execute("UPDATE matches SET winner = ?, status = 'finished', date = ? WHERE id = ?",
                       (winner, date_str, match_id))
        self.conn.commit()

    def delete_match(self, match_id):
        cursor = self.conn.cursor()
        cursor.execute("DELETE FROM rounds WHERE match_id = ?", (match_id,))
        cursor.execute("DELETE FROM matches WHERE id = ?", (match_id,))
        self.conn.commit()

    def get_history(self):
        cursor = self.conn.cursor()
        cursor.execute("SELECT id, date, winner FROM matches WHERE status = 'finished' ORDER BY id DESC")
        return cursor.fetchall()

    def get_top_wins(self):
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT winner, COUNT(*) as wins
            FROM matches
            WHERE status = 'finished' AND winner IS NOT NULL
            GROUP BY winner
            ORDER BY wins DESC LIMIT 5
        """)
        return cursor.fetchall()

    def get_top_total_melds(self):
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT player_name, SUM(meld_40 + meld_60 + meld_80 + meld_100) as total
            FROM rounds
            GROUP BY player_name
            ORDER BY total DESC LIMIT 5
        """)
        return cursor.fetchall()

    def get_top_100_melds(self):
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT player_name, SUM(meld_100) as cnt
            FROM rounds
            GROUP BY player_name
            ORDER BY cnt DESC LIMIT 5
        """)
        return cursor.fetchall()

    def get_paused_games_summary(self):
        cursor = self.conn.cursor()
        cursor.execute("SELECT id, date FROM matches WHERE status = 'paused' ORDER BY id DESC")
        paused_matches = cursor.fetchall()
        results = []
        for mid, mdate in paused_matches:
            cursor.execute("SELECT player_name, SUM(score_change) FROM rounds WHERE match_id = ? GROUP BY player_name", (mid,))
            scores = cursor.fetchall()
            score_str = ", ".join([f"{name}: {pts}" for name, pts in scores])
            results.append((mid, mdate, score_str))
        return results

    def get_match_metadata(self, match_id):
        cursor = self.conn.cursor()
        cursor.execute("SELECT initial_dealer_offset FROM matches WHERE id = ?", (match_id,))
        res = cursor.fetchone()
        if res: return {'dealer_offset': res[0]}
        return {'dealer_offset': 0}

    def get_match_details(self, match_id):
        cursor = self.conn.cursor()
        # Pobieramy też nowe pola
        cursor.execute("""
            SELECT round_number, player_name, score_change, meld_40, meld_60, meld_80, meld_100, is_declaration, declared_points
            FROM rounds
            WHERE match_id = ?
            ORDER BY round_number ASC
        """, (match_id,))
        return cursor.fetchall()

    def get_all_player_names(self):
        cursor = self.conn.cursor()
        cursor.execute("SELECT DISTINCT player_name FROM rounds ORDER BY player_name")
        return [row[0] for row in cursor.fetchall()]

# ==========================================
# OKNO DIALOGOWE: WSTRZYMANE GRY
# ==========================================
class PausedGamesDialog(QDialog):
    def __init__(self, parent, db, main_window):
        super().__init__(parent)
        self.db = db
        self.main_window = main_window
        self.setWindowTitle("Wstrzymane Gry")
        self.resize(700, 450)

        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("Wybierz grę, aby ją dokończyć:"))

        self.tree = QTreeWidget()
        self.tree.setHeaderLabels(["ID", "Data", "Stan Gry"])
        self.tree.setColumnHidden(0, True)
        self.tree.header().setSectionResizeMode(2, QHeaderView.Stretch)
        self.tree.itemDoubleClicked.connect(self.resume_selected)
        layout.addWidget(self.tree)

        btn_layout = QHBoxLayout()
        btn_resume = QPushButton("▶ Wznów Grę")
        btn_resume.clicked.connect(self.resume_selected)
        btn_resume.setStyleSheet("font-weight: bold; background-color: #2e7d32; color: white; padding: 5px;")

        btn_finish = QPushButton("🏁 Zakończ / Usuń")
        btn_finish.clicked.connect(self.finish_selected)

        btn_close = QPushButton("Zamknij")
        btn_close.clicked.connect(self.close)

        btn_layout.addWidget(btn_resume)
        btn_layout.addWidget(btn_finish)
        btn_layout.addWidget(btn_close)
        layout.addLayout(btn_layout)

        self.refresh_list()

    def refresh_list(self):
        self.tree.clear()
        paused = self.db.get_paused_games_summary()
        for pid, date, status in paused:
            self.tree.addTopLevelItem(QTreeWidgetItem([str(pid), date, status]))

    def resume_selected(self):
        item = self.tree.currentItem()
        if not item: return
        match_id = int(item.text(0))

        details = self.db.get_match_details(match_id)
        meta = self.db.get_match_metadata(match_id)
        if not details: return

        game_log = []
        players = set()
        for row in details:
            # row: 0=rnd, 1=name, 2=score, 3=m40, 4=m60, 5=m80, 6=m100, 7=is_decl, 8=decl_pts
            players.add(row[1])
            is_decl = 0
            decl_pts = 0
            if len(row) > 7:
                is_decl = row[7]
                decl_pts = row[8]

            game_log.append({
                'round': row[0], 'player': row[1], 'score': row[2],
                'melds': {'40': row[3], '60': row[4], '80': row[5], '100': row[6]},
                'is_declaration': is_decl,
                'declared_points': decl_pts
            })
        player_names = sorted(list(players))

        self.main_window.resume_game(player_names, match_id, game_log, dealer_offset=meta['dealer_offset'])
        self.close()

    def finish_selected(self):
        item = self.tree.currentItem()
        if not item: return
        match_id = int(item.text(0))

        details = self.db.get_match_details(match_id)
        total_abs_score = sum([abs(row[2]) for row in details])

        if total_abs_score == 0:
            if QMessageBox.question(self, "Porzucić?", "Ta gra ma zerowy wynik. Czy usunąć ją trwale?",
                                    QMessageBox.Yes | QMessageBox.No) == QMessageBox.Yes:
                self.db.delete_match(match_id)
                self.refresh_list()
            return

        scores = {}
        for row in details: scores[row[1]] = scores.get(row[1], 0) + row[2]
        winner = max(scores, key=scores.get)
        max_s = scores[winner]

        if QMessageBox.question(self, "Zakończyć?", f"Lider: {winner} ({max_s} pkt).\nZakończyć i przenieść do archiwum?",
                                QMessageBox.Yes | QMessageBox.No) == QMessageBox.Yes:
            self.db.force_finish_match(match_id, winner)
            QMessageBox.information(self, "Sukces", f"Gra zakończona. Zwycięzca: {winner}")
            self.refresh_list()
            self.main_window.menu_widget.refresh_data()


# ==========================================
# INTERFEJS GRAFICZNY (PySide6)
# ==========================================

class PlayerInputWidget(QGroupBox):
    def __init__(self, player_name, parent_game):
        super().__init__(player_name)
        self.parent_game = parent_game
        self.player_name = player_name

        layout = QVBoxLayout()
        layout.setSpacing(10)

        # --- SEKCJA PUNKTÓW Z KART ---
        self.score_input = QLineEdit()
        self.score_input.setPlaceholderText("Pkt z kart")
        self.score_input.setToolTip("Wpisz punkty z kart (bez meldunków)")
        self.score_input.setAlignment(Qt.AlignCenter)
        self.score_input.setMinimumHeight(50)
        self.score_input.setFont(QFont("Arial", 20, QFont.Weight.Bold))

        regex = QRegularExpression(r"^-?\d{0,3}$")
        validator = QRegularExpressionValidator(regex, self.score_input)
        self.score_input.setValidator(validator)
        self.score_input.returnPressed.connect(self.parent_game.process_round)

        layout.addWidget(self.score_input)

        # --- SEKCJA MELDUNKÓW ---
        grid_melds = QGridLayout()
        red_style = "QCheckBox { color: #d32f2f; font-weight: bold; font-size: 14px; }"
        black_style = "QCheckBox { font-weight: bold; font-size: 14px; }"

        self.cb_40 = QCheckBox("40 ♠")
        self.cb_40.setStyleSheet(black_style)
        self.cb_60 = QCheckBox("60 ♣")
        self.cb_60.setStyleSheet(black_style)
        self.cb_80 = QCheckBox("80 ♦")
        self.cb_80.setStyleSheet(red_style)
        self.cb_100 = QCheckBox("100 ♥")
        self.cb_100.setStyleSheet(red_style)

        # --- ZMIANA: TAB IGNORUJE CHECKBOXY (tylko myszka) ---
        self.cb_40.setFocusPolicy(Qt.ClickFocus)
        self.cb_60.setFocusPolicy(Qt.ClickFocus)
        self.cb_80.setFocusPolicy(Qt.ClickFocus)
        self.cb_100.setFocusPolicy(Qt.ClickFocus)

        # Logika blokowania meldunków
        self.cb_40.stateChanged.connect(self.parent_game.update_meld_constraints)
        self.cb_60.stateChanged.connect(self.parent_game.update_meld_constraints)
        self.cb_80.stateChanged.connect(self.parent_game.update_meld_constraints)
        self.cb_100.stateChanged.connect(self.parent_game.update_meld_constraints)

        grid_melds.addWidget(self.cb_40, 0, 0)
        grid_melds.addWidget(self.cb_60, 0, 1)
        grid_melds.addWidget(self.cb_80, 1, 0)
        grid_melds.addWidget(self.cb_100, 1, 1)
        layout.addLayout(grid_melds)

        # --- NOWA SEKCJA: DEKLARACJA ---
        decl_frame = QFrame()
        decl_frame.setFrameShape(QFrame.StyledPanel)
        decl_frame.setStyleSheet("QFrame { border: 1px dashed #aaa; border-radius: 4px; padding: 2px; }")
        decl_layout = QVBoxLayout(decl_frame)
        decl_layout.setContentsMargins(2, 2, 2, 2)

        self.cb_declare = QCheckBox("Gra pod deklarację?")
        self.cb_declare.setStyleSheet("font-size: 12px; color: #1565C0; font-weight: bold;")
        self.cb_declare.clicked.connect(self.handle_checkbox_click)
        # To też ignorujemy TABem
        self.cb_declare.setFocusPolicy(Qt.ClickFocus)

        self.input_declare = QLineEdit()
        self.input_declare.setPlaceholderText("Ile? (np. 150)")
        self.input_declare.setAlignment(Qt.AlignCenter)
        self.input_declare.setEnabled(False)
        self.input_declare.setFont(QFont("Arial", 12))

        reg_decl = QRegularExpression(r"^\d{0,3}$")
        val_decl = QRegularExpressionValidator(reg_decl, self.input_declare)
        self.input_declare.setValidator(val_decl)

        decl_layout.addWidget(self.cb_declare)
        decl_layout.addWidget(self.input_declare)

        layout.addWidget(decl_frame)
        self.setLayout(layout)

    def handle_checkbox_click(self):
        self.parent_game.handle_exclusive_declaration(self)
        self.toggle_declaration_input()

    def toggle_declaration_input(self):
        if self.cb_declare.isChecked():
            self.input_declare.setEnabled(True)
            self.input_declare.setFocus()
        else:
            self.input_declare.setEnabled(False)
            self.input_declare.clear()
            self.input_declare.setStyleSheet("")

    def get_data(self):
        text = self.score_input.text().strip()
        try:
            if not text or text == "-": points_cards = 0
            else: points_cards = int(text)
        except ValueError: points_cards = 0

        melds = {
            '40': 1 if self.cb_40.isChecked() else 0,
            '60': 1 if self.cb_60.isChecked() else 0,
            '80': 1 if self.cb_80.isChecked() else 0,
            '100': 1 if self.cb_100.isChecked() else 0,
        }

        is_declaring = self.cb_declare.isChecked()
        try:
            decl_val = int(self.input_declare.text()) if self.input_declare.text() else 0
        except ValueError:
            decl_val = 0

        return points_cards, melds, is_declaring, decl_val

    def clear_data(self):
        self.score_input.clear()
        self.cb_40.setChecked(False)
        self.cb_60.setChecked(False)
        self.cb_80.setChecked(False)
        self.cb_100.setChecked(False)
        self.cb_declare.setChecked(False)
        self.toggle_declaration_input()

class GameWidget(QWidget):
    # ... __init__ i setup_ui BEZ ZMIAN ...
    def __init__(self, main_window, db):
        super().__init__()
        self.main_window = main_window
        self.db = db
        self.players_data = []
        self.round_number = 1
        self.game_log = []
        self.current_match_id = None
        self.dealer_offset = 0
        self.input_widgets = []
        self.setup_ui()

    def setup_ui(self):
        # ... (kod setup_ui taki sam jak wcześniej) ...
        layout = QVBoxLayout(self)
        self.lbl_round = QLabel("Rozdanie: 1")
        self.lbl_round.setFont(QFont("Arial", 26, QFont.Weight.Bold))
        self.lbl_round.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.lbl_round)
        self.scores_layout = QHBoxLayout()
        layout.addLayout(self.scores_layout)
        gb_input = QGroupBox("Wyniki tego rozdania")
        self.input_layout = QHBoxLayout()
        gb_input.setLayout(self.input_layout)
        layout.addWidget(gb_input)
        btn_layout = QHBoxLayout()
        self.btn_submit = QPushButton("ZATWIERDŹ ROZDANIE")
        self.btn_submit.setMinimumHeight(60)
        self.btn_submit.setFont(QFont("Arial", 22, QFont.Weight.Bold))
        self.btn_submit.clicked.connect(self.process_round)
        self.btn_submit.setStyleSheet("background-color: #2e7d32; color: white;")
        btn_pause = QPushButton("⏸ Wstrzymaj (Menu)")
        btn_pause.clicked.connect(self.pause_game)
        btn_stop = QPushButton("🛑 Zakończ (Zwycięzca)")
        btn_stop.clicked.connect(self.force_stop_game)
        btn_layout.addWidget(btn_pause)
        btn_layout.addWidget(self.btn_submit)
        btn_layout.addWidget(btn_stop)
        layout.addLayout(btn_layout)
        layout.addWidget(QLabel("Historia (na bieżąco):"))
        self.history_tree = QTreeWidget()
        self.history_tree.setHeaderLabels(["Kol."])
        self.history_tree.setStyleSheet("""
            QTreeWidget { font-size: 16px; font-weight: bold; }
            QTreeWidget::item { padding-top: 5px; padding-bottom: 5px; height: 35px; }
            QHeaderView::section { font-size: 16px; font-weight: bold; padding: 5px; }
        """)
        header = self.history_tree.header()
        header.setSectionResizeMode(QHeaderView.Stretch)
        header.setSectionResizeMode(0, QHeaderView.Fixed)
        self.history_tree.setColumnWidth(0, 70)
        header.setDefaultAlignment(Qt.AlignCenter)
        layout.addWidget(self.history_tree)

    def initialize_game(self, player_names, match_id=None, existing_log=None, dealer_offset=0):
        for i in reversed(range(self.scores_layout.count())):
            self.scores_layout.itemAt(i).widget().setParent(None)
        for i in reversed(range(self.input_layout.count())):
            self.input_layout.itemAt(i).widget().setParent(None)
        self.history_tree.clear()

        self.current_match_id = match_id
        self.dealer_offset = dealer_offset
        self.players_data = []
        self.input_widgets = []

        cols = ["Kol."] + player_names
        self.history_tree.setColumnCount(len(cols))
        self.history_tree.setHeaderLabels(cols)

        header = self.history_tree.header()
        header.setSectionResizeMode(QHeaderView.Stretch)
        header.setSectionResizeMode(0, QHeaderView.Fixed)
        self.history_tree.setColumnWidth(0, 70)

        # Tworzenie widgetów graczy
        for name in player_names:
            score_card = QGroupBox()
            score_card.setStyleSheet("QGroupBox { border: 2px solid gray; border-radius: 5px; margin-top: 1ex; } QGroupBox::title { subcontrol-origin: margin; subcontrol-position: top center; padding: 0 3px; }")
            vbox = QVBoxLayout()
            lbl_name = QLabel(name)
            lbl_name.setStyleSheet("font-size: 22px; font-weight: bold;")
            lbl_name.setAlignment(Qt.AlignCenter)
            lbl_name.setProperty("role", "name_label")
            lbl_score = QLabel("0")
            lbl_score.setStyleSheet("font-size: 70px; font-weight: bold; color: #2196F3;")
            lbl_score.setAlignment(Qt.AlignCenter)
            lbl_status = QLabel("")
            lbl_status.setFont(QFont("Arial", 12, italic=True))
            lbl_status.setAlignment(Qt.AlignCenter)
            lbl_status.setStyleSheet("color: #F44336;")
            vbox.addWidget(lbl_name)
            vbox.addWidget(lbl_score)
            vbox.addWidget(lbl_status)
            score_card.setLayout(vbox)
            self.scores_layout.addWidget(score_card)

            self.players_data.append({
                'name': name, 'score': 0, 'lbl_name': lbl_name, 'lbl_score': lbl_score,
                'lbl_status': lbl_status, 'card_widget': score_card
            })

            inp = PlayerInputWidget(name, self)
            self.input_layout.addWidget(inp)
            self.input_widgets.append(inp)

        # --- ZMIANA: RĘCZNE USTAWIANIE KOLEJNOŚCI TABULACJI ---
        # Łączymy inputy jeden po drugim
        for i in range(len(self.input_widgets) - 1):
            QWidget.setTabOrder(self.input_widgets[i].score_input, self.input_widgets[i+1].score_input)

        # Ostatni input prowadzi do przycisku ZATWIERDŹ
        if self.input_widgets:
            QWidget.setTabOrder(self.input_widgets[-1].score_input, self.btn_submit)

        if existing_log:
            self.game_log = []
            players_map = {p['name']: p for p in self.players_data}
            max_round = 0
            rounds_map = {}
            for entry in existing_log:
                r = entry['round']
                if r not in rounds_map: rounds_map[r] = {}
                rounds_map[r][entry['player']] = entry
                players_map[entry['player']]['score'] += entry['score']
                if r > max_round: max_round = r
            self.round_number = max_round + 1
            self.game_log = existing_log
            for r in sorted(rounds_map.keys()):
                row_data = [str(r)]
                for p in self.players_data:
                    if p['name'] in rounds_map[r]: row_data.append(str(rounds_map[r][p['name']]['score']))
                    else: row_data.append("0")
                item = QTreeWidgetItem(row_data)
                for i in range(len(row_data)):
                    item.setTextAlignment(i, Qt.AlignCenter)
                self.history_tree.addTopLevelItem(item)
        else:
            self.round_number = 1
            self.game_log = []

        self.update_visuals()
        if self.input_widgets: self.input_widgets[0].score_input.setFocus()

    # ... RESZTA METOD (update_meld_constraints, process_round itp.) BEZ ZMIAN ...
    def update_meld_constraints(self):
        holders = {'40': None, '60': None, '80': None, '100': None}
        for inp in self.input_widgets:
            if inp.cb_40.isChecked(): holders['40'] = inp
            if inp.cb_60.isChecked(): holders['60'] = inp
            if inp.cb_80.isChecked(): holders['80'] = inp
            if inp.cb_100.isChecked(): holders['100'] = inp
        for inp in self.input_widgets:
            if holders['40'] is not None and holders['40'] != inp:
                inp.cb_40.setEnabled(False); inp.cb_40.setChecked(False)
            else: inp.cb_40.setEnabled(True)
            if holders['60'] is not None and holders['60'] != inp:
                inp.cb_60.setEnabled(False); inp.cb_60.setChecked(False)
            else: inp.cb_60.setEnabled(True)
            if holders['80'] is not None and holders['80'] != inp:
                inp.cb_80.setEnabled(False); inp.cb_80.setChecked(False)
            else: inp.cb_80.setEnabled(True)
            if holders['100'] is not None and holders['100'] != inp:
                inp.cb_100.setEnabled(False); inp.cb_100.setChecked(False)
            else: inp.cb_100.setEnabled(True)

    def handle_exclusive_declaration(self, sender_widget):
        for inp in self.input_widgets:
            if inp != sender_widget:
                inp.cb_declare.setChecked(False)
                inp.toggle_declaration_input()

    def update_visuals(self):
        self.lbl_round.setText(f"Rozdanie: {self.round_number}")
        dealer_idx = (self.round_number - 1 + self.dealer_offset) % len(self.players_data)
        for i, p in enumerate(self.players_data):
            if i == dealer_idx:
                p['lbl_name'].setText(f"🎴 {p['name']} (Rozdaje)")
                p['card_widget'].setStyleSheet("""
                    QGroupBox { border: 2px solid #FFD700; background-color: rgba(255, 215, 0, 0.1);
                        border-radius: 5px; margin-top: 1ex; }
                """)
            else:
                p['lbl_name'].setText(p['name'])
                p['card_widget'].setStyleSheet("QGroupBox { border: 2px solid gray; border-radius: 5px; margin-top: 1ex; }")
            p['lbl_score'].setText(str(p['score']))
            if p['score'] >= 800:
                p['lbl_score'].setStyleSheet("font-size: 70px; font-weight: bold; color: #F44336;")
                p['lbl_status'].setText("(Pod kreską!)")
            else:
                p['lbl_score'].setStyleSheet("font-size: 70px; font-weight: bold; color: #2196F3;")
                p['lbl_status'].setText("")
        self.history_tree.scrollToBottom()

    def round_points(self, points):
        if points < 0: return points
        return ((points + 5) // 10) * 10

    def process_round(self):
        round_data_list = []
        for i, inp in enumerate(self.input_widgets):
            pts, melds, is_decl, decl_val = inp.get_data()
            round_data_list.append({
                'pts_cards_raw': pts,
                'melds': melds,
                'is_declaring': is_decl,
                'decl_val': decl_val
            })

        total_input_score = sum(d['pts_cards_raw'] for d in round_data_list)
        total_melds_active = sum(1 for d in round_data_list for m in d['melds'].values() if m)
        if total_input_score == 0 and total_melds_active == 0 and not any(d['is_declaring'] for d in round_data_list):
             if QMessageBox.question(self, "Puste rozdanie?",
                                     "Wszyscy mają 0 punktów. Czy na pewno chcesz zapisać takie rozdanie?",
                                     QMessageBox.Yes | QMessageBox.No) == QMessageBox.No:
                 return

        winner_found = None
        hist_row = [str(self.round_number)]
        for idx, data in enumerate(round_data_list):
            p_data = self.players_data[idx]
            meld_points = 0
            if data['melds']['40']: meld_points += 40
            if data['melds']['60']: meld_points += 60
            if data['melds']['80']: meld_points += 80
            if data['melds']['100']: meld_points += 100
            final_score_change = 0
            if data['is_declaring']:
                ugrane_dokladnie = data['pts_cards_raw'] + meld_points
                if ugrane_dokladnie >= data['decl_val']:
                    final_score_change = data['decl_val']
                else:
                    final_score_change = -data['decl_val']
            else:
                pts_rounded = self.round_points(data['pts_cards_raw'])
                ugrane_lacznie = pts_rounded + meld_points
                final_score_change = ugrane_lacznie
            p_data['score'] += final_score_change
            hist_row.append(str(final_score_change))
            self.game_log.append({
                'round': self.round_number,
                'player': p_data['name'],
                'score': final_score_change,
                'melds': data['melds'],
                'is_declaration': 1 if data['is_declaring'] else 0,
                'declared_points': data['decl_val']
            })
            if p_data['score'] >= 1000: winner_found = p_data['name']
            self.input_widgets[idx].clear_data()

        item = QTreeWidgetItem(hist_row)
        for i in range(len(hist_row)):
            item.setTextAlignment(i, Qt.AlignCenter)
        self.history_tree.addTopLevelItem(item)
        self.current_match_id = self.db.save_or_update_game(
            self.current_match_id, None, self.game_log, status="paused", dealer_offset=self.dealer_offset
        )
        if winner_found:
            self.update_visuals()
            self.end_game(winner_found)
        else:
            self.round_number += 1
            self.update_visuals()
            if self.input_widgets: self.input_widgets[0].score_input.setFocus()

    def has_any_points(self):
        for p in self.players_data:
            if p['score'] != 0: return True
        return False

    def pause_game(self):
        if not self.has_any_points():
            if QMessageBox.question(self, "Porzucić?", "Gra ma zerowy wynik. Czy usunąć ją?",
                                    QMessageBox.Yes | QMessageBox.No) == QMessageBox.Yes:
                if self.current_match_id: self.db.delete_match(self.current_match_id)
                self.main_window.show_menu()
            return
        if QMessageBox.question(self, "Wstrzymaj", "Zapisać i wrócić do menu?",
                                QMessageBox.Yes | QMessageBox.No) == QMessageBox.Yes:
            self.db.save_or_update_game(self.current_match_id, None, self.game_log, status="paused", dealer_offset=self.dealer_offset)
            self.main_window.show_menu()

    def force_stop_game(self):
        if not self.has_any_points():
            if QMessageBox.question(self, "Porzucić?", "Brak punktów. Porzucić grę?",
                                    QMessageBox.Yes | QMessageBox.No) == QMessageBox.Yes:
                if self.current_match_id: self.db.delete_match(self.current_match_id)
                self.main_window.show_menu()
            return
        if QMessageBox.question(self, "Zakończ", "Zakończyć grę teraz?",
                                QMessageBox.Yes | QMessageBox.No) == QMessageBox.Yes:
            winner = max(self.players_data, key=lambda p: p['score'])
            self.end_game(winner['name'])

    def end_game(self, winner_name):
        self.db.save_or_update_game(self.current_match_id, winner_name, self.game_log, status="finished", dealer_offset=self.dealer_offset)
        msg = QMessageBox()
        msg.setWindowTitle("Koniec Gry")
        msg.setText(f"Gratulacje! Wygrał gracz: {winner_name} 🏆")
        msg.setInformativeText("Czy chcesz zagrać REWANŻ w tym samym składzie?")
        msg.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
        if msg.exec() == QMessageBox.Yes:
            names = [p['name'] for p in self.players_data]
            new_offset = random.randint(0, len(names) - 1)
            self.initialize_game(names, match_id=None, existing_log=None, dealer_offset=new_offset)
        else:
            self.main_window.show_menu()


class MenuWidget(QWidget):
    def __init__(self, main_window, db):
        super().__init__()
        self.main_window = main_window
        self.db = db
        self.setup_ui()

    def setup_ui(self):
        main_layout = QVBoxLayout(self)

        gb_new = QGroupBox()
        gb_new_layout = QVBoxLayout()

        lbl_new_game = QLabel("Rozpocznij Nową Grę")
        lbl_new_game.setAlignment(Qt.AlignCenter)
        lbl_new_game.setFont(QFont("Arial", 14, QFont.Weight.Bold))
        gb_new_layout.addWidget(lbl_new_game)

        self.player_inputs_layout = QHBoxLayout()
        self.player_combos = []
        for i in range(3): self.add_player_field()
        gb_new_layout.addLayout(self.player_inputs_layout)

        btn_row = QHBoxLayout()
        btn_add = QPushButton("Dodaj gracza (+)")
        btn_add.clicked.connect(self.add_player_field)

        btn_start = QPushButton("🚀 START NOWEJ GRY")
        btn_start.setMinimumHeight(50)
        btn_start.setFont(QFont("Arial", 16, QFont.Weight.Bold))
        btn_start.setStyleSheet("background-color: #1976D2; color: white;")
        btn_start.clicked.connect(self.start_new_game)

        btn_paused = QPushButton("⏸ Wstrzymane Gry")
        btn_paused.clicked.connect(self.show_paused_games_dialog)

        btn_row.addWidget(btn_add)
        btn_row.addWidget(btn_start)
        btn_row.addWidget(btn_paused)
        gb_new_layout.addLayout(btn_row)

        gb_new.setLayout(gb_new_layout)
        main_layout.addWidget(gb_new)

        split_layout = QHBoxLayout()

        left_container = QWidget()
        left_layout = QVBoxLayout(left_container)

        lbl_ranking = QLabel("🏆 Ranking")
        lbl_ranking.setAlignment(Qt.AlignCenter)
        lbl_ranking.setFont(QFont("Arial", 14, QFont.Weight.Bold))
        left_layout.addWidget(lbl_ranking)

        gb_leaders = QGroupBox()
        gb_leaders.setMinimumWidth(350)

        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_content = QWidget()
        scroll_layout = QVBoxLayout(scroll_content)

        style_rank = """
            QTreeWidget { font-size: 13px; }
            QTreeWidget::item { padding: 3px; }
        """

        self.tree_wins = QTreeWidget()
        self.tree_wins.setStyleSheet(style_rank)
        self.setup_leaderboard_tree(self.tree_wins, "Wygrane")
        self.tree_wins.setFixedHeight(150)

        lbl_wins = QLabel("<b>Mistrzowie (Wygrane)</b>")
        lbl_wins.setAlignment(Qt.AlignCenter)
        lbl_wins.setFont(QFont("Arial", 12))
        scroll_layout.addWidget(lbl_wins)
        scroll_layout.addWidget(self.tree_wins)

        self.tree_melds = QTreeWidget()
        self.tree_melds.setStyleSheet(style_rank)
        self.setup_leaderboard_tree(self.tree_melds, "Meld. (♠♣♦♥)")
        self.tree_melds.setFixedHeight(150)

        lbl_melds = QLabel("<b>Królowie Meldunków</b>")
        lbl_melds.setAlignment(Qt.AlignCenter)
        lbl_melds.setFont(QFont("Arial", 12))
        scroll_layout.addWidget(lbl_melds)
        scroll_layout.addWidget(self.tree_melds)

        self.tree_100 = QTreeWidget()
        self.tree_100.setStyleSheet(style_rank)
        self.setup_leaderboard_tree(self.tree_100, "Ilość 100 ♥")
        self.tree_100.setFixedHeight(150)

        lbl_100 = QLabel("<b>Łowcy Meldunku '100'</b>")
        lbl_100.setAlignment(Qt.AlignCenter)
        lbl_100.setFont(QFont("Arial", 12))
        scroll_layout.addWidget(lbl_100)
        scroll_layout.addWidget(self.tree_100)

        scroll_layout.addStretch()
        scroll_area.setWidget(scroll_content)

        gb_leaders_layout = QVBoxLayout()
        gb_leaders_layout.addWidget(scroll_area)
        gb_leaders.setLayout(gb_leaders_layout)

        left_layout.addWidget(gb_leaders)
        split_layout.addWidget(left_container, 1)

        right_container = QWidget()
        right_layout = QVBoxLayout(right_container)

        lbl_archive = QLabel("🗄️ Ostatnie Gry (Archiwum)")
        lbl_archive.setAlignment(Qt.AlignCenter)
        lbl_archive.setFont(QFont("Arial", 14, QFont.Weight.Bold))
        right_layout.addWidget(lbl_archive)

        gb_archive = QGroupBox()
        gb_archive.setMinimumWidth(350)
        archive_layout = QVBoxLayout()
        self.tree_archive = QTreeWidget()
        self.tree_archive.setHeaderLabels(["ID", "Data", "Zwycięzca"])
        self.tree_archive.setColumnHidden(0, True)
        self.tree_archive.setColumnWidth(1, 160)
        self.tree_archive.header().setSectionResizeMode(2, QHeaderView.Stretch)
        self.tree_archive.itemDoubleClicked.connect(self.open_archive_details)
        archive_layout.addWidget(self.tree_archive)

        btn_details = QPushButton("Pokaż szczegóły (Raport)")
        btn_details.setFont(QFont("Arial", 11, QFont.Weight.Bold))
        btn_details.clicked.connect(self.open_archive_details)
        archive_layout.addWidget(btn_details)

        gb_archive.setLayout(archive_layout)
        right_layout.addWidget(gb_archive)
        split_layout.addWidget(right_container, 1)

        main_layout.addLayout(split_layout)

    def setup_leaderboard_tree(self, tree, score_col):
        tree.setHeaderLabels(["Poz", "Gracz", score_col])
        tree.setColumnWidth(0, 40)
        tree.setColumnWidth(2, 80)
        tree.header().setSectionResizeMode(1, QHeaderView.Stretch)

    def add_player_field(self):
        if len(self.player_combos) >= 4: return
        combo = QComboBox()
        combo.setEditable(True)
        combo.setPlaceholderText(f"Imię {len(self.player_combos)+1}")
        self.player_combos.append(combo)
        self.player_inputs_layout.addWidget(combo)
        self.refresh_combo_suggestions()

    def refresh_data(self):
        known_players = self.db.get_all_player_names()
        for cb in self.player_combos:
            current = cb.currentText()
            cb.clear()
            cb.addItems(known_players)
            cb.setCurrentText(current)

        self.fill_tree(self.tree_wins, self.db.get_top_wins())
        self.fill_tree(self.tree_melds, self.db.get_top_total_melds())
        self.fill_tree(self.tree_100, self.db.get_top_100_melds())

        self.tree_archive.clear()
        hist = self.db.get_history()
        for mid, date, winner in hist:
            self.tree_archive.addTopLevelItem(QTreeWidgetItem([str(mid), date, winner]))

    def refresh_combo_suggestions(self):
        known = self.db.get_all_player_names()
        for cb in self.player_combos:
            txt = cb.currentText()
            cb.clear()
            cb.addItems(known)
            cb.setCurrentText(txt)

    def fill_tree(self, tree, data):
        tree.clear()
        for idx, (name, score) in enumerate(data):
            display_name = name
            if idx == 0: display_name = f"🥇 {name}"
            elif idx == 1: display_name = f"🥈 {name}"
            elif idx == 2: display_name = f"🥉 {name}"

            tree.addTopLevelItem(QTreeWidgetItem([str(idx+1), display_name, str(score)]))

    def start_new_game(self):
        names = [cb.currentText().strip() for cb in self.player_combos if cb.currentText().strip()]
        if len(names) < 2:
            QMessageBox.warning(self, "Błąd", "Podaj co najmniej 2 graczy!")
            return
        offset = random.randint(0, len(names) - 1)
        self.main_window.start_game(names, dealer_offset=offset)

    def show_paused_games_dialog(self):
        dlg = PausedGamesDialog(self, self.db, self.main_window)
        dlg.exec()

    def open_archive_details(self):
        item = self.tree_archive.currentItem()
        if not item: return
        match_id = int(item.text(0))
        details = self.db.get_match_details(match_id)
        if not details: return

        players = sorted(list(set(row[1] for row in details)))
        player_totals = {p: 0 for p in players}
        rounds_map = {}
        for row in details:
            r_num, p_name, score = row[0], row[1], row[2]
            player_totals[p_name] += score
            if r_num not in rounds_map: rounds_map[r_num] = {}
            rounds_map[r_num][p_name] = score
        winner = max(player_totals, key=player_totals.get) if player_totals else None

        det_dlg = QDialog(self)
        det_dlg.setWindowTitle(f"Raport meczowy z {item.text(1)}")
        det_dlg.resize(900, 600)
        det_lay = QVBoxLayout(det_dlg)

        summary_group = QGroupBox("Podsumowanie Wyników")
        sum_lay = QHBoxLayout()
        for p in players:
            total = player_totals[p]
            frame = QFrame()
            frame.setFrameShape(QFrame.StyledPanel)
            f_lay = QVBoxLayout()
            if p == winner:
                name_lbl = QLabel(f"🏆 {p}")
                name_lbl.setStyleSheet("color: #d4af37; font-weight: bold; font-size: 16px;")
                total_lbl = QLabel(str(total))
                total_lbl.setStyleSheet("color: #d4af37; font-weight: bold; font-size: 24px;")
                frame.setStyleSheet("background-color: #1a1a1a; border: 2px solid #d4af37; border-radius: 8px;")
            else:
                name_lbl = QLabel(p)
                name_lbl.setStyleSheet("font-size: 14px;")
                total_lbl = QLabel(str(total))
                total_lbl.setStyleSheet("font-size: 20px; font-weight: bold;")
                frame.setStyleSheet("border: 1px solid gray; border-radius: 8px;")
            name_lbl.setAlignment(Qt.AlignCenter)
            total_lbl.setAlignment(Qt.AlignCenter)
            f_lay.addWidget(name_lbl)
            f_lay.addWidget(total_lbl)
            frame.setLayout(f_lay)
            sum_lay.addWidget(frame)
        summary_group.setLayout(sum_lay)
        det_lay.addWidget(summary_group)

        det_tree = QTreeWidget()
        cols = ["Runda"] + players
        det_tree.setHeaderLabels(cols)
        for r_num in sorted(rounds_map.keys()):
            row_data = [str(r_num)]
            for p in players: row_data.append(str(rounds_map[r_num].get(p, 0)))
            det_tree.addTopLevelItem(QTreeWidgetItem(row_data))
        sum_row = ["SUMA"]
        for p in players: sum_row.append(str(player_totals[p]))
        sum_item = QTreeWidgetItem(sum_row)
        for i in range(len(sum_row)):
            sum_item.setFont(i, QFont("Arial", 10, QFont.Weight.Bold))
            sum_item.setForeground(i, QColor("#2196F3"))
        det_tree.addTopLevelItem(sum_item)
        det_lay.addWidget(det_tree)
        det_dlg.exec()

    def show_full_history(self):
        pass


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Menadżer Gry 1000")
        self.resize(1200, 850)

        self.db = TysiacDB()

        # Ikona
        if sys.platform == 'win32':
            pass

        self.stack = QStackedWidget()
        self.setCentralWidget(self.stack)

        # GŁÓWNA KONFIGURACJA CZCIONKI DLA CAŁEJ APLIKACJI (Styl globalny)
        self.setStyleSheet("""
            QWidget { font-size: 12pt; }
            QTreeWidget { font-size: 14px; }
            QTreeWidget::item { padding: 5px; }
            QHeaderView::section { font-size: 14px; font-weight: bold; }
            QPushButton { font-size: 13px; }
            QLineEdit { font-size: 14px; }
            QGroupBox { font-weight: bold; }
        """)

        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.setStyleSheet("QStatusBar { font-size: 10pt; } QLabel { font-size: 10pt; }")

        lbl_version = QLabel(f" Wersja: {APP_VERSION} ")
        self.status_bar.addWidget(lbl_version)

        current_year = datetime.now().year
        year_str = "2025" if current_year == 2025 else f"2025 - {current_year}"
        lbl_copyright = QLabel(f" ©️ KlapkiSzatana {year_str} ")
        self.status_bar.addPermanentWidget(lbl_copyright)

        self.menu_widget = MenuWidget(self, self.db)
        self.stack.addWidget(self.menu_widget)

        self.game_widget = GameWidget(self, self.db)
        self.stack.addWidget(self.game_widget)

        self.show_menu()

    def show_menu(self):
        self.menu_widget.refresh_data()
        self.stack.setCurrentWidget(self.menu_widget)

    def start_game(self, player_names, dealer_offset=0):
        self.game_widget.initialize_game(player_names, dealer_offset=dealer_offset)
        self.stack.setCurrentWidget(self.game_widget)

    def resume_game(self, player_names, match_id, game_log, dealer_offset=0):
        self.game_widget.initialize_game(player_names, match_id, game_log, dealer_offset)
        self.stack.setCurrentWidget(self.game_widget)


if __name__ == "__main__":
    app = QApplication(sys.argv)

    # Pobieramy ID ze zmiennej środowiskowej, domyślnie 'tysiac-manager'
    desktop_id = os.environ.get("APP_ID", "tysiac-manager")
    app.setDesktopFileName(desktop_id)

    # Ładowanie ikony (musi być plik tysiac.png obok skryptu)
    app.setWindowIcon(QIcon(icon_path))

    if HAS_THEME:
        qdarktheme.setup_theme("auto")
    else:
        app.setStyle("Fusion")

    window = MainWindow()
    window.show()

    sys.exit(app.exec())
