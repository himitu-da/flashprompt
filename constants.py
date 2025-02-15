"""
このファイルには、アプリケーション全体で使用される定数が定義されています。

COLORS: UIの色テーマを定義する辞書。
FONTS: UIのフォントスタイルを定義する辞書。
WINDOW_SIZES: ウィンドウのサイズ設定を定義する辞書。
DEFAULT_SETTINGS: アプリケーションのデフォルト設定を定義する辞書。
"""

COLORS = {
    'primary': '#2962ff',
    'primary_hover': '#1565c0',
    'secondary': '#455a64',
    'danger': '#f44336',
    'danger_hover': '#d32f2f',
    'background': '#f5f5f5',
    'surface': '#ffffff',
    'text': '#212121',
    'text_secondary': '#757575'
}

FONTS = {
    'default': ('Segoe UI', 9),
    'default_bold': ('Segoe UI', 9, 'bold'),
    'heading': ('Segoe UI', 10, 'bold'),
    'input': ('Segoe UI', 11)
}

WINDOW_SIZES = {
    'main_min': (300, 300),
    'prompt_creation': (700, 500), # サイズを少し大きくしました
    'prompt_creation_min': (600, 400),
    'variable_dialog': (300, 150)
}

# デフォルト設定
DEFAULT_SETTINGS = {
    'save_directory': '',  # デフォルトは空文字列
}