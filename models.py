import os
import json
from constants import DEFAULT_SETTINGS

class PromptManager:
    """
    プロンプトの保存、読み込み、管理を行うクラス。

    プロンプトはJSONファイルに保存され、アプリケーションのローカルアプリケーションデータディレクトリに格納されます。
    """
    def __init__(self):
        """
        PromptManagerクラスのコンストラクタ。

        アプリケーションデータディレクトリのパスを設定し、ディレクトリとプロンプトファイルを初期化します。
        """
        self.appdata_path = os.path.join(os.getenv('LOCALAPPDATA'), 'flashprompt')
        self.prompts_file = os.path.join(self.appdata_path, 'prompts.json')
        self._ensure_directory()
        self.prompts = self._load_prompts()

    def _ensure_directory(self):
        """
        アプリケーションデータディレクトリとプロンプトファイルが存在することを保証する。

        存在しない場合は、ディレクトリと空のプロンプトファイルを作成します。
        """
        if not os.path.exists(self.appdata_path):
            os.makedirs(self.appdata_path)
        if not os.path.exists(self.prompts_file):
            with open(self.prompts_file, 'w', encoding='utf-8') as f:
                json.dump([], f)

    def _load_prompts(self):
        """
        プロンプトファイルからプロンプトを読み込む。

        ファイルが存在しない場合やJSONの読み込みに失敗した場合は、空のリストを返します。

        Returns:
            list: プロンプトのリスト。各プロンプトは辞書形式 ({'name': 'prompt_name', 'template': 'prompt_template'}) です。
        """
        try:
            with open(self.prompts_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError): # ファイルが見つからない、またはJSONデコードに失敗した場合の例外処理を追加
            return []

    def save_prompt(self, name, template):
        """
        新しいプロンプトを保存する。

        Args:
            name (str): プロンプトの名前。
            template (str): プロンプトのテンプレート。
        """
        prompt = {
            'name': name,
            'template': template
        }
        self.prompts.append(prompt)
        self._save_to_file()

    def _save_to_file(self):
        """
        プロンプトをJSONファイルに保存する。
        """
        with open(self.prompts_file, 'w', encoding='utf-8') as f:
            json.dump(self.prompts, f, ensure_ascii=False, indent=2)

    def delete_prompt(self, name):
        """
        指定された名前のプロンプトを削除する。

        Args:
            name (str): 削除するプロンプトの名前。
        """
        self.prompts = [p for p in self.prompts if p['name'] != name]
        self._save_to_file()

    def get_prompt(self, name):
        """
        指定された名前のプロンプトを取得する。

        Args:
            name (str): 取得するプロンプトの名前。

        Returns:
            dict or None: プロンプトが見つかった場合はプロンプトの辞書、見つからない場合はNone。
        """
        for prompt in self.prompts:
            if prompt['name'] == name:
                return prompt
        return None

class SettingsManager:
    """
    アプリケーション設定の保存、読み込み、管理を行うクラス。

    設定はJSONファイルに保存され、アプリケーションのローカルアプリケーションデータディレクトリに格納されます。
    """
    def __init__(self):
        """
        SettingsManagerクラスのコンストラクタ。

        アプリケーションデータディレクトリのパスを設定し、ディレクトリと設定ファイルを初期化します。
        """
        self.appdata_path = os.path.join(os.getenv('LOCALAPPDATA'), 'flashprompt')
        self.settings_file = os.path.join(self.appdata_path, 'settings.json')
        self._ensure_directory()
        self.settings = self._load_settings()

    def _ensure_directory(self):
        """
        アプリケーションデータディレクトリと設定ファイルが存在することを保証する。

        存在しない場合は、ディレクトリとデフォルト設定ファイルを作成します。
        """
        if not os.path.exists(self.appdata_path):
            os.makedirs(self.appdata_path)
        if not os.path.exists(self.settings_file):
            with open(self.settings_file, 'w', encoding='utf-8') as f:
                json.dump(DEFAULT_SETTINGS, f)

    def _load_settings(self):
        """
        設定ファイルから設定を読み込む。

        ファイルが存在しない場合やJSONの読み込みに失敗した場合は、デフォルト設定を返します。
        設定ファイルに不足しているキーがある場合は、デフォルト設定から補完します。

        Returns:
            dict: 設定の辞書。
        """
        try:
            with open(self.settings_file, 'r', encoding='utf-8') as f:
                settings = json.load(f)
                # デフォルト設定との整合性を確保
                for key, value in DEFAULT_SETTINGS.items():
                    if key not in settings:
                        settings[key] = value
                return settings
        except (FileNotFoundError, json.JSONDecodeError): # ファイルが見つからない、またはJSONデコードに失敗した場合の例外処理を追加
            return DEFAULT_SETTINGS.copy()

    def save_settings(self, settings):
        """
        設定をJSONファイルに保存する。

        Args:
            settings (dict): 保存する設定の辞書。
        """
        self.settings = settings
        with open(self.settings_file, 'w', encoding='utf-8') as f:
            json.dump(settings, f, ensure_ascii=False, indent=2)

    def get_settings(self):
        """
        現在の設定を取得する。

        Returns:
            dict: 現在の設定の辞書。
        """
        return self.settings