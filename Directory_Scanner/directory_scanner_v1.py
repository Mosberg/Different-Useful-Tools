# Author: Mosberg
# Github: https://github.com/Mosberg

import os
import json
import csv
import tkinter as tk
from tkinter import filedialog

def choose_folder():
    root = tk.Tk()
    root.withdraw()
    folder = filedialog.askdirectory(title="Select a folder to scan")
    return folder

def scan_directory(path):
    structure = []

    for root, dirs, files in os.walk(path):
        rel_root = os.path.relpath(root, path)
        rel_root = "." if rel_root == "." else rel_root.replace("\\", "/")

        structure.append({
            "type": "folder",
            "path": rel_root
        })

        for f in files:
            structure.append({
                "type": "file",
                "path": f"{rel_root}/{f}" if rel_root != "." else f
            })

    return structure

# ---------- EXPORTERS ----------

def export_markdown(structure, output_path):
    with open(output_path, "w", encoding="utf-8") as md:
        md.write("# Folder Structure\n\n")
        for item in structure:
            if item["type"] == "folder":
                md.write(f"## 📁 {item['path']}\n")
            else:
                md.write(f"- {item['path']}\n")

def export_csv(structure, output_path):
    with open(output_path, "w", newline="", encoding="utf-8") as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(["type", "path"])
        for item in structure:
            writer.writerow([item["type"], item["path"]])

def export_json(structure, output_path):
    with open(output_path, "w", encoding="utf-8") as jf:
        json.dump(structure, jf, indent=4)

# ---------- MAIN ----------

def main():
    folder = choose_folder()
    if not folder:
        print("No folder selected.")
        return

    structure = scan_directory(folder)

    print("\nChoose export format:")
    print("1 = Markdown (.md)")
    print("2 = CSV (.csv)")
    print("3 = JSON (.json)")
    choice = input("Enter number: ").strip()

    if choice == "1":
        export_markdown(structure, "folder_structure.md")
        print("Saved as folder_structure.md")
    elif choice == "2":
        export_csv(structure, "folder_structure.csv")
        print("Saved as folder_structure.csv")
    elif choice == "3":
        export_json(structure, "folder_structure.json")
        print("Saved as folder_structure.json")
    else:
        print("Invalid choice.")

if __name__ == "__main__":
    main()
