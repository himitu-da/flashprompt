"""
UIユーティリティ関数とスタイル設定を定義するモジュール。
"""

from tkinter import ttk
from constants import COLORS, FONTS

def setup_styles(style):
    """
    ttkスタイルを設定する。

    アプリケーション全体で一貫したUIテーマを提供するために、
    様々なttkウィジェットのスタイルを構成します。

    Args:
        style (ttk.Style): 設定するttkスタイルオブジェクト。
    """
    style.theme_use('clam')

    # 基本スタイル
    style.configure('TFrame', background=COLORS['background'])
    style.configure('TLabelframe', background=COLORS['background'])
    style.configure('TLabelframe.Label',
                   background=COLORS['background'],
                   foreground=COLORS['text'],
                   font=FONTS['heading'])

    # ノートブックスタイル
    style.configure('TNotebook',
                   background=COLORS['surface'],
                   tabmargins=[2, 5, 2, 0])
    style.configure('TNotebook.Tab',
                   padding=[15, 5],
                   background=COLORS['surface'],
                   foreground=COLORS['text'],
                   font=FONTS['default'])
    style.map('TNotebook.Tab',
              background=[('selected', COLORS['primary'])],
              foreground=[('selected', COLORS['surface'])])

    # ボタンスタイル
    style.configure('TButton',
                   padding=[15, 8],
                   background=COLORS['primary'],
                   foreground=COLORS['surface'],
                   font=FONTS['default'])
    style.map('TButton',
              background=[('active', COLORS['primary_hover'])],
              relief=[('pressed', 'flat')])

    # キャンセルボタンスタイル
    style.configure('Cancel.TButton',
                   padding=[15, 8],
                   background=COLORS['surface'],
                   foreground='red',
                   font=FONTS['default'])

    # ラベルスタイル
    style.configure('TLabel',
                   background=COLORS['background'],
                   foreground=COLORS['text'],
                   font=FONTS['default'])

    # エントリースタイル
    style.configure('TEntry',
                   fieldbackground=COLORS['surface'],
                   foreground=COLORS['text'],
                   padding=[5, 5],
                   font=FONTS['default'])

    # ツリービュースタイル
    style.configure('Treeview',
                   background=COLORS['surface'],
                   foreground=COLORS['text'],
                   rowheight=30,
                   fieldbackground=COLORS['surface'],
                   font=FONTS['default'])
    style.configure('Treeview.Heading',
                   background=COLORS['secondary'],
                   foreground=COLORS['surface'],
                   font=FONTS['default_bold'])
    style.map('Treeview',
              background=[('selected', COLORS['primary'])],
              foreground=[('selected', COLORS['surface'])])

def calculate_window_position(parent, width, height):
    """
    ウィンドウの位置を親ウィンドウの中心に計算する。

    新しいウィンドウを親ウィンドウの中央に配置するために使用します。
    画面外に出ないように位置を調整します。

    Args:
        parent (tk.Tk or tk.Toplevel): 親ウィンドウオブジェクト。
        width (int): 新しいウィンドウの幅。
        height (int): 新しいウィンドウの高さ。

    Returns:
        tuple: ウィンドウのx座標とy座標のタプル。
    """
    parent_x = parent.winfo_x()
    parent_y = parent.winfo_y()
    parent_width = parent.winfo_width()
    parent_height = parent.winfo_height()

    screen_width = parent.winfo_screenwidth()
    screen_height = parent.winfo_screenheight()

    x = parent_x + (parent_width - width) // 2
    y = parent_y + (parent_height - height) // 2

    # 画面からはみ出ないように位置を調整
    x = max(0, min(x, screen_width - width))
    y = max(0, min(y, screen_height - height))

    return x, y