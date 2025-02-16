"""
アプリケーションのUIビューを定義するモジュール。

FlashPromptAppクラスはメインアプリケーションウィンドウを管理し、
PromptCreationWindowクラスはプロンプト作成/編集ウィンドウを管理します。
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import re
from models import PromptManager, SettingsManager
from constants import COLORS, FONTS, WINDOW_SIZES, DEFAULT_SETTINGS
from utils import setup_styles, calculate_window_position
import os

class PromptCreationWindow:
    """
    プロンプトの作成と編集を行うためのウィンドウクラス。

    既存のプロンプトを編集したり、新しいプロンプトを作成したりするために使用されます。
    """
    def __init__(self, parent, prompt_data, initial_tab='prompt', always_on_top=True):
        """
        PromptCreationWindowクラスのコンストラクタ。

        新しいToplevelウィンドウを作成し、UIをセットアップします。

        Args:
            parent (tk.Tk or tk.Toplevel): 親ウィンドウオブジェクト。
            prompt_data (dict): 編集するプロンプトのデータ（新規作成の場合は空の辞書）。
            initial_tab (str): 初期に選択するタブの名前。'prompt' または 'template'。
            always_on_top (bool): ウィンドウを常に最前面に表示するかどうか。
        """
        self.window = tk.Toplevel(parent)
        self.window.title(prompt_data.get('name', 'プロンプト作成'))
        self.window.attributes('-topmost', always_on_top)

        # ウィンドウのサイズを設定
        self.window.resizable(True, True)
        self.window.minsize(*WINDOW_SIZES['prompt_creation_min'])

        # ウィンドウの位置を計算
        x, y = calculate_window_position(parent, *WINDOW_SIZES['prompt_creation'])
        self.window.geometry(f"{WINDOW_SIZES['prompt_creation'][0]}x{WINDOW_SIZES['prompt_creation'][1]}+{x}+{y}")

        self.prompt_data = prompt_data
        self.original_template = prompt_data['template']  # 編集をキャンセルするために元のテンプレートを保存
        self.original_name = prompt_data['name'] # 編集をキャンセルするために元のテンプレート名を保存

        # スタイルの設定
        self.style = ttk.Style()

        self.notebook = ttk.Notebook(self.window)
        self.notebook.pack(expand=True, fill='both')

        # プロンプト作成タブ
        self.prompt_tab = ttk.Frame(self.notebook)
        self.notebook.add(self.prompt_tab, text='プロンプト作成')
        self._setup_prompt_creation_tab()

        # テンプレート編集タブ
        self.template_change_tab = ttk.Frame(self.notebook)
        self.notebook.add(self.template_change_tab, text='テンプレート編集')
        self._setup_template_change_tab()

        # デフォルトで指定されたタブを選択
        if initial_tab == 'template':
            self.notebook.select(self.template_change_tab)
        else:
            self.notebook.select(self.prompt_tab)
        self._update_variables_listbox() # 変数一覧を初期化


    def _setup_prompt_creation_tab(self):
        """プロンプト作成タブのUIをセットアップ"""
        prompt_frame = ttk.Frame(self.prompt_tab)
        prompt_frame.pack(fill='both', expand=True, padx=10, pady=10)

        # 変数入力エリアのセットアップ
        self._setup_variable_input_area(prompt_frame)

        # プレビューエリア
        preview_frame = ttk.LabelFrame(prompt_frame, text="生成されたプロンプト")
        preview_frame.pack(fill='both', expand=True, padx=10, pady=5)

        self.preview_text = tk.Text(preview_frame, height=5, width=50, font=FONTS['input'])
        self.preview_text.pack(padx=5, pady=5, fill='both', expand=True)

        # コピーボタンをインスタンス変数として保存
        self.copy_button = ttk.Button(prompt_frame, text="コピー", command=self.copy_to_clipboard)
        self.copy_button.pack(pady=10)

        # 初期プレビューを生成
        self.update_preview(None)

        # 最初の変数入力欄にフォーカスを移動
        if self.first_entry:
            self.first_entry.focus_set()
            self.first_entry.tag_add('sel', '1.0', tk.END)

    def _setup_template_change_tab(self):
        """
        「テンプレート編集」タブのUIをセットアップする。(テンプレート登録タブをコピーして修正)
        """
        # メインコンテンツを左右に分けるフレーム
        content_frame = ttk.Frame(self.template_change_tab, style='TFrame')
        content_frame.pack(fill='both', expand=True, padx=10, pady=10)

        # 左側フレーム（入力エリア）
        left_frame = ttk.LabelFrame(content_frame, text="テンプレート編集", style='TLabelframe') # textを変更
        left_frame.pack(side='left', fill='both', expand=True, padx=(0, 10))

        # テンプレート入力エリア
        template_label_frame = ttk.Frame(left_frame, style='TFrame')
        template_label_frame.pack(fill='x', padx=10)
        ttk.Label(template_label_frame, text="テンプレート:", style='TLabel').pack(side='left')

        self.template_text = tk.Text(left_frame, height=10, width=50, # heightを10に設定
                                   font=FONTS['input'],
                                   bg=COLORS['surface'],
                                   fg=COLORS['text'])
        self.template_text.pack(padx=10, pady=5, fill='both', expand=True)
        self.template_text.insert("1.0", self.prompt_data['template']) # 既存のテンプレートを挿入
        self.template_text.bind('<KeyRelease>', self._on_template_change_change_tab) # メソッド名を変更

        # 右側フレーム（変数一覧）
        right_frame = ttk.LabelFrame(content_frame, text="変数一覧", style='TLabelframe')
        right_frame.pack(side='right', fill='both', padx=(10, 0))

        self.variables_listbox = tk.Listbox(right_frame,
                                          width=20,
                                          font=FONTS['input'],
                                          bg=COLORS['surface'],
                                          fg=COLORS['text'],
                                          selectmode='single',
                                          activestyle='none',
                                          selectbackground=COLORS['primary'],
                                          selectforeground=COLORS['surface'])
        self.variables_listbox.pack(padx=10, pady=10, fill='both', expand=True)
        self.variables_listbox.configure(height=10)
        self.variables_listbox.bind('<Double-Button-1>', self._insert_selected_variable_change_tab) # メソッド名を変更

        # 変数操作ボタンフレーム
        var_button_frame = ttk.Frame(right_frame, style='TFrame')
        var_button_frame.pack(fill='x', padx=10, pady=10)
        ttk.Button(var_button_frame, text="変数追加",
                  command=self._show_variable_dialog_change_tab, # メソッド名を変更
                  style='TButton').pack(side='left', padx=5)
        ttk.Button(var_button_frame, text="変数挿入",
                  command=self._insert_selected_variable_change_tab, # メソッド名を変更
                  style='TButton').pack(side='left', padx=5)

        # ボタンフレーム
        button_frame = ttk.Frame(self.template_change_tab, style='TFrame')
        button_frame.pack(fill='x', padx=10, pady=10)
        ttk.Button(button_frame, text="保存",
                  command=self._save_template_change_tab, # メソッド名を変更
                  style='TButton').pack(side='left', padx=5)
        ttk.Button(button_frame, text="破棄",
                  command=self._discard_current_template_input_change_tab, # メソッド名を変更
                  style='TButton').pack(side='left', padx=5)


    def _setup_variable_input_area(self, parent_frame):
        """変数入力エリアをセットアップする。"""
        variables = list(dict.fromkeys(re.findall(r'\{\{(\w+)\}\}', self.prompt_data['template'])))
        if variables:
            self.vars_frame = ttk.LabelFrame(parent_frame, text="変数入力")
            self.vars_frame.pack(fill='both', expand=True, padx=10, pady=5)

            self.var_entries = {}
            self.first_entry = None

            for var in variables:
                self._create_variable_input_row(var)
        else:
            # 変数が存在しない場合は入力欄を生成せず、空の dict を初期化する
            self.var_entries = {}
            self.first_entry = None

    def _create_variable_input_row(self, var):
        """変数入力行を作成するヘルパー関数。"""
        var_frame = ttk.Frame(self.vars_frame)
        var_frame.pack(fill='both', expand=True, padx=5, pady=4)
        # ラベルを左側に配置
        label_frame = ttk.Frame(var_frame)
        label_frame.pack(side='left', fill='y', padx=(0, 5))
        ttk.Label(label_frame, text=f"{var}:", font=FONTS['input']).pack(side='left', anchor='n', pady=2)

        # テキストウィジェットとスクロールバーを含むフレーム
        text_frame = ttk.Frame(var_frame)
        text_frame.pack(side='left', fill='both', expand=True)

        text = tk.Text(text_frame, width=1, height=3, font=FONTS['input'])
        text.pack(side='left', fill='both', expand=True)

        scrollbar = ttk.Scrollbar(text_frame, orient="vertical", command=text.yview)
        scrollbar.pack(side='right', fill='y')
        text.configure(yscrollcommand=scrollbar.set)

        self.var_entries[var] = text
        if self.first_entry is None:
            self.first_entry = text
        text.bind('<KeyRelease>', self.update_preview)


    def _update_variables_prompt_creation_tab(self):
        """
        テンプレート内の変数の変更に基づいてプロンプト作成タブの変数入力エリアを更新する。
        """
        if not hasattr(self, 'vars_frame') or not self.vars_frame.winfo_exists():
            # vars_frame が存在しない場合は作成
            self._setup_variable_input_area(self.prompt_tab)
        else:
            # vars_frame が存在する場合は、中身を更新
            for child in self.vars_frame.winfo_children():
                child.destroy()
            variables = list(dict.fromkeys(re.findall(r'\{\{(\w+)\}\}', self.prompt_data['template'])))
            if variables:
                for var in variables:
                    self._create_variable_input_row(var)
            else:
                self.var_entries = {}
                self.first_entry = None


    def update_preview(self, event):
        """
        変数入力に基づいてプレビューテキストを更新する。

        テンプレートと変数エントリから値を取得し、プレビューテキストを更新します。
        """
        template = self.prompt_data['template']
        variables = {var: entry.get("1.0", tk.END).strip() for var, entry in self.var_entries.items()}

        # format_mapに渡す辞書を作成 (変数名をキー、空文字列を値とする)
        # format_dict = {var: variables.get(var, '') for var in re.findall(r'\{\{(\w+)\}\}', template)}
        # result = template.format_map(format_dict) # format_mapを使用

        # format_map を使う代わりに、replace で置換処理を行う
        result = template
        for var, value in variables.items():
          result = result.replace(f"{{{{{var}}}}}", value)


        self.preview_text.delete("1.0", tk.END)
        self.preview_text.insert("1.0", result)


    def copy_to_clipboard(self):
        """
        プレビューテキストをクリップボードにコピーする。

        プレビューテキストを取得し、クリップボードにコピーした後、
        コピーボタンのテキストを一時的に「コピーしました」に変更して、
        5秒後に元の「コピー」に戻します。
        """
        preview_text = self.preview_text.get("1.0", tk.END).strip()
        if preview_text:
            self.window.clipboard_clear()
            self.window.clipboard_append(preview_text)
            self.copy_button.config(text="コピーしました")
            self.window.after(5000, lambda: self.copy_button.config(text="コピー"))

    def _update_variables_listbox(self):
        """
        テンプレート内の変数の変更に基づいて変数一覧リストボックスを更新する。(テンプレート編集タブ用)
        """
        template = self.prompt_data['template']
        variables = set(re.findall(r'\{\{(\w+)\}\}', template))
        self.variables_listbox.delete(0, tk.END)
        for var in sorted(variables):
            self.variables_listbox.insert(tk.END, var)

    def _on_template_change_change_tab(self, event=None):
        """
        テンプレートテキストが変更されたときに変数を更新する。(テンプレート編集タブ用)
        """
        template = self.template_text.get("1.0", tk.END)
        variables = set(re.findall(r'\{\{(\w+)\}\}', template))
        self.variables_listbox.delete(0, tk.END)
        for var in sorted(variables):
            self.variables_listbox.insert(tk.END, var)

    def _insert_selected_variable_change_tab(self, event=None):
        """
        選択された変数をテンプレート編集タブのテンプレートテキストに挿入する。(テンプレート編集タブ用)
        """
        selection = self.variables_listbox.curselection()
        if selection:
            variable = self.variables_listbox.get(selection[0])
            current_pos = self.template_text.index(tk.INSERT)
            self.template_text.insert(tk.INSERT, f"{{{{{variable}}}}}")
            self.template_text.mark_set(tk.INSERT, f"{current_pos}+{len(variable)+4}c")
            self.template_text.focus_set()
            self._update_variables_prompt_creation_tab() # テンプレート編集を反映するためにプロンプト作成タブの変数を更新

    def _show_variable_dialog_change_tab(self):
        """
        変数追加ダイアログをテンプレート編集タブから表示する。(テンプレート編集タブ用)
        """
        dialog = tk.Toplevel(self.window)
        dialog.title("変数追加")
        dialog.attributes('-topmost', True)

        dialog.resizable(False, False)
        x, y = calculate_window_position(self.window, *WINDOW_SIZES['variable_dialog'])
        dialog.geometry(f"{WINDOW_SIZES['variable_dialog'][0]}x{WINDOW_SIZES['variable_dialog'][1]}+{x}+{y}")

        ttk.Label(dialog, text="追加する変数名を入力してください:",
                 font=FONTS['input']).pack(padx=10, pady=10)

        var_entry = ttk.Entry(dialog, width=30, font=FONTS['input'])
        var_entry.pack(padx=10, pady=5)
        var_entry.focus_set()

        def add_variable():
            var_name = var_entry.get().strip()
            if var_name:
                current_pos = self.template_text.index(tk.INSERT)
                self.template_text.insert(current_pos, f"{{{{{var_name}}}}}")
                self.template_text.mark_set(tk.INSERT, f"{current_pos}+{len(var_name)+4}c")
                dialog.destroy()
                self._on_template_change_change_tab()
                self.template_text.focus_set()
            else:
                messagebox.showerror("エラー", "変数名を入力してください。")

        var_entry.bind('<Return>', lambda e: add_variable())

        button_frame = ttk.Frame(dialog)
        button_frame.pack(fill='x', padx=10, pady=10)
        ttk.Button(button_frame, text="追加",
                  command=add_variable,
                  style='TButton').pack(side='left', padx=5)
        ttk.Button(button_frame, text="キャンセル",
                  command=dialog.destroy,
                  style='TButton').pack(side='left', padx=5)

    def _save_template_change_tab(self):
        """
        テンプレートの変更を保存する。(テンプレート編集タブ用)

        ユーザーに保存の確認を求め、テンプレートを更新し、UIを編集不可状態に戻します。
        """
        # 保存の確認
        if not messagebox.askyesno("確認", "変更を保存しますか？"):
            return

        # 新しいテンプレートを保存
        new_template = self.template_text.get("1.0", tk.END).strip()
        new_name = self.original_name # テンプレート名は変更しない

        self.prompt_data['template'] = new_template
        self.prompt_data['name'] = new_name # テンプレート名も更新 (念のため)
        self.original_template = new_template # original_templateも更新
        self.original_name = new_name # original_nameも更新

        prompt_manager = PromptManager() # PromptManagerのインスタンスを生成
        # 既存のプロンプトを削除して新しいプロンプトを保存 (nameで検索して削除)
        prompt_manager.delete_prompt(self.original_name)
        prompt_manager.save_prompt(new_name, new_template)

        # UIを編集不可状態に戻す (今回は不要)

        # 変数入力エリアを更新 (プロンプト作成タブの変数入力を更新)
        self._update_variables_prompt_creation_tab()
        # 変数一覧を更新 (テンプレート編集タブの変数一覧を更新)
        self._update_variables_listbox()

        # プレビューを更新
        self.update_preview(None)
        messagebox.showinfo("成功", "テンプレートを保存しました。") # 保存成功メッセージを表示

    def _discard_current_template_input_change_tab(self): # メソッド名変更
        """
        テンプレートの編集を破棄し、元の状態に戻す。(テンプレート編集タブ用)

        ユーザーに破棄の確認を求め、テンプレートを元の状態に戻し、UIを編集不可状態に戻します。
        """
        # 破棄の確認
        if not messagebox.askyesno("確認", "変更を破棄しますか？\n※この操作は取り消せません。"):
            return

        # テンプレートを元の状態に戻す
        self.template_text.delete("1.0", tk.END)
        self.template_text.insert("1.0", self.original_template)

        # UIを編集不可状態に戻す (今回は不要)
        self._update_variables_listbox() # 変数一覧を更新
        self._update_variables_prompt_creation_tab() # プロンプト作成タブの変数入力エリアも更新
        self.update_preview(None) # プレビューを更新


class FlashPromptApp:
    """
    メインアプリケーションウィンドウクラス。

    テンプレート一覧、テンプレート登録、設定のタブを含むメインアプリケーションウィンドウを管理します。
    """
    def __init__(self, root):
        """
        FlashPromptAppクラスのコンストラクタ。

        ルートウィンドウを設定し、UIを初期化し、タブをセットアップします。

        Args:
            root (tk.Tk): Tkinterのルートウィンドウオブジェクト。
        """
        self.root = root
        self.root.title("FlashPrompt")
        self.settings_manager = SettingsManager()
        always_on_top = self.settings_manager.get_settings().get('always_on_top', True)
        self.root.attributes('-topmost', always_on_top)

        # メインウィンドウの最小サイズを設定
        self.root.minsize(*WINDOW_SIZES['main_min'])

        self.prompt_manager = PromptManager()
        self.variables = set()  # 変数の一覧を保持

        # スタイルの設定
        self.style = ttk.Style()
        setup_styles(self.style)

        # タブの作成
        self.notebook = ttk.Notebook(root)
        self.notebook.pack(expand=True, fill='both')

        # キーボードナビゲーションの設定
        self.root.bind('<Left>', self._previous_tab)
        self.root.bind('<Right>', self._next_tab)

        # テンプレート一覧タブ
        self.list_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.list_frame, text='テンプレート一覧')
        self._setup_list_tab()

        # テンプレート登録タブ
        self.template_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.template_frame, text='テンプレート登録')
        self._setup_template_tab()

        # 設定タブ
        self.settings_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.settings_frame, text='設定')
        self._setup_settings_tab()

    def _setup_list_tab(self):
        """
        「テンプレート一覧」タブのUIをセットアップする。

        プロンプト作成ボタン、削除ボタン、テンプレート一覧のTreeViewを作成します。
        """
        button_frame = ttk.Frame(self.list_frame)
        button_frame.pack(pady=10, padx=10)

        ttk.Button(button_frame, text='プロンプト作成', 
                  command=self._open_prompt_creation,
                  style='TButton').pack(side='left', padx=5)
        ttk.Button(button_frame, text='テンプレート編集',
                  command=self._open_template_edit,
                  style='TButton').pack(side='left', padx=5)
        ttk.Button(button_frame, text='削除',
                  command=self._delete_prompt,
                  style='Danger.TButton').pack(side='left', padx=5)

        # テンプレート一覧の表示（下部に配置）
        list_frame = ttk.Frame(self.list_frame)
        list_frame.pack(fill='both', expand=True, padx=10)

        # TreeViewの作成（ヘッダー非表示）
        self.prompt_list = ttk.Treeview(list_frame,
                                      columns=('name',),
                                      show='tree',  # ヘッダーを非表示にする
                                      height=10)
        self.prompt_list.column('#0', width=0, stretch=False)  # 最初の列を非表示
        self.prompt_list.column('name', width=200)
        self.prompt_list.pack(fill='both', expand=True)

        # キーボードナビゲーションとダブルクリックの設定
        self.prompt_list.bind('<Double-Button-1>', self._open_prompt_creation)
        self.prompt_list.bind('<Return>', self._open_prompt_creation)
        self.prompt_list.bind('<Up>', self._navigate_list)
        self.prompt_list.bind('<Down>', self._navigate_list)

        self._update_prompt_list()

    def _open_prompt_creation(self, event=None):
        selection = self.prompt_list.selection()
        always_on_top = self.settings_manager.get_settings().get('always_on_top', True)
        if not selection:
            items = self.prompt_list.get_children()
            if items:
                selection = (items[0],)
        if selection:
            prompt_name = str(self.prompt_list.item(selection[0])['values'][0])
            if prompt_name:
                prompt_data = self.prompt_manager.get_prompt(prompt_name)
                if prompt_data is not None:
                    PromptCreationWindow(self.root, prompt_data, always_on_top=always_on_top)
        else:
            # 「プロンプト作成」ボタンから新規作成する場合
            PromptCreationWindow(self.root, {'name': '新しいプロンプト', 'template': ''}, always_on_top=always_on_top)

    def _delete_prompt(self):
        selection = self.prompt_list.selection()
        if selection:
            prompt_name = str(self.prompt_list.item(selection[0])['values'][0])
            if messagebox.askyesno("確認", f"プロンプト '{prompt_name}' を削除しますか？"):
                self.prompt_manager.delete_prompt(prompt_name)
                self._update_prompt_list()

    def _setup_template_tab(self):
        """
        「テンプレート登録」タブのUIをセットアップする。

        テンプレート名入力欄、テンプレートテキストエリア、変数一覧リストボックス、ボタンを作成します。
        """
        # メインコンテンツを左右に分けるフレーム
        content_frame = ttk.Frame(self.template_frame, style='TFrame')
        content_frame.pack(fill='both', expand=True, padx=10, pady=10)

        # 左側フレーム（入力エリア）
        left_frame = ttk.LabelFrame(content_frame, text="テンプレート登録", style='TLabelframe')
        left_frame.pack(side='left', fill='both', expand=True, padx=(0, 10))

        # テンプレート名入力
        name_frame = ttk.Frame(left_frame, style='TFrame')
        name_frame.pack(fill='x', pady=10, padx=10)
        ttk.Label(name_frame, text="テンプレート名:", style='TLabel').pack(side='left')
        self.template_name_entry = ttk.Entry(name_frame, width=40, style='TEntry', font=FONTS['input'])
        self.template_name_entry.pack(side='left', padx=5)

        # テンプレート入力エリア
        template_label_frame = ttk.Frame(left_frame, style='TFrame')
        template_label_frame.pack(fill='x', padx=10)
        ttk.Label(template_label_frame, text="テンプレート:", style='TLabel').pack(side='left')

        self.template_text = tk.Text(left_frame, height=10, width=50,
                                   font=FONTS['input'],
                                   bg=COLORS['surface'],
                                   fg=COLORS['text'])
        self.template_text.pack(padx=10, pady=5, fill='both', expand=True)
        self.template_text.bind('<KeyRelease>', self._on_template_change)

        # 右側フレーム（変数一覧）
        right_frame = ttk.LabelFrame(content_frame, text="変数一覧", style='TLabelframe')
        right_frame.pack(side='right', fill='both', padx=(10, 0))

        self.variables_listbox = tk.Listbox(right_frame,
                                          width=20,
                                          font=FONTS['input'],
                                          bg=COLORS['surface'],
                                          fg=COLORS['text'],
                                          selectmode='single',
                                          activestyle='none',
                                          selectbackground=COLORS['primary'],
                                          selectforeground=COLORS['surface'])
        self.variables_listbox.pack(padx=10, pady=10, fill='both', expand=True)
        self.variables_listbox.configure(height=10)
        self.variables_listbox.bind('<Double-Button-1>', self._insert_selected_variable_template_tab)

        # 変数操作ボタンフレーム
        var_button_frame = ttk.Frame(right_frame, style='TFrame')
        var_button_frame.pack(fill='x', padx=10, pady=10)
        ttk.Button(var_button_frame, text="変数追加",
                  command=self._show_variable_dialog_template_tab,
                  style='TButton').pack(side='left', padx=5)
        ttk.Button(var_button_frame, text="変数挿入",
                  command=self._insert_selected_variable_template_tab,
                  style='TButton').pack(side='left', padx=5)

        # ボタンフレーム
        button_frame = ttk.Frame(self.template_frame, style='TFrame')
        button_frame.pack(fill='x', padx=10, pady=10)
        ttk.Button(button_frame, text="保存",
                  command=self._save_template_tab,
                  style='TButton').pack(side='left', padx=5)
        ttk.Button(button_frame, text="破棄",
                  command=self._discard_current_template_input_tab, # メソッド名変更
                  style='TButton').pack(side='left', padx=5)

    def _on_template_change(self, event=None):
        """
        テンプレートテキストが変更されたときに変数を更新する。(テンプレート登録タブ用)
        """
        template = self.template_text.get("1.0", tk.END)
        variables = set(re.findall(r'\{\{(\w+)\}\}', template))
        self.variables_listbox.delete(0, tk.END)
        for var in sorted(variables):
            self.variables_listbox.insert(tk.END, var)

    def _insert_selected_variable_template_tab(self, event=None):
        """
        選択された変数をテンプレートテキストに挿入する。(テンプレート登録タブ用)
        """
        selection = self.variables_listbox.curselection()
        if selection:
            variable = self.variables_listbox.get(selection[0])
            current_pos = self.template_text.index(tk.INSERT)
            self.template_text.insert(tk.INSERT, f"{{{{{variable}}}}}")
            self.template_text.mark_set(tk.INSERT, f"{current_pos}+{len(variable)+4}c")
            self.template_text.focus_set()

    def _show_variable_dialog_template_tab(self):
        """
        変数追加ダイアログを表示する。(テンプレート登録タブ用)
        """
        dialog = tk.Toplevel(self.root)
        dialog.title("変数追加")
        dialog.attributes('-topmost', True)

        dialog.resizable(False, False)
        x, y = calculate_window_position(self.root, *WINDOW_SIZES['variable_dialog'])
        dialog.geometry(f"{WINDOW_SIZES['variable_dialog'][0]}x{WINDOW_SIZES['variable_dialog'][1]}+{x}+{y}")

        ttk.Label(dialog, text="追加する変数名を入力してください:",
                 font=FONTS['input']).pack(padx=10, pady=10)

        var_entry = ttk.Entry(dialog, width=30, font=FONTS['input'])
        var_entry.pack(padx=10, pady=5)
        var_entry.focus_set()

        def add_variable():
            var_name = var_entry.get().strip()
            if var_name:
                current_pos = self.template_text.index(tk.INSERT)
                self.template_text.insert(current_pos, f"{{{{{var_name}}}}}")
                self.template_text.mark_set(tk.INSERT, f"{current_pos}+{len(var_name)+4}c")
                dialog.destroy()
                self._on_template_change()
                self.template_text.focus_set()
            else:
                messagebox.showerror("エラー", "変数名を入力してください。")

        var_entry.bind('<Return>', lambda e: add_variable())

        button_frame = ttk.Frame(dialog)
        button_frame.pack(fill='x', padx=10, pady=10)
        ttk.Button(button_frame, text="追加",
                  command=add_variable,
                  style='TButton').pack(side='left', padx=5)
        ttk.Button(button_frame, text="キャンセル",
                  command=dialog.destroy,
                  style='TButton').pack(side='left', padx=5)

    def _save_template_tab(self):
        """
        テンプレートを保存する。(テンプレート登録タブ用)
        """
        name = self.template_name_entry.get().strip()
        template = self.template_text.get("1.0", tk.END).strip()

        if not name:
            messagebox.showerror("エラー", "テンプレート名を入力してください。")
            return

        if not template:
            messagebox.showerror("エラー", "テンプレートを入力してください。")
            return

        self.prompt_manager.save_prompt(name, template)
        self._update_prompt_list()
        self._clear_template_fields_tab()
        messagebox.showinfo("成功", "テンプレートを保存しました。")

    def _discard_current_template_input_tab(self): # メソッド名変更
        """
        現在のテンプレート入力を破棄する。(テンプレート登録タブ用)
        """
        if self.template_name_entry.get().strip() or self.template_text.get("1.0", tk.END).strip():
            if messagebox.askyesno("確認", "入力内容を破棄してもよろしいですか？"):
                self._clear_template_fields_tab()
        else:
            self._clear_template_fields_tab()

    def _clear_template_fields_tab(self):
        """
        テンプレート名とテキストフィールドをクリアする。(テンプレート登録タブ用)
        """
        self.template_name_entry.delete(0, tk.END)
        self.template_text.delete("1.0", tk.END)

    def _update_prompt_list(self):
        for item in self.prompt_list.get_children():
            self.prompt_list.delete(item)
        for prompt in self.prompt_manager.prompts:
            self.prompt_list.insert('', 'end', values=(str(prompt['name']),)) # テンプレート名を文字列に変換して挿入

    def _setup_settings_tab(self):
        """
        「設定」タブのUIをセットアップする。

        保存ディレクトリ設定UIに加えて、ウィンドウの最前面表示のオン/オフ設定を作成します。
        """
        # メインコンテンツを配置するフレーム
        content_frame = ttk.Frame(self.settings_frame, style='TFrame')
        content_frame.pack(fill='both', expand=True, padx=10, pady=10)

        # 保存ディレクトリ設定
        dir_frame = ttk.LabelFrame(content_frame, text="保存ディレクトリ", style='TLabelframe')
        dir_frame.pack(fill='x', padx=5, pady=5)

        # 現在の設定を取得
        settings = self.settings_manager.get_settings()

        # ディレクトリ入力フレーム
        input_frame = ttk.Frame(dir_frame, style='TFrame')
        input_frame.pack(fill='x', padx=10, pady=10)

        # ディレクトリパス入力欄
        self.dir_entry = ttk.Entry(input_frame, width=40, style='TEntry', font=FONTS['input'])
        self.dir_entry.pack(side='left', padx=(0, 5), fill='x', expand=True)
        self.dir_entry.insert(0, settings.get('save_directory', ''))

        # 参照ボタン
        browse_btn = ttk.Button(input_frame, text="参照", command=self._browse_directory)
        browse_btn.pack(side='left')

        # 新たに「常に最前面に表示」設定を追加
        topmost_frame = ttk.Frame(content_frame, style='TFrame')
        topmost_frame.pack(fill='x', padx=5, pady=5)
        self.topmost_var = tk.BooleanVar(value=settings.get('always_on_top', True))
        topmost_check = ttk.Checkbutton(topmost_frame, text="ウィンドウを常に最前面に表示", variable=self.topmost_var)
        topmost_check.pack(side='left', padx=10, pady=5)

        # 保存ボタン
        save_frame = ttk.Frame(content_frame, style='TFrame')
        save_frame.pack(fill='x', padx=5, pady=10)
        save_btn = ttk.Button(save_frame, text="設定を保存", command=self._save_settings)
        save_btn.pack(side='right')

    def _browse_directory(self):
        """
        ディレクトリ参照ダイアログを開き、保存ディレクトリを選択する。

        ユーザーにディレクトリを選択させ、ディレクトリ入力欄を更新します。
        """
        current_dir = self.dir_entry.get() or os.path.expanduser("~")
        directory = filedialog.askdirectory(
            initialdir=current_dir,
            title="保存ディレクトリを選択"
        )
        if directory:
            self.dir_entry.delete(0, tk.END)
            self.dir_entry.insert(0, directory)

    def _save_settings(self):
        """
        設定を保存する。

        UIから設定値を取得し、SettingsManagerを使用して保存、さらに
        ルートウィンドウの常に最前面表示の設定を更新します。
        """
        settings = self.settings_manager.get_settings()
        settings['save_directory'] = self.dir_entry.get()
        settings['always_on_top'] = self.topmost_var.get()
        self.settings_manager.save_settings(settings)
        self.root.attributes('-topmost', self.topmost_var.get())
        messagebox.showinfo("成功", "設定を保存しました。")

    def _next_tab(self, event=None):
        """
        次のタブに移動する。

        キーボードナビゲーション（右キー）用。 テキスト入力ウィジェットにフォーカスがない場合にのみタブを切り替えます。
        """
        if event and event.widget.winfo_class() in ('Text', 'TEntry', 'Entry'):
            return
        current = self.notebook.index('current')
        if current < self.notebook.index('end') - 1:
            self.notebook.select(current + 1)
        return 'break'

    def _previous_tab(self, event=None):
        """
        前のタブに移動する。

        キーボードナビゲーション（左キー）用。 テキスト入力ウィジェットにフォーカスがない場合にのみタブを切り替えます。
        """
        if event and event.widget.winfo_class() in ('Text', 'TEntry', 'Entry'):
            return
        current = self.notebook.index('current')
        if current > 0:
            self.notebook.select(current - 1)
        return 'break'

    def _navigate_list(self, event):
        """
        テンプレート一覧をキーボードでナビゲートする。

        上下キーでリスト選択を移動し、リストの端でループしないようにします。
        """
        items = self.prompt_list.get_children()
        if not items:
            return 'break'

        selection = self.prompt_list.selection()
        if not selection:
            # リストが空でない場合、最初のアイテムを選択
            self.prompt_list.selection_set(items[0])
            self.prompt_list.focus(items[0])
            return 'break'

        current_idx = items.index(selection[0])
        next_idx = current_idx

        if event.keysym == 'Up' and current_idx > 0:
            next_idx = current_idx - 1
        elif event.keysym == 'Down' and current_idx < len(items) - 1:
            next_idx = current_idx + 1

        self.prompt_list.selection_set(items[next_idx])
        self.prompt_list.focus(items[next_idx])
        self.prompt_list.see(items[next_idx])  # 選択したアイテムが見えるようにスクロール

        return 'break'

    def _open_template_edit(self, event=None):
        """テンプレート編集用のウィンドウを開く"""
        selection = self.prompt_list.selection()
        if not selection:
            messagebox.showwarning("警告", "編集するプロンプトを選択してください")
            return
            
        prompt_name = str(self.prompt_list.item(selection[0])['values'][0])
        prompt_data = self.prompt_manager.get_prompt(prompt_name)
        if prompt_data:
            always_on_top = self.settings_manager.get_settings().get('always_on_top', True)
            window = PromptCreationWindow(self.root, prompt_data, always_on_top=always_on_top)
            window.notebook.select(window.template_change_tab)  # テンプレート編集タブを選択
        else:
            messagebox.showerror("エラー", "プロンプトが見つかりませんでした。")