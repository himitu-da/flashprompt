import tkinter as tk
from tkinter import ttk, messagebox
import os
import json
import re

class PromptManager:
    def __init__(self):
        self.appdata_path = os.path.join(os.getenv('LOCALAPPDATA'), 'flashprompt')
        self.prompts_file = os.path.join(self.appdata_path, 'prompts.json')
        self._ensure_directory()
        self.prompts = self._load_prompts()

    def _ensure_directory(self):
        if not os.path.exists(self.appdata_path):
            os.makedirs(self.appdata_path)
        if not os.path.exists(self.prompts_file):
            with open(self.prompts_file, 'w', encoding='utf-8') as f:
                json.dump([], f)

    def _load_prompts(self):
        try:
            with open(self.prompts_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            return []

    def save_prompt(self, name, template):
        prompt = {
            'name': name,
            'template': template
        }
        self.prompts.append(prompt)
        self._save_to_file()
        
    def _save_to_file(self):
        with open(self.prompts_file, 'w', encoding='utf-8') as f:
            json.dump(self.prompts, f, ensure_ascii=False, indent=2)

    def delete_prompt(self, name):
        self.prompts = [p for p in self.prompts if p['name'] != name]
        self._save_to_file()

    def get_prompt(self, name):
        for prompt in self.prompts:
            if prompt['name'] == name:
                return prompt
        return None

class PromptCreationWindow:
    def __init__(self, parent, prompt_data):
        self.window = tk.Toplevel(parent)
        self.window.title("プロンプト作成")
        self.window.attributes('-topmost', True)
        
        # ウィンドウのサイズを設定
        window_width = 600
        window_height = 400
        self.window.resizable(True, True)
        
        # プロンプト作成ウィンドウの最小サイズを設定
        self.window.minsize(500, 500)
        
        # 親ウィンドウの位置とサイズを取得
        parent_x = parent.winfo_x()
        parent_y = parent.winfo_y()
        parent_width = parent.winfo_width()
        parent_height = parent.winfo_height()
        
        # スクリーンのサイズを取得
        screen_width = parent.winfo_screenwidth()
        screen_height = parent.winfo_screenheight()
        
        # ウィンドウを親ウィンドウの中心に配置
        x = parent_x + (parent_width - window_width) // 2
        y = parent_y + (parent_height - window_height) // 2
        
        # 画面からはみ出ないように位置を調整
        x = max(0, min(x, screen_width - window_width))
        y = max(0, min(y, screen_height - window_height))
        
        self.window.geometry(f"{window_width}x{window_height}+{x}+{y}")
        
        self.prompt_data = prompt_data
        self.setup_ui()
        
    def setup_ui(self):
        # プロンプト名表示
        name_frame = ttk.Frame(self.window)
        name_frame.pack(fill='x', padx=10, pady=5)
        ttk.Label(name_frame, text="プロンプト名:", font=('Segoe UI', 11)).pack(side='left')
        name_label = ttk.Label(name_frame, text=self.prompt_data['name'], font=('Segoe UI', 11))
        name_label.pack(side='left', padx=5)

        # テンプレート表示
        template_frame = ttk.Frame(self.window)
        template_frame.pack(fill='x', padx=10, pady=5)
        ttk.Label(template_frame, text="テンプレート:", font=('Segoe UI', 11)).pack(anchor='w')
        template_text = tk.Text(template_frame, height=3, width=50, font=('Segoe UI', 11))
        template_text.insert("1.0", self.prompt_data['template'])
        template_text.config(state='disabled')
        template_text.pack(pady=5)

        # 変数入力エリア
        self.vars_frame = ttk.LabelFrame(self.window, text="変数入力")
        self.vars_frame.pack(fill='x', padx=10, pady=5)
        
        # テンプレートから変数を抽出（重複を除去）
        variables = list(dict.fromkeys(re.findall(r'\{\{(\w+)\}\}', self.prompt_data['template'])))
        self.var_entries = {}
        
        # 最初の変数のエントリーを記録
        self.first_entry = None
        
        for var in variables:
            var_frame = ttk.Frame(self.vars_frame)
            var_frame.pack(fill='x', padx=5, pady=4)
            ttk.Label(var_frame, text=f"{var}:", font=('Segoe UI', 11)).pack(side='left')
            entry = ttk.Entry(var_frame, width=40, font=('Segoe UI', 11))
            entry.pack(side='left', padx=5)
            self.var_entries[var] = entry
            # 最初の変数のエントリーを記録
            if self.first_entry is None:
                self.first_entry = entry
            # エントリーの変更を監視
            entry.bind('<KeyRelease>', self.update_preview)

        # プレビューエリア
        preview_frame = ttk.LabelFrame(self.window, text="生成されたプロンプト")
        preview_frame.pack(fill='both', expand=True, padx=10, pady=5)
        
        self.preview_text = tk.Text(preview_frame, height=5, width=50, font=('Segoe UI', 11))
        self.preview_text.pack(padx=5, pady=5, fill='both', expand=True)
        
        # コピーボタン
        copy_btn = ttk.Button(self.window, text="コピー", command=self.copy_to_clipboard)
        copy_btn.pack(pady=10)

        # 初期プレビューを生成
        self.update_preview(None)

        # 最初の変数入力欄にフォーカスを移動
        if self.first_entry:
            self.first_entry.focus_set()
            self.first_entry.select_range(0, tk.END)  # テキストを全選択

    def update_preview(self, event):
        template = self.prompt_data['template']
        variables = {var: entry.get() for var, entry in self.var_entries.items()}
        
        try:
            # テンプレート内の二重波括弧を一時的に単一波括弧に変換
            template_single_braces = re.sub(r'\{\{(\w+)\}\}', r'{\1}', template)
            result = template_single_braces.format(**variables)
            self.preview_text.delete("1.0", tk.END)
            self.preview_text.insert("1.0", result)
        except KeyError:
            # 未入力の変数がある場合は何もしない
            pass

    def copy_to_clipboard(self):
        preview_text = self.preview_text.get("1.0", tk.END).strip()
        if preview_text:
            self.window.clipboard_clear()
            self.window.clipboard_append(preview_text)
            messagebox.showinfo("成功", "クリップボードにコピーしました。")

class FlashPromptApp:
    # カラーパレット
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

    def __init__(self, root):
        self.root = root
        self.root.title("FlashPrompt")
        self.root.attributes('-topmost', True)
        
        # メインウィンドウの最小サイズを設定
        self.root.minsize(300, 300)
        
        self.prompt_manager = PromptManager()
        self.variables = set()  # 変数の一覧を保持
        
        # スタイルの設定
        self.style = ttk.Style()
        self.style.theme_use('clam')
        
        # 基本スタイル
        self.style.configure('TFrame', background=self.COLORS['background'])
        self.style.configure('TLabelframe', background=self.COLORS['background'])
        self.style.configure('TLabelframe.Label', 
                           background=self.COLORS['background'],
                           foreground=self.COLORS['text'],
                           font=('Segoe UI', 10, 'bold'))
        
        # ノートブックスタイル
        self.style.configure('TNotebook', 
                           background=self.COLORS['surface'],
                           tabmargins=[2, 5, 2, 0])
        self.style.configure('TNotebook.Tab',
                           padding=[15, 5],
                           background=self.COLORS['surface'],
                           foreground=self.COLORS['text'],
                           font=('Segoe UI', 9))
        self.style.map('TNotebook.Tab',
                      background=[('selected', self.COLORS['primary'])],
                      foreground=[('selected', self.COLORS['surface'])])
        
        # ボタンスタイル
        self.style.configure('TButton',
                           padding=[15, 8],
                           background=self.COLORS['primary'],
                           foreground=self.COLORS['surface'],
                           font=('Segoe UI', 9))
        self.style.map('TButton',
                      background=[('active', self.COLORS['primary_hover'])],
                      relief=[('pressed', 'flat')])
        
        # 危険ボタンスタイル
        self.style.configure('Danger.TButton',
                           padding=[15, 8],
                           background=self.COLORS['danger'],
                           foreground=self.COLORS['surface'],
                           font=('Segoe UI', 9))
        self.style.map('Danger.TButton',
                      background=[('active', self.COLORS['danger_hover'])],
                      relief=[('pressed', 'flat')])
        
        # ラベルスタイル
        self.style.configure('TLabel',
                           background=self.COLORS['background'],
                           foreground=self.COLORS['text'],
                           font=('Segoe UI', 9))
        
        # エントリースタイル
        self.style.configure('TEntry',
                           fieldbackground=self.COLORS['surface'],
                           foreground=self.COLORS['text'],
                           padding=[5, 5],
                           font=('Segoe UI', 9))
        
        # ツリービュースタイル
        self.style.configure('Treeview',
                           background=self.COLORS['surface'],
                           foreground=self.COLORS['text'],
                           rowheight=30,
                           fieldbackground=self.COLORS['surface'],
                           font=('Segoe UI', 9))
        self.style.configure('Treeview.Heading',
                           background=self.COLORS['secondary'],
                           foreground=self.COLORS['surface'],
                           font=('Segoe UI', 9, 'bold'))
        self.style.map('Treeview',
                      background=[('selected', self.COLORS['primary'])],
                      foreground=[('selected', self.COLORS['surface'])])
        
        # タブの作成
        self.notebook = ttk.Notebook(root)
        self.notebook.pack(expand=True, fill='both')
        
        # プロンプト一覧タブ
        self.list_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.list_frame, text='プロンプト一覧')
        self._setup_list_tab()
        
        # テンプレート登録タブ
        self.template_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.template_frame, text='テンプレート登録')
        self._setup_template_tab()

    def _setup_list_tab(self):
        # メインのコンテナフレーム
        container_frame = ttk.Frame(self.list_frame, style='TFrame')
        container_frame.pack(fill='both', expand=True, padx=10, pady=10)
        
        # ボタンフレーム（上部に配置）
        button_frame = ttk.Frame(container_frame, style='TFrame')
        button_frame.pack(fill='x', padx=0, pady=(0, 10))
        ttk.Button(button_frame, text="プロンプト作成",
                  command=self._open_prompt_creation,
                  style='TButton').pack(side='left', padx=5)
        ttk.Button(button_frame, text="プロンプト削除",
                  command=self._delete_prompt,
                  style='Danger.TButton').pack(side='left', padx=5)

        # プロンプト一覧の表示（下部に配置）
        list_frame = ttk.Frame(container_frame, style='TFrame')
        list_frame.pack(fill='both', expand=True)
        self.prompt_listbox = tk.Listbox(list_frame,
                                          width=50,
                                          font=('Segoe UI', 11),
                                          bg=self.COLORS['surface'],
                                          fg=self.COLORS['text'],
                                          selectmode='single',
                                          activestyle='none',
                                          selectbackground=self.COLORS['primary'],
                                          selectforeground=self.COLORS['surface'])
        self.prompt_listbox.pack(fill='both', expand=True)
        # リストボックスの行の高さを設定
        self.prompt_listbox.configure(height=10)
        self.prompt_listbox.bind('<Double-Button-1>', self._open_prompt_creation)
        self._update_prompt_list()

    def _open_prompt_creation(self, event=None):
        selection = self.prompt_listbox.curselection()
        if selection:
            prompt_name = self.prompt_listbox.get(selection[0])
            prompt_data = self.prompt_manager.get_prompt(prompt_name)
            if prompt_data:
                PromptCreationWindow(self.root, prompt_data)

    def _delete_prompt(self):
        selection = self.prompt_listbox.curselection()
        if selection:
            prompt_name = self.prompt_listbox.get(selection[0])
            self.prompt_manager.delete_prompt(prompt_name)
            self._update_prompt_list()

    def _setup_template_tab(self):
        # メインコンテンツを左右に分けるフレーム
        content_frame = ttk.Frame(self.template_frame, style='TFrame')
        content_frame.pack(fill='both', expand=True, padx=10, pady=10)

        # 左側フレーム（入力エリア）
        left_frame = ttk.LabelFrame(content_frame, text="テンプレート作成", style='TLabelframe')
        left_frame.pack(side='left', fill='both', expand=True, padx=(0, 10))

        # プロンプト名入力
        name_frame = ttk.Frame(left_frame, style='TFrame')
        name_frame.pack(fill='x', pady=10, padx=10)
        ttk.Label(name_frame, text="プロンプト名:", style='TLabel').pack(side='left')
        self.template_name_entry = ttk.Entry(name_frame, width=40, style='TEntry', font=('Segoe UI', 11))
        self.template_name_entry.pack(side='left', padx=5)

        # テンプレート入力エリア
        template_label_frame = ttk.Frame(left_frame, style='TFrame')
        template_label_frame.pack(fill='x', padx=10)
        ttk.Label(template_label_frame, text="テンプレート:", style='TLabel').pack(side='left')
        
        # テンプレート入力用のテキストエリア
        self.template_text = tk.Text(left_frame, height=10, width=50,
                                   font=('Segoe UI', 11),
                                   bg=self.COLORS['surface'],
                                   fg=self.COLORS['text'])
        self.template_text.pack(padx=10, pady=5, fill='both', expand=True)
        # テンプレート変更時のイベントを追加
        self.template_text.bind('<KeyRelease>', self._on_template_change)

        # 右側フレーム（変数一覧）
        right_frame = ttk.LabelFrame(content_frame, text="変数一覧", style='TLabelframe')
        right_frame.pack(side='right', fill='both', padx=(10, 0))

        # 変数一覧のリストボックス
        self.variables_listbox = tk.Listbox(right_frame,
                                          width=20,
                                          font=('Segoe UI', 11),
                                          bg=self.COLORS['surface'],
                                          fg=self.COLORS['text'],
                                          selectmode='single',
                                          activestyle='none',
                                          selectbackground=self.COLORS['primary'],
                                          selectforeground=self.COLORS['surface'])
        self.variables_listbox.pack(padx=10, pady=10, fill='both', expand=True)
        # リストボックスの行の高さを設定
        self.variables_listbox.configure(height=10)
        self.variables_listbox.bind('<Double-Button-1>', self._insert_selected_variable)

        # 変数操作ボタンフレーム
        var_button_frame = ttk.Frame(right_frame, style='TFrame')
        var_button_frame.pack(fill='x', padx=10, pady=10)
        ttk.Button(var_button_frame, text="変数追加",
                  command=self._show_variable_dialog,
                  style='TButton').pack(side='left', padx=5)
        ttk.Button(var_button_frame, text="変数挿入",
                  command=self._insert_selected_variable,
                  style='TButton').pack(side='left', padx=5)

        # ボタンフレーム
        button_frame = ttk.Frame(self.template_frame, style='TFrame')
        button_frame.pack(fill='x', padx=10, pady=10)
        ttk.Button(button_frame, text="保存",
                  command=self._save_template,
                  style='TButton').pack(side='left', padx=5)
        ttk.Button(button_frame, text="破棄",
                  command=self._discard_template,
                  style='Danger.TButton').pack(side='left', padx=5)

    def _on_template_change(self, event=None):
        """テンプレート本文が変更されたときに呼び出される関数"""
        template = self.template_text.get("1.0", tk.END).strip()
        # テンプレートから変数を抽出
        variables = set(re.findall(r'\{\{(\w+)\}\}', template))
        # 変数一覧を更新
        self.variables_listbox.delete(0, tk.END)
        for var in sorted(variables):
            self.variables_listbox.insert(tk.END, var)

    def _insert_selected_variable(self, event=None):
        """変数一覧から選択された変数をテンプレートに挿入する"""
        selection = self.variables_listbox.curselection()
        if selection:
            variable = self.variables_listbox.get(selection[0])
            current_pos = self.template_text.index(tk.INSERT)
            self.template_text.insert(tk.INSERT, f"{{{{{variable}}}}}")
            # カーソルを変数の直後に移動
            self.template_text.mark_set(tk.INSERT, f"{current_pos}+{len(variable)+4}c")
            self.template_text.focus_set()

    def _show_variable_dialog(self):
        """変数追加ダイアログを表示する"""
        dialog = tk.Toplevel(self.root)
        dialog.title("変数追加")
        dialog.attributes('-topmost', True)
        
        # ダイアログのサイズを設定
        dialog_width = 300
        dialog_height = 150
        dialog.resizable(False, False)
        
        # メインウィンドウの位置とサイズを取得
        root_x = self.root.winfo_x()
        root_y = self.root.winfo_y()
        root_width = self.root.winfo_width()
        root_height = self.root.winfo_height()
        
        # スクリーンのサイズを取得
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        
        # ダイアログをメインウィンドウの中心に配置
        x = root_x + (root_width - dialog_width) // 2
        y = root_y + (root_height - dialog_height) // 2
        
        # 画面からはみ出ないように位置を調整
        x = max(0, min(x, screen_width - dialog_width))
        y = max(0, min(y, screen_height - dialog_height))
        
        dialog.geometry(f"{dialog_width}x{dialog_height}+{x}+{y}")
        
        # 説明ラベル
        ttk.Label(dialog, text="追加する変数名を入力してください:",
                 font=('Segoe UI', 11)).pack(padx=10, pady=10)
        
        # 変数名入力フィールド
        var_entry = ttk.Entry(dialog, width=30, font=('Segoe UI', 11))
        var_entry.pack(padx=10, pady=5)
        var_entry.focus_set()
        
        def add_variable():
            var_name = var_entry.get().strip()
            if var_name:
                # 変数名が有効な場合、テンプレートにカーソル位置に挿入
                current_pos = self.template_text.index(tk.INSERT)
                self.template_text.insert(current_pos, f"{{{{{var_name}}}}}")
                # カーソルを変数の直後に移動
                self.template_text.mark_set(tk.INSERT, f"{current_pos}+{len(var_name)+4}c")
                dialog.destroy()
                # テンプレート変更イベントを手動で発火させて変数一覧を更新
                self._on_template_change()
                # フォーカスをテンプレートテキストエリアに移動
                self.template_text.focus_set()
            else:
                messagebox.showerror("エラー", "変数名を入力してください。")
        
        # Enterキーでも追加できるようにする
        var_entry.bind('<Return>', lambda e: add_variable())
        
        # ボタンフレーム
        button_frame = ttk.Frame(dialog)
        button_frame.pack(fill='x', padx=10, pady=10)
        ttk.Button(button_frame, text="追加",
                  command=add_variable,
                  style='TButton').pack(side='left', padx=5)
        ttk.Button(button_frame, text="キャンセル",
                  command=dialog.destroy,
                  style='Danger.TButton').pack(side='left', padx=5)

    def _save_template(self):
        name = self.template_name_entry.get().strip()
        template = self.template_text.get("1.0", tk.END).strip()
        
        if not name:
            messagebox.showerror("エラー", "プロンプト名を入力してください。")
            return
            
        if not template:
            messagebox.showerror("エラー", "テンプレートを入力してください。")
            return

        self.prompt_manager.save_prompt(name, template)
        self._update_prompt_list()
        self._clear_template_fields()
        messagebox.showinfo("成功", "テンプレートを保存しました。")

    def _discard_template(self):
        if self.template_name_entry.get().strip() or self.template_text.get("1.0", tk.END).strip():
            if messagebox.askyesno("確認", "入力内容を破棄してもよろしいですか？"):
                self._clear_template_fields()
        else:
            self._clear_template_fields()

    def _clear_template_fields(self):
        self.template_name_entry.delete(0, tk.END)
        self.template_text.delete("1.0", tk.END)

    def _update_prompt_list(self):
        self.prompt_listbox.delete(0, tk.END)
        for prompt in self.prompt_manager.prompts:
            self.prompt_listbox.insert(tk.END, prompt['name'])

def main():
    root = tk.Tk()
    app = FlashPromptApp(root)
    root.mainloop()

if __name__ == "__main__":
    main()
