# Author: Mosberg
# Github: https://github.com/Mosberg

import os
import tkinter as tk
from tkinter import filedialog, scrolledtext, messagebox

def rename_files(root_dir, find_text, replace_text, log_widget):
    count = 0

    for folder, _, files in os.walk(root_dir):
        for filename in files:
            if find_text in filename:
                new_filename = filename.replace(find_text, replace_text)

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
    find_text = find_var.get()
    replace_text = replace_var.get()

    if not folder:
        messagebox.showwarning("No folder selected", "Please choose a folder first.")
        return

    if not find_text:
        messagebox.showwarning("Missing find text", "Please enter what to search for.")
        return

    log_box.delete(1.0, tk.END)
    rename_files(folder, find_text, replace_text, log_box)


# ---------------- GUI ---------------- #

root = tk.Tk()
root.title("Custom File Renamer")
root.geometry("750x550")

folder_var = tk.StringVar()
find_var = tk.StringVar()
replace_var = tk.StringVar()

frame = tk.Frame(root)
frame.pack(pady=10)

# Folder selection
tk.Label(frame, text="Folder:").grid(row=0, column=0, padx=5)
tk.Entry(frame, textvariable=folder_var, width=50).grid(row=0, column=1, padx=5)
tk.Button(frame, text="Browse", command=choose_folder).grid(row=0, column=2, padx=5)

# Find text
tk.Label(frame, text="Find:").grid(row=1, column=0, padx=5, pady=5)
tk.Entry(frame, textvariable=find_var, width=50).grid(row=1, column=1, padx=5)

# Replace text
tk.Label(frame, text="Replace with:").grid(row=2, column=0, padx=5, pady=5)
tk.Entry(frame, textvariable=replace_var, width=50).grid(row=2, column=1, padx=5)

tk.Button(root, text="Start Renaming", command=start_renaming, width=20).pack(pady=10)

log_box = scrolledtext.ScrolledText(root, width=90, height=20)
log_box.pack(padx=10, pady=10)

root.mainloop()
