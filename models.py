import os
import json

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
