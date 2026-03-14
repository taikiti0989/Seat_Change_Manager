"""
席替えソフト - main.py
Python標準ライブラリのみで動作します。
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import random
import copy

# ===============================
# 定数
# ===============================
CIRCLE_NUMBERS = [
    "①", "②", "③", "④", "⑤", "⑥", "⑦", "⑧", "⑨", "⑩",
    "⑪", "⑫", "⑬", "⑭", "⑮", "⑯", "⑰", "⑱", "⑲", "⑳",
    "㉑", "㉒", "㉓", "㉔", "㉕", "㉖", "㉗", "㉘", "㉙", "㉚",
    "㉛", "㉜", "㉝", "㉞", "㉟", "㊱", "㊲", "㊳", "㊴", "㊵",
    "㊶", "㊷", "㊸", "㊹", "㊺", "㊻", "㊼", "㊽", "㊾", "㊿",
]

# カラーパレット
BG_MAIN      = "#1e1e2e"    # 背景（ダーク）
BG_CARD      = "#2a2a3e"    # カード背景
BG_SIDEBAR   = "#16213e"    # サイドバー
ACCENT       = "#7c5cbf"    # アクセント（紫）
ACCENT_LIGHT = "#9d7fd4"    # 薄いアクセント
SUCCESS      = "#4caf87"    # 成功色（緑）
DANGER       = "#e05a6a"    # 危険色（赤）
SEAT_ACTIVE  = "#3a3a5c"    # 有効席の色
SEAT_HOVER   = "#4e4e7c"    # ホバー時
SEAT_INVALID = "#2a2a3e"    # 無効席
SEAT_RESULT  = "#3a5c4e"    # 結果表示時の有効席
TEXT_PRIMARY = "#e8eaf6"    # メインテキスト
TEXT_SECONDARY = "#9e9ebf"  # サブテキスト
TEXT_INVALID = "#4a4a6a"    # 無効席テキスト

FONT_TITLE   = ("Helvetica", 22, "bold")
FONT_SUB     = ("Helvetica", 13)
FONT_LABEL   = ("Helvetica", 11)
FONT_SEAT    = ("Helvetica", 15, "bold")
FONT_SEAT_SM = ("Helvetica", 12, "bold")
FONT_BTN     = ("Helvetica", 12, "bold")


def get_circle(n: int) -> str:
    """生徒番号（1始まり）を丸数字に変換する。50超は#番号で表示。"""
    if 1 <= n <= 50:
        return CIRCLE_NUMBERS[n - 1]
    return f"#{n}"


def count_violations(layout: list, bad_pairs: list,
                     near_front: list = None) -> int:
    """
    制約違反数を返す。
    - bad_pairs: [(A, B), ...] 隣接させてはいけないペア
    - near_front: [(student, max_row), ...] 前から max_row 行以内に置く（0始まり換算）
      layout は 2D リスト（None or 生徒番号）。
    """
    if near_front is None:
        near_front = []
    rows = len(layout)
    cols = len(layout[0]) if rows > 0 else 0
    # 座席の (行, 列) 位置マップ を作成
    pos = {}
    for r in range(rows):
        for c in range(cols):
            if layout[r][c] is not None:
                pos[layout[r][c]] = (r, c)
    count = 0
    # 仲が悪いペアの違反チェック
    for a, b in bad_pairs:
        if a not in pos or b not in pos:
            continue
        ar, ac = pos[a]
        br, bc = pos[b]
        if abs(ar - br) <= 1 and abs(ac - bc) <= 1:
            count += 1
    # 視力制約の違反チェック（行番号 0始まり、max_row は 1始まり）
    for student, max_row in near_front:
        if student not in pos:
            continue
        sr, _ = pos[student]
        if sr >= max_row:   # max_row 行より後ろにいる
            count += 1
    return count


def assign_seats(valid_seats: list, num_students: int,
                 bad_pairs: list, near_front: list = None,
                 max_tries: int = 3000) -> dict:
    """
    有効席リスト[(r,c), ...]に生徒を配置する。
    制約違反が最小の配置を返す。
    戻り値: {(r,c): 生徒番号} の辞書
    - bad_pairs: [(A,B), ...] 隣接させてはいけないペア
    - near_front: [(student, max_row), ...] 前から max_row 行以内（1始まり）
    """
    if near_front is None:
        near_front = []
    if len(valid_seats) < num_students:
        return None

    students = list(range(1, num_students + 1))

    def make_layout(assignment):
        """割り当て辞書から2Dリストを生成。"""
        max_r = max(r for r, c in valid_seats)
        max_c = max(c for r, c in valid_seats)
        layout = [[None] * (max_c + 1) for _ in range(max_r + 1)]
        for (r, c), s in assignment.items():
            layout[r][c] = s
        return layout

    has_constraints = bool(bad_pairs) or bool(near_front)

    # 初期ランダム配置
    seats_sample = random.sample(valid_seats, num_students)
    best_assign = {seats_sample[i]: students[i] for i in range(num_students)}
    best_layout = make_layout(best_assign)
    best_viol = count_violations(best_layout, bad_pairs, near_front)

    if best_viol == 0 or not has_constraints:
        return best_assign

    # スワップによる改善
    current_assign = dict(best_assign)
    current_viol = best_viol

    for _ in range(max_tries):
        # ランダムに2席をスワップ
        seat_list = list(current_assign.keys())
        i, j = random.sample(range(len(seat_list)), 2)
        s1, s2 = seat_list[i], seat_list[j]
        current_assign[s1], current_assign[s2] = current_assign[s2], current_assign[s1]

        layout = make_layout(current_assign)
        viol = count_violations(layout, bad_pairs, near_front)

        if viol < current_viol:
            current_viol = viol
            if viol < best_viol:
                best_assign = dict(current_assign)
                best_viol = viol
                if best_viol == 0:
                    break
        else:
            # 元に戻す
            current_assign[s1], current_assign[s2] = current_assign[s2], current_assign[s1]

    return best_assign


def load_constraints(filepath: str) -> tuple:
    """
    制約ファイルを読み込む。
    戻り値: (bad_pairs, near_front, errors)
      - bad_pairs   : [(A, B), ...]  隣接させないペア
      - near_front  : [(student, max_row), ...]  前から max_row 行以内（1始まり）
      - errors      : [str, ...]  パースエラー一覧

    対応フォーマット:
      bad_pair: A, B          → 仲の悪いペア
      near_front: student, N  → 前から N 行以内
      A,B                     → 旧互換（bad_pair 扱い）
    """
    bad_pairs = []
    near_front = []
    errors = []
    try:
        with open(filepath, encoding="utf-8") as f:
            for lineno, raw in enumerate(f, 1):
                line = raw.strip()
                if not line or line.startswith("#"):
                    continue

                # キーワード付きフォーマット
                if ":" in line:
                    key, _, rest = line.partition(":")
                    key = key.strip().lower()
                    parts = [p.strip() for p in rest.split(",")]
                    if key == "bad_pair":
                        if len(parts) != 2:
                            errors.append(f"行{lineno}: bad_pair のフォーマットエラー「{line}」")
                            continue
                        try:
                            bad_pairs.append((int(parts[0]), int(parts[1])))
                        except ValueError:
                            errors.append(f"行{lineno}: 数値エラー「{line}」")
                    elif key == "near_front":
                        if len(parts) != 2:
                            errors.append(f"行{lineno}: near_front のフォーマットエラー「{line}」")
                            continue
                        try:
                            student = int(parts[0])
                            max_row = int(parts[1])
                            if max_row < 1:
                                errors.append(f"行{lineno}: near_front の行数は1以上にしてください「{line}」")
                                continue
                            near_front.append((student, max_row))
                        except ValueError:
                            errors.append(f"行{lineno}: 数値エラー「{line}」")
                    else:
                        errors.append(f"行{lineno}: 不明なキーワード「{key}」")
                else:
                    # 旧互換フォーマット: A,B
                    parts = line.split(",")
                    if len(parts) != 2:
                        errors.append(f"行{lineno}: フォーマットエラー「{line}」")
                        continue
                    try:
                        bad_pairs.append((int(parts[0].strip()), int(parts[1].strip())))
                    except ValueError:
                        errors.append(f"行{lineno}: 数値エラー「{line}」")
    except Exception as e:
        errors.append(str(e))
    return bad_pairs, near_front, errors


# ===============================
# メインアプリ
# ===============================
class SeatApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("席替えソフト")
        self.configure(bg=BG_MAIN)
        self.resizable(True, True)
        self.minsize(700, 500)

        # 共有データ
        self.rows_var = tk.IntVar(value=5)
        self.cols_var = tk.IntVar(value=6)
        self.students_var = tk.IntVar(value=25)
        self.invalid_seats: set = set()      # (r, c)
        self.bad_pairs: list = []            # [(A, B), ...]
        self.near_front: list = []           # [(student, max_row), ...]
        self.constraints_file: str = ""
        self.result_assign: dict = {}        # (r,c) -> 生徒番号

        # フレームを重ねて管理
        self._frames = {}
        container = tk.Frame(self, bg=BG_MAIN)
        container.pack(fill="both", expand=True)
        container.grid_rowconfigure(0, weight=1)
        container.grid_columnconfigure(0, weight=1)

        for F in (SettingsPage, LayoutPage, ResultPage):
            frame = F(container, self)
            self._frames[F] = frame
            frame.grid(row=0, column=0, sticky="nsew")

        self.show_frame(SettingsPage)

    def show_frame(self, page_cls):
        frame = self._frames[page_cls]
        frame.on_show()
        frame.tkraise()


# ===============================
# ページ1: 設定画面
# ===============================
class SettingsPage(tk.Frame):
    def __init__(self, parent, app: SeatApp):
        super().__init__(parent, bg=BG_MAIN)
        self.app = app
        self._build()

    def _build(self):
        # ヘッダー
        header = tk.Frame(self, bg=BG_SIDEBAR, pady=30)
        header.pack(fill="x")
        tk.Label(header, text="🪑 席替えソフト", font=FONT_TITLE,
                 bg=BG_SIDEBAR, fg=TEXT_PRIMARY).pack()
        tk.Label(header, text="クラスの設定を入力してください",
                 font=FONT_SUB, bg=BG_SIDEBAR, fg=TEXT_SECONDARY).pack(pady=(6, 0))

        # カード
        card = tk.Frame(self, bg=BG_CARD, padx=50, pady=40,
                        relief="flat", bd=0)
        card.pack(padx=80, pady=50, fill="both", expand=True)

        def add_row(label_text, var, from_=1, to=50):
            row = tk.Frame(card, bg=BG_CARD)
            row.pack(fill="x", pady=10)
            tk.Label(row, text=label_text, font=FONT_SUB,
                     bg=BG_CARD, fg=TEXT_PRIMARY, width=14, anchor="w").pack(side="left")
            spin = tk.Spinbox(
                row, from_=from_, to=to, textvariable=var,
                width=6, font=FONT_SUB,
                bg="#3a3a5c", fg=TEXT_PRIMARY, insertbackground=TEXT_PRIMARY,
                buttonbackground=ACCENT, relief="flat", bd=4,
                highlightthickness=1, highlightcolor=ACCENT,
                highlightbackground="#4a4a6a"
            )
            spin.pack(side="left", padx=10)
            return spin

        add_row("列数（横）:", self.app.cols_var, 1, 20)
        add_row("行数（縦）:", self.app.rows_var, 1, 20)
        add_row("生徒数:", self.app.students_var, 1, 50)

        # ヒントラベル
        tk.Label(card, text="💡 生徒数は（列数 × 行数）以下にしてください",
                 font=("Helvetica", 10), bg=BG_CARD,
                 fg=TEXT_SECONDARY).pack(pady=(10, 0))

        # 次へボタン
        btn = tk.Button(card, text="次へ　→", font=FONT_BTN,
                        bg=ACCENT, fg="white", relief="flat",
                        padx=30, pady=12, cursor="hand2",
                        activebackground=ACCENT_LIGHT, activeforeground="white",
                        command=self._on_next)
        btn.pack(pady=(30, 0))
        _bind_hover(btn, ACCENT, ACCENT_LIGHT)

    def _on_next(self):
        rows = self.app.rows_var.get()
        cols = self.app.cols_var.get()
        students = self.app.students_var.get()
        if students > rows * cols:
            messagebox.showerror(
                "設定エラー",
                f"生徒数（{students}）が席数（{rows}×{cols}={rows*cols}）を超えています。\n"
                "設定を変更してください。"
            )
            return
        # 無効席リセット（行列数が変わったとき）
        self.app.invalid_seats = set()
        self.app.bad_pairs = []
        self.app.near_front = []
        self.app.constraints_file = ""
        self.app.show_frame(LayoutPage)

    def on_show(self):
        pass


# ===============================
# ページ2: レイアウト編集
# ===============================
class LayoutPage(tk.Frame):
    def __init__(self, parent, app: SeatApp):
        super().__init__(parent, bg=BG_MAIN)
        self.app = app
        self.seat_buttons = {}   # (r,c) -> tk.Button
        self._grid_frame = None
        self._info_label = None
        self._constraint_label = None
        self._build_static()

    def _build_static(self):
        """毎回変わらない部分だけ先に作る。"""
        # ヘッダー
        header = tk.Frame(self, bg=BG_SIDEBAR, pady=20)
        header.pack(fill="x")
        tk.Label(header, text="🗺 席レイアウト設定",
                 font=FONT_TITLE, bg=BG_SIDEBAR, fg=TEXT_PRIMARY).pack()
        tk.Label(header,
                 text="グレーの席をクリックして「使わない席」に指定できます",
                 font=FONT_LABEL, bg=BG_SIDEBAR, fg=TEXT_SECONDARY).pack(pady=(4, 0))

        # ツールバー
        toolbar = tk.Frame(self, bg=BG_MAIN, pady=10)
        toolbar.pack(fill="x", padx=20)

        back_btn = tk.Button(
            toolbar, text="← 戻る", font=FONT_BTN,
            bg="#4a4a6a", fg="white", relief="flat",
            padx=16, pady=8, cursor="hand2",
            activebackground="#5a5a7a", activeforeground="white",
            command=lambda: self.app.show_frame(SettingsPage)
        )
        back_btn.pack(side="left")
        _bind_hover(back_btn, "#4a4a6a", "#5a5a7a")

        self._constraint_label = tk.Label(
            toolbar, text="制約ファイル: 未読み込み",
            font=FONT_LABEL, bg=BG_MAIN, fg=TEXT_SECONDARY
        )
        self._constraint_label.pack(side="left", padx=20)

        load_btn = tk.Button(
            toolbar, text="📂 制約ファイル読込", font=FONT_BTN,
            bg="#4a6a5c", fg="white", relief="flat",
            padx=16, pady=8, cursor="hand2",
            activebackground="#5a7a6c", activeforeground="white",
            command=self._load_constraints
        )
        load_btn.pack(side="right")
        _bind_hover(load_btn, "#4a6a5c", "#5a7a6c")

        run_btn = tk.Button(
            toolbar, text="✨ 席替え実行", font=FONT_BTN,
            bg=ACCENT, fg="white", relief="flat",
            padx=20, pady=8, cursor="hand2",
            activebackground=ACCENT_LIGHT, activeforeground="white",
            command=self._run_assignment
        )
        run_btn.pack(side="right", padx=(0, 10))
        _bind_hover(run_btn, ACCENT, ACCENT_LIGHT)

        # 情報ラベル
        self._info_label = tk.Label(
            self, text="", font=FONT_LABEL,
            bg=BG_MAIN, fg=TEXT_SECONDARY
        )
        self._info_label.pack()

        # グリッドのスクロール可能コンテナ
        self._canvas = tk.Canvas(self, bg=BG_MAIN, highlightthickness=0)
        self._scrollbar_y = ttk.Scrollbar(self, orient="vertical",
                                          command=self._canvas.yview)
        self._scrollbar_x = ttk.Scrollbar(self, orient="horizontal",
                                           command=self._canvas.xview)
        self._canvas.configure(yscrollcommand=self._scrollbar_y.set,
                               xscrollcommand=self._scrollbar_x.set)

        self._scrollbar_x.pack(side="bottom", fill="x")
        self._scrollbar_y.pack(side="right", fill="y")
        self._canvas.pack(fill="both", expand=True, padx=10, pady=10)

        self._grid_container = tk.Frame(self._canvas, bg=BG_MAIN)
        self._canvas_window = self._canvas.create_window(
            (0, 0), window=self._grid_container, anchor="nw"
        )
        self._grid_container.bind("<Configure>", self._on_frame_configure)
        self._canvas.bind("<Configure>", self._on_canvas_configure)

    def _on_frame_configure(self, event):
        self._canvas.configure(scrollregion=self._canvas.bbox("all"))

    def _on_canvas_configure(self, event):
        self._canvas.itemconfig(self._canvas_window, width=event.width)

    def on_show(self):
        """ページ表示時にグリッドを再構築する。"""
        self._build_grid()
        self._update_info()

    def _build_grid(self):
        """席グリッドを再構築する。"""
        for w in self._grid_container.winfo_children():
            w.destroy()
        self.seat_buttons.clear()

        rows = self.app.rows_var.get()
        cols = self.app.cols_var.get()

        # 黒板ラベル
        board_frame = tk.Frame(self._grid_container, bg="#2e4a3a",
                               padx=20, pady=8, relief="flat")
        board_frame.grid(row=0, column=0, columnspan=cols,
                         sticky="ew", padx=5, pady=(10, 20))
        tk.Label(board_frame, text="📋 黒板（前方）",
                 font=FONT_SUB, bg="#2e4a3a", fg="#a8d8b0").pack()

        for r in range(rows):
            for c in range(cols):
                is_invalid = (r, c) in self.app.invalid_seats
                btn = tk.Button(
                    self._grid_container,
                    text="✕" if is_invalid else "　",
                    font=FONT_SEAT,
                    width=3, height=1,
                    relief="flat", bd=0,
                    cursor="hand2",
                    bg=SEAT_INVALID if is_invalid else SEAT_ACTIVE,
                    fg=TEXT_INVALID if is_invalid else TEXT_PRIMARY,
                )
                btn.grid(row=r + 1, column=c, padx=4, pady=4, sticky="nsew")
                self._grid_container.grid_columnconfigure(c, weight=1)

                seat = (r, c)
                btn.configure(command=lambda s=seat: self._toggle_seat(s))
                _bind_hover(
                    btn,
                    SEAT_INVALID if is_invalid else SEAT_ACTIVE,
                    SEAT_HOVER,
                    toggle=False
                )
                self.seat_buttons[seat] = btn

    def _toggle_seat(self, seat):
        r, c = seat
        if (r, c) in self.app.invalid_seats:
            self.app.invalid_seats.discard((r, c))
            is_invalid = False
        else:
            self.app.invalid_seats.add((r, c))
            is_invalid = True
        btn = self.seat_buttons[seat]
        btn.configure(
            text="✕" if is_invalid else "　",
            bg=SEAT_INVALID if is_invalid else SEAT_ACTIVE,
            fg=TEXT_INVALID if is_invalid else TEXT_PRIMARY,
        )
        self._update_info()

    def _update_info(self):
        rows = self.app.rows_var.get()
        cols = self.app.cols_var.get()
        total = rows * cols
        invalid = len(self.app.invalid_seats)
        valid = total - invalid
        students = self.app.students_var.get()
        color = SUCCESS if valid >= students else DANGER
        self._info_label.configure(
            text=f"有効席: {valid} ／ 生徒数: {students}",
            fg=color
        )

    def _load_constraints(self):
        path = filedialog.askopenfilename(
            title="制約ファイルを選択",
            filetypes=[("テキストファイル", "*.txt"), ("すべて", "*.*")]
        )
        if not path:
            return
        bad_pairs, near_front, errors = load_constraints(path)
        if errors:
            messagebox.showwarning(
                "読み込み警告",
                "以下のエラーがありました（他の行は読み込まれました）:\n\n" + "\n".join(errors)
            )
        self.app.bad_pairs = bad_pairs
        self.app.near_front = near_front
        self.app.constraints_file = path
        fname = path.split("/")[-1]
        total = len(bad_pairs) + len(near_front)
        self._constraint_label.configure(
            text=f"制約: {fname}（仲悪ペア{len(bad_pairs)}件 / 視力{len(near_front)}件）",
            fg=SUCCESS
        )
        messagebox.showinfo(
            "制約ファイル読み込み完了",
            f"【仲が悪いペア】{len(bad_pairs)} 件\n"
            f"【視力制約（前方着席）】{len(near_front)} 件\n"
            f"合計 {total} 件の制約を読み込みました。"
        )

    def _run_assignment(self):
        rows = self.app.rows_var.get()
        cols = self.app.cols_var.get()
        students = self.app.students_var.get()

        valid_seats = [
            (r, c)
            for r in range(rows)
            for c in range(cols)
            if (r, c) not in self.app.invalid_seats
        ]

        if len(valid_seats) < students:
            messagebox.showerror(
                "エラー",
                f"有効な席（{len(valid_seats)}）が生徒数（{students}）より少ないです。\n"
                "無効席を減らすか、生徒数を減らしてください。"
            )
            return

        result = assign_seats(valid_seats, students,
                              self.app.bad_pairs, self.app.near_front)
        if result is None:
            messagebox.showerror("エラー", "席の割り当てに失敗しました。")
            return

        self.app.result_assign = result
        self.app.show_frame(ResultPage)


# ===============================
# ページ3: 結果表示
# ===============================
class ResultPage(tk.Frame):
    def __init__(self, parent, app: SeatApp):
        super().__init__(parent, bg=BG_MAIN)
        self.app = app
        self._result_frame = None
        self._viol_label = None
        self._build_static()

    def _build_static(self):
        # ヘッダー
        header = tk.Frame(self, bg=BG_SIDEBAR, pady=20)
        header.pack(fill="x")
        tk.Label(header, text="✅ 席替え結果",
                 font=FONT_TITLE, bg=BG_SIDEBAR, fg=TEXT_PRIMARY).pack()
        self._viol_label = tk.Label(
            header, text="", font=FONT_LABEL,
            bg=BG_SIDEBAR, fg=TEXT_SECONDARY
        )
        self._viol_label.pack(pady=(4, 0))

        # ボタン類
        toolbar = tk.Frame(self, bg=BG_MAIN, pady=10)
        toolbar.pack(fill="x", padx=20)

        retry_btn = tk.Button(
            toolbar, text="🔄 もう一度", font=FONT_BTN,
            bg="#4a6a5c", fg="white", relief="flat",
            padx=16, pady=8, cursor="hand2",
            activebackground="#5a7a6c", activeforeground="white",
            command=self._retry
        )
        retry_btn.pack(side="left")
        _bind_hover(retry_btn, "#4a6a5c", "#5a7a6c")

        reset_btn = tk.Button(
            toolbar, text="⚙ 最初から", font=FONT_BTN,
            bg="#4a4a6a", fg="white", relief="flat",
            padx=16, pady=8, cursor="hand2",
            activebackground="#5a5a7a", activeforeground="white",
            command=lambda: self.app.show_frame(SettingsPage)
        )
        reset_btn.pack(side="left", padx=10)
        _bind_hover(reset_btn, "#4a4a6a", "#5a5a7a")

        # スクロール可能結果エリア
        self._canvas = tk.Canvas(self, bg=BG_MAIN, highlightthickness=0)
        self._scrollbar_y = ttk.Scrollbar(self, orient="vertical",
                                          command=self._canvas.yview)
        self._scrollbar_x = ttk.Scrollbar(self, orient="horizontal",
                                           command=self._canvas.xview)
        self._canvas.configure(yscrollcommand=self._scrollbar_y.set,
                               xscrollcommand=self._scrollbar_x.set)

        self._scrollbar_x.pack(side="bottom", fill="x")
        self._scrollbar_y.pack(side="right", fill="y")
        self._canvas.pack(fill="both", expand=True, padx=10, pady=10)

        self._result_container = tk.Frame(self._canvas, bg=BG_MAIN)
        self._canvas_window = self._canvas.create_window(
            (0, 0), window=self._result_container, anchor="nw"
        )
        self._result_container.bind(
            "<Configure>",
            lambda e: self._canvas.configure(
                scrollregion=self._canvas.bbox("all")
            )
        )
        self._canvas.bind(
            "<Configure>",
            lambda e: self._canvas.itemconfig(self._canvas_window, width=e.width)
        )

    def on_show(self):
        self._build_result()

    def _build_result(self):
        for w in self._result_container.winfo_children():
            w.destroy()

        rows = self.app.rows_var.get()
        cols = self.app.cols_var.get()
        assign = self.app.result_assign   # (r,c) -> 生徒番号
        invalid = self.app.invalid_seats

        # 制約違反チェック
        layout = [[None] * cols for _ in range(rows)]
        for (r, c), s in assign.items():
            layout[r][c] = s
        violations = count_violations(layout, self.app.bad_pairs, self.app.near_front)

        if violations == 0:
            viol_text = "✅ 制約違反なし"
            viol_color = SUCCESS
        else:
            viol_text = f"⚠ 制約違反 {violations} 件（最適化後）"
            viol_color = DANGER
        self._viol_label.configure(text=viol_text, fg=viol_color)

        # 黒板
        board_frame = tk.Frame(self._result_container, bg="#2e4a3a",
                               padx=20, pady=8)
        board_frame.grid(row=0, column=0, columnspan=cols,
                         sticky="ew", padx=5, pady=(10, 20))
        tk.Label(board_frame, text="📋 黒板（前方）",
                 font=FONT_SUB, bg="#2e4a3a", fg="#a8d8b0").pack()

        for r in range(rows):
            for c in range(cols):
                if (r, c) in invalid:
                    # 無効席
                    cell = tk.Frame(self._result_container, bg=SEAT_INVALID,
                                    width=60, height=60)
                    cell.grid(row=r + 1, column=c, padx=4, pady=4, sticky="nsew")
                    cell.grid_propagate(False)
                    self._result_container.grid_columnconfigure(c, weight=1)
                elif (r, c) in assign:
                    student = assign[(r, c)]
                    circle = get_circle(student)
                    # 制約違反がある席を赤くする
                    seat_bg = SEAT_RESULT
                    # 仲の悪いペア違反チェック
                    for a, b in self.app.bad_pairs:
                        partner = None
                        if assign.get((r, c)) == a:
                            partner = b
                        elif assign.get((r, c)) == b:
                            partner = a
                        if partner:
                            for dr in [-1, 0, 1]:
                                for dc in [-1, 0, 1]:
                                    if dr == 0 and dc == 0:
                                        continue
                                    nr, nc = r + dr, c + dc
                                    if assign.get((nr, nc)) == partner:
                                        seat_bg = "#5c2a3e"
                                        break
                    # 視力制約違反チェック（前方着席）
                    for s, max_row in self.app.near_front:
                        if student == s and r >= max_row:
                            seat_bg = "#5c3a1e"   # オレンジ系で区別
                            break

                    cell = tk.Frame(self._result_container, bg=seat_bg,
                                    width=60, height=60)
                    cell.grid(row=r + 1, column=c, padx=4, pady=4, sticky="nsew")
                    cell.grid_propagate(False)
                    tk.Label(cell, text=circle, font=FONT_SEAT,
                             bg=seat_bg, fg=TEXT_PRIMARY).place(relx=0.5, rely=0.5,
                                                                 anchor="center")
                    self._result_container.grid_columnconfigure(c, weight=1)
                else:
                    # 有効だが生徒なし（生徒数 < 席数のとき空席）
                    cell = tk.Frame(self._result_container, bg="#2a3a4e",
                                    width=60, height=60)
                    cell.grid(row=r + 1, column=c, padx=4, pady=4, sticky="nsew")
                    cell.grid_propagate(False)
                    tk.Label(cell, text="空", font=FONT_SEAT_SM,
                             bg="#2a3a4e", fg="#4a6a7a").place(relx=0.5, rely=0.5,
                                                              anchor="center")
                    self._result_container.grid_columnconfigure(c, weight=1)

        # 凡例
        legend = tk.Frame(self._result_container, bg=BG_MAIN)
        legend.grid(row=rows + 2, column=0, columnspan=cols, pady=20)
        _legend_item(legend, SEAT_RESULT, "生徒あり")
        _legend_item(legend, "#5c2a3e", "違反: 仲悪ペアが隣接")
        _legend_item(legend, "#5c3a1e", "違反: 視力制約（前方）")
        _legend_item(legend, SEAT_INVALID, "無効席")
        _legend_item(legend, "#2a3a4e", "空席")

    def _retry(self):
        """同じレイアウトで再抽選。"""
        rows = self.app.rows_var.get()
        cols = self.app.cols_var.get()
        students = self.app.students_var.get()
        valid_seats = [
            (r, c)
            for r in range(rows)
            for c in range(cols)
            if (r, c) not in self.app.invalid_seats
        ]
        result = assign_seats(valid_seats, students,
                              self.app.bad_pairs, self.app.near_front)
        if result:
            self.app.result_assign = result
            self._build_result()


# ===============================
# ユーティリティ
# ===============================
def _bind_hover(btn: tk.Button, normal_bg: str, hover_bg: str, toggle=True):
    """ボタンにホバーエフェクトを付与する。"""
    def on_enter(e):
        btn.configure(bg=hover_bg)
    def on_leave(e):
        btn.configure(bg=normal_bg)
    btn.bind("<Enter>", on_enter)
    btn.bind("<Leave>", on_leave)


def _legend_item(parent, color, text):
    f = tk.Frame(parent, bg=BG_MAIN)
    f.pack(side="left", padx=12)
    tk.Frame(f, bg=color, width=20, height=20).pack(side="left")
    tk.Label(f, text=text, font=("Helvetica", 10),
             bg=BG_MAIN, fg=TEXT_SECONDARY).pack(side="left", padx=4)


# ===============================
# エントリポイント
# ===============================
if __name__ == "__main__":
    app = SeatApp()
    app.mainloop()
