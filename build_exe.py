#!/usr/bin/env python
"""
このスクリプトは PyInstaller を使用して、単一の exe ファイルを生成するためのものです。

実行前に以下のコマンドで PyInstaller をインストールしてください:
    pip install pyinstaller

このスクリプトを実行すると、エントリーポイントの main.py を基に、
GUIアプリケーション用の単一 exe ファイル「FlasshPrompt_v●●」が生成されます。
"""

import PyInstaller.__main__
import constants

# バージョン番号をファイル名に挿入します
exe_name = f"FlasshPrompt_v{constants.VERSION}"

PyInstaller.__main__.run([
    'main.py',
    '--onefile',           # 単一の exe ファイルを生成
    '--windowed',          # GUIアプリ用：コンソールウィンドウを表示しない
    f'--name={exe_name}',  # 出力される exe ファイル名をバージョン付きに変更
    # 以下の各ファイルをビルドに含めます:
    '--add-data', 'constants.py;.',  # constants.py を追加
    '--add-data', 'models.py;.',    # models.py を追加
    '--add-data', 'utils.py;.',     # utils.py を追加
    '--add-data', 'views.py;.'       # views.py を追加
])