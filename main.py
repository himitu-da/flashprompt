"""
アプリケーションのエントリーポイント。

Tkinterアプリケーションのメインループを開始します。
"""

import tkinter as tk
from views import FlashPromptApp

def main():
    """
    アプリケーションのメイン関数。

    Tkinterのルートウィンドウを作成し、FlashPromptAppを実行します。
    """
    root = tk.Tk()
    app = FlashPromptApp(root)
    root.mainloop()

if __name__ == "__main__":
    main()