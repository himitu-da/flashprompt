import tkinter as tk
from tkinter import ttk, messagebox
import re
from models import PromptManager
from constants import COLORS, FONTS, WINDOW_SIZES
from utils import setup_styles, calculate_window_position

class PromptCreationWindow:
    def __init__(self, parent, prompt_data):
        self.window = tk.Toplevel(parent)
        self.window.title("プロンプト作成")
        self.window.attributes('-topmost', True)
        
        # ウィンドウのサイズを設定
        self.window.resizable(True, True)
        self.window.minsize(*WINDOW_SIZES['prompt_creation_min'])
        
        # ウィンドウの位置を計算
        x, y = calculate_window_position(parent, *WINDOW_SIZES['prompt_creation'])
        self.window.geometry(f"{WINDOW_SIZES['prompt_creation'][0]}x{WINDOW_SIZES['prompt_creation'][1]}+{x}+{y}")
        
        self.prompt_data = prompt_data
        self.setup_ui()

    def setup_ui(self):
        # プロンプト名表示
        name_frame = ttk.Frame(self.window)
        name_frame.pack(fill='x', padx=10, pady=5)
        ttk.Label(name_frame, text="プロンプト名:", font=FONTS['input']).pack(side='left')
        name_label = ttk.Label(name_frame, text=self.prompt_data['name'], font=FONTS['input'])
        name_label.pack(side='left', padx=5)

        # テンプレート表示
        template_frame = ttk.Frame(self.window)
        template_frame.pack(fill='x', padx=10, pady=5)
        ttk.Label(template_frame, text="テンプレート:", font=FONTS['input']).pack(anchor='w')
        template_text = tk.Text(template_frame, height=3, width=50, font=FONTS['input'])
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
            ttk.Label(var_frame, text=f"{var}:", font=FONTS['input']).pack(side='left')
            entry = ttk.Entry(var_frame, width=40, font=FONTS['input'])
            entry.pack(side='left', padx=5)
            self.var_entries[var] = entry
            if self.first_entry is None:
                self.first_entry = entry
            entry.bind('<KeyRelease>', self.update_preview)

        # プレビューエリア
        preview_frame = ttk.LabelFrame(self.window, text="生成されたプロンプト")
        preview_frame.pack(fill='both', expand=True, padx=10, pady=5)
        
        self.preview_text = tk.Text(preview_frame, height=5, width=50, font=FONTS['input'])
        self.preview_text.pack(padx=5, pady=5, fill='both', expand=True)
        
        # コピーボタン
        copy_btn = ttk.Button(self.window, text="コピー", command=self.copy_to_clipboard)
        copy_btn.pack(pady=10)

        # 初期プレビューを生成
        self.update_preview(None)

        # 最初の変数入力欄にフォーカスを移動
        if self.first_entry:
            self.first_entry.focus_set()
            self.first_entry.select_range(0, tk.END)

    def update_preview(self, event):
        template = self.prompt_data['template']
        variables = {var: entry.get() for var, entry in self.var_entries.items()}
        
        try:
            template_single_braces = re.sub(r'\{\{(\w+)\}\}', r'{\1}', template)
            result = template_single_braces.format(**variables)
            self.preview_text.delete("1.0", tk.END)
            self.preview_text.insert("1.0", result)
        except KeyError:
            pass

    def copy_to_clipboard(self):
        preview_text = self.preview_text.get("1.0", tk.END).strip()
        if preview_text:
            self.window.clipboard_clear()
            self.window.clipboard_append(preview_text)
            messagebox.showinfo("成功", "クリップボードにコピーしました。")

class FlashPromptApp:
    def __init__(self, root):
        self.root = root
        self.root.title("FlashPrompt")
        self.root.attributes('-topmost', True)
        
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
                                       font=FONTS['input'],
                                       bg=COLORS['surface'],
                                       fg=COLORS['text'],
                                       selectmode='single',
                                       activestyle='none',
                                       selectbackground=COLORS['primary'],
                                       selectforeground=COLORS['surface'])
        self.prompt_listbox.pack(fill='both', expand=True)
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
        template = self.template_text.get("1.0", tk.END)
        variables = set(re.findall(r'\{\{(\w+)\}\}', template))
        self.variables_listbox.delete(0, tk.END)
        for var in sorted(variables):
            self.variables_listbox.insert(tk.END, var)

    def _insert_selected_variable(self, event=None):
        selection = self.variables_listbox.curselection()
        if selection:
            variable = self.variables_listbox.get(selection[0])
            current_pos = self.template_text.index(tk.INSERT)
            self.template_text.insert(tk.INSERT, f"{{{{{variable}}}}}")
            self.template_text.mark_set(tk.INSERT, f"{current_pos}+{len(variable)+4}c")
            self.template_text.focus_set()

    def _show_variable_dialog(self):
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
