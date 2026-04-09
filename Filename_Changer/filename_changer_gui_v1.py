# Author: Mosberg
# Github: https://github.com/Mosberg

import os
import re
import tkinter as tk
from tkinter import filedialog, scrolledtext, messagebox

# Updated pattern: match a space before (number)
pattern = re.compile(r" \((\d+)\)")

def rename_files(root_dir, log_widget):
    count = 0
    for folder, _, files in os.walk(root_dir):
        for filename in files:
            match = pattern.search(filename)
            if match:
                number = match.group(1)

                # Replace " (2)" with "_2"
                new_filename = pattern.sub(f"_{number}", filename)

                old_path = os.path.join(folder, filename)
                new_path = os.path.join(folder, new_filename)

                try:
                    os.rename(old_path, new_path)
                    log_widget.insert(tk.END, f"Renamed: {old_path} -> {new_path}\n")
                    count += 1
                except Exception as e:
                    log_widget.insert(tk.END, f"Error renaming {old_path}: {e}\n")

    log_widget.insert(tk.END, f"\nDone! Renamed {count} files.\n")
    log_widget.see(tk.END)


def choose_folder():
    folder = filedialog.askdirectory()
    if folder:
        folder_var.set(folder)


def start_renaming():
    folder = folder_var.get()
    if not folder:
        messagebox.showwarning("No folder selected", "Please choose a folder first.")
        return

    log_box.delete(1.0, tk.END)
    rename_files(folder, log_box)


# ---------------- GUI ---------------- #

root = tk.Tk()
root.title("Rename Files (2) → _2")
root.geometry("700x500")

folder_var = tk.StringVar()

frame = tk.Frame(root)
frame.pack(pady=10)

tk.Label(frame, text="Folder:").grid(row=0, column=0, padx=5)
tk.Entry(frame, textvariable=folder_var, width=50).grid(row=0, column=1, padx=5)
tk.Button(frame, text="Browse", command=choose_folder).grid(row=0, column=2, padx=5)

tk.Button(root, text="Start Renaming", command=start_renaming, width=20).pack(pady=10)

log_box = scrolledtext.ScrolledText(root, width=80, height=20)
log_box.pack(padx=10, pady=10)

root.mainloop()
