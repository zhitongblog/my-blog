import tkinter as tk from tkinter import ttk, filedialog, messagebox import os import shutil import datetime import re

class HugoTool: def init(self, root): self.root = root self.root.title("Hugo文章生成器") self.root.geometry("600x700")

if name == "main": root = tk.Tk() app = HugoTool(root) root.mainloop()