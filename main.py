import tkinter as tk
from views import FlashPromptApp

def main():
    root = tk.Tk()
    app = FlashPromptApp(root)
    root.mainloop()

if __name__ == "__main__":
    main()
