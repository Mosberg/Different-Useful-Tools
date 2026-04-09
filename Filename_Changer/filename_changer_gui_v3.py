# Author: Mosberg
# Github: https://github.com/Mosberg

import os
import re
import shutil
import tkinter as tk
from tkinter import filedialog, messagebox, ttk

# ------------------------------
# Utility: Undo Manager
# ------------------------------
class UndoManager:
    def __init__(self):
        self.actions = []

    def add(self, old_path, new_path):
        self.actions.append((old_path, new_path))

    def undo_all(self):
        for old_path, new_path in reversed(self.actions):
            if os.path.exists(new_path):
                shutil.move(new_path, old_path)
        self.actions.clear()


# ------------------------------
# Renamer Engine
# ------------------------------
class Renamer:
    def __init__(self, root_dir, find_pattern, replace_text, regex_mode,
                 rename_folders, extensions_filter):
        self.root_dir = root_dir
        self.find_pattern = find_pattern
        self.replace_text = replace_text
        self.regex_mode = regex_mode
        self.rename_folders = rename_folders
        self.extensions_filter = extensions_filter
        self.undo = UndoManager()

    def _match_extension(self, filename):
        if not self.extensions_filter:
            return True
        ext = os.path.splitext(filename)[1].lower()
        return ext in self.extensions_filter

    def preview(self):
        preview_list = []

        for folder, subfolders, files in os.walk(self.root_dir):

            # Rename folders?
            if self.rename_folders:
                for sub in subfolders:
                    old = os.path.join(folder, sub)
                    new_name = self._apply(sub)
                    if new_name != sub:
                        preview_list.append((old, os.path.join(folder, new_name)))

            # Rename files
            for f in files:
                if not self._match_extension(f):
                    continue
                old = os.path.join(folder, f)
                new_name = self._apply(f)
                if new_name != f:
                    preview_list.append((old, os.path.join(folder, new_name)))

        return preview_list

    def _apply(self, text):
        if self.regex_mode:
            return re.sub(self.find_pattern, self.replace_text, text)
        else:
            return text.replace(self.find_pattern, self.replace_text)

    def execute(self, preview_list, progress_callback=None):
        total = len(preview_list)
        for i, (old, new) in enumerate(preview_list):
            try:
                os.rename(old, new)
                self.undo.add(old, new)
            except Exception as e:
                print("Rename error:", e)

            if progress_callback:
                progress_callback(i + 1, total)


# ------------------------------
# GUI
# ------------------------------
class App:
    def __init__(self, root):
        self.root = root
        root.title("Advanced Batch Renamer")
        root.geometry("900x600")

        self.folder_var = tk.StringVar()
        self.find_var = tk.StringVar()
        self.replace_var = tk.StringVar()
        self.regex_var = tk.BooleanVar()
        self.folder_rename_var = tk.BooleanVar()
        self.extensions_var = tk.StringVar()

        self.preview_data = []

        self._build_ui()

    def _build_ui(self):
        frame = tk.Frame(self.root)
        frame.pack(pady=10)

        # Folder selection
        tk.Label(frame, text="Folder:").grid(row=0, column=0, padx=5)
        tk.Entry(frame, textvariable=self.folder_var, width=50).grid(row=0, column=1, padx=5)
        tk.Button(frame, text="Browse", command=self.choose_folder).grid(row=0, column=2, padx=5)

        # Find / Replace
        tk.Label(frame, text="Find:").grid(row=1, column=0, padx=5, pady=5)
        tk.Entry(frame, textvariable=self.find_var, width=50).grid(row=1, column=1, padx=5)

        tk.Label(frame, text="Replace with:").grid(row=2, column=0, padx=5, pady=5)
        tk.Entry(frame, textvariable=self.replace_var, width=50).grid(row=2, column=1, padx=5)

        # Options
        tk.Checkbutton(frame, text="Regex mode", variable=self.regex_var).grid(row=3, column=1, sticky="w")
        tk.Checkbutton(frame, text="Rename folders", variable=self.folder_rename_var).grid(row=4, column=1, sticky="w")

        tk.Label(frame, text="Extensions filter (e.g. .jpg,.png,.mp4):").grid(row=5, column=0, padx=5)
        tk.Entry(frame, textvariable=self.extensions_var, width=50).grid(row=5, column=1, padx=5)

        # Buttons
        tk.Button(self.root, text="Preview", command=self.preview, width=20).pack(pady=5)
        tk.Button(self.root, text="Execute Rename", command=self.execute, width=20).pack(pady=5)
        tk.Button(self.root, text="Undo", command=self.undo, width=20).pack(pady=5)

        # Preview list
        self.tree = ttk.Treeview(self.root, columns=("old", "new"), show="headings", height=15)
        self.tree.heading("old", text="Old Path")
        self.tree.heading("new", text="New Path")
        self.tree.pack(fill="both", expand=True, padx=10, pady=10)

        # Progress bar
        self.progress = ttk.Progressbar(self.root, length=400)
        self.progress.pack(pady=10)

    def choose_folder(self):
        folder = filedialog.askdirectory()
        if folder:
            self.folder_var.set(folder)

    def preview(self):
        folder = self.folder_var.get()
        if not folder:
            messagebox.showwarning("Missing folder", "Choose a folder first.")
            return

        extensions = [e.strip().lower() for e in self.extensions_var.get().split(",") if e.strip()]

        renamer = Renamer(
            folder,
            self.find_var.get(),
            self.replace_var.get(),
            self.regex_var.get(),
            self.folder_rename_var.get(),
            extensions
        )

        self.preview_data = renamer.preview()

        # Update preview table
        for row in self.tree.get_children():
            self.tree.delete(row)

        for old, new in self.preview_data:
            self.tree.insert("", "end", values=(old, new))

        messagebox.showinfo("Preview Ready", f"Found {len(self.preview_data)} items to rename.")

    def execute(self):
        if not self.preview_data:
            messagebox.showwarning("No preview", "Run preview first.")
            return

        folder = self.folder_var.get()
        extensions = [e.strip().lower() for e in self.extensions_var.get().split(",") if e.strip()]

        renamer = Renamer(
            folder,
            self.find_var.get(),
            self.replace_var.get(),
            self.regex_var.get(),
            self.folder_rename_var.get(),
            extensions
        )

        def update_progress(done, total):
            self.progress["value"] = (done / total) * 100
            self.root.update_idletasks()

        renamer.execute(self.preview_data, update_progress)
        self.undo_manager = renamer.undo

        messagebox.showinfo("Done", "Renaming completed.")

    def undo(self):
        if hasattr(self, "undo_manager"):
            self.undo_manager.undo_all()
            messagebox.showinfo("Undo", "All changes restored.")
        else:
            messagebox.showwarning("Nothing to undo", "No rename operations recorded.")


# ------------------------------
# Run App (no console window if using pythonw.exe)
# ------------------------------
if __name__ == "__main__":
    root = tk.Tk()
    App(root)
    root.mainloop()
