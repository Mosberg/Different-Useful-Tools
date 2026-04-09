# Author: Mosberg
# Github: https://github.com/Mosberg

import os
import re
import csv
import shutil
import tkinter as tk
from tkinter import filedialog, messagebox, ttk

# Try optional tkdnd for drag-and-drop (if installed)
try:
    import tkdnd  # noqa: F401
    TKDND_AVAILABLE = True
except Exception:
    TKDND_AVAILABLE = False


# ------------------------------
# Tooltip helper
# ------------------------------
class ToolTip:
    def __init__(self, widget, text):
        self.widget = widget
        self.text = text
        self.tipwindow = None
        widget.bind("<Enter>", self.show_tip)
        widget.bind("<Motion>", self.show_tip)
        widget.bind("<Leave>", self.hide_tip)


    def show_tip(self, event=None):
        if self.tipwindow or not self.text:
            return

        x = event.x_root + 15
        y = event.y_root + 15

        self.tipwindow = tw = tk.Toplevel(self.widget)
        tw.wm_overrideredirect(True)
        tw.wm_geometry(f"+{x}+{y}")

        label = tk.Label(
            tw,
            text=self.text,
            justify=tk.LEFT,
            background="#333333",
            foreground="#ffffff",
            relief=tk.SOLID,
            borderwidth=1,
            font=("Segoe UI", 9),
        )
        label.pack(ipadx=4, ipady=2)


    def hide_tip(self, _event=None):
        if self.tipwindow:
            self.tipwindow.destroy()
            self.tipwindow = None


# ------------------------------
# Undo Manager
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
# Rule model
# ------------------------------
class Rule:
    def __init__(self, find_pattern, replace_text, regex_mode, rename_folders):
        self.find_pattern = find_pattern
        self.replace_text = replace_text
        self.regex_mode = regex_mode
        self.rename_folders = rename_folders

    def apply(self, text):
        if self.regex_mode:
            return re.sub(self.find_pattern, self.replace_text, text)
        else:
            return text.replace(self.find_pattern, self.replace_text)

    def __str__(self):
        mode = "Regex" if self.regex_mode else "Text"
        folder = " +Folders" if self.rename_folders else ""
        return f"[{mode}{folder}] '{self.find_pattern}' → '{self.replace_text}'"


# ------------------------------
# Renamer Engine
# ------------------------------
class Renamer:
    def __init__(self, root_dir, rules, extensions_filter):
        self.root_dir = root_dir
        self.rules = rules
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
            # Folders
            for i, sub in enumerate(list(subfolders)):
                old_folder_name = sub
                new_folder_name = old_folder_name
                for rule in self.rules:
                    if rule.rename_folders:
                        new_folder_name = rule.apply(new_folder_name)
                if new_folder_name != old_folder_name:
                    old = os.path.join(folder, old_folder_name)
                    new = os.path.join(folder, new_folder_name)
                    preview_list.append((old, new))
                    subfolders[i] = new_folder_name  # keep walk consistent

            # Files
            for f in files:
                if not self._match_extension(f):
                    continue
                old_file_name = f
                new_file_name = old_file_name
                for rule in self.rules:
                    new_file_name = rule.apply(new_file_name)
                if new_file_name != old_file_name:
                    old = os.path.join(folder, old_file_name)
                    new = os.path.join(folder, new_file_name)
                    preview_list.append((old, new))

        return preview_list

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
        root.geometry("1000x650")

        self._enable_dark_mode()

        self.folder_var = tk.StringVar()
        self.find_var = tk.StringVar()
        self.replace_var = tk.StringVar()
        self.regex_var = tk.BooleanVar()
        self.folder_rename_var = tk.BooleanVar()
        self.extensions_var = tk.StringVar()

        self.rules = []
        self.preview_data = []
        self.undo_manager = None

        self._build_ui()
        self._bind_live_preview()

        if TKDND_AVAILABLE:
            self._enable_drag_and_drop()

    # ---------- Dark mode ----------
    def _enable_dark_mode(self):
        style = ttk.Style()
        try:
            style.theme_use("clam")
        except Exception:
            pass
        bg = "#1e1e1e"
        fg = "#ffffff"
        self.root.configure(bg=bg)
        style.configure(".", background=bg, foreground=fg, fieldbackground="#2d2d2d")
        style.configure("Treeview", background="#252526", foreground=fg, fieldbackground="#252526")
        style.configure("TButton", padding=4)
        style.map("TButton", background=[("active", "#3e3e3e")])

    # ---------- UI ----------
    def _build_ui(self):
        frame = tk.Frame(self.root, bg="#1e1e1e")
        frame.pack(pady=10, fill="x")

        # Folder selection
        lbl_folder = tk.Label(frame, text="Folder:", bg="#1e1e1e", fg="#ffffff")
        lbl_folder.grid(row=0, column=0, padx=5, sticky="e")
        entry_folder = tk.Entry(frame, textvariable=self.folder_var, width=60, bg="#2d2d2d", fg="#ffffff", insertbackground="#ffffff")
        entry_folder.grid(row=0, column=1, padx=5)
        btn_browse = ttk.Button(frame, text="Browse", command=self.choose_folder)
        btn_browse.grid(row=0, column=2, padx=5)

        ToolTip(lbl_folder, "Root folder to scan recursively.")
        ToolTip(entry_folder, "You can also paste a path here.")
        ToolTip(btn_browse, "Open a folder selection dialog.")

        # Find / Replace
        lbl_find = tk.Label(frame, text="Find:", bg="#1e1e1e", fg="#ffffff")
        lbl_find.grid(row=1, column=0, padx=5, pady=5, sticky="e")
        entry_find = tk.Entry(frame, textvariable=self.find_var, width=60, bg="#2d2d2d", fg="#ffffff", insertbackground="#ffffff")
        entry_find.grid(row=1, column=1, padx=5)

        lbl_replace = tk.Label(frame, text="Replace with:", bg="#1e1e1e", fg="#ffffff")
        lbl_replace.grid(row=2, column=0, padx=5, pady=5, sticky="e")
        entry_replace = tk.Entry(frame, textvariable=self.replace_var, width=60, bg="#2d2d2d", fg="#ffffff", insertbackground="#ffffff")
        entry_replace.grid(row=2, column=1, padx=5)

        ToolTip(lbl_find, "Text or regex pattern to search for.")
        ToolTip(entry_find, "Supports plain text or regex (if enabled).")
        ToolTip(lbl_replace, "Replacement text.")
        ToolTip(entry_replace, "What the matched text will be replaced with.")

        # Options for current rule
        chk_regex = tk.Checkbutton(frame, text="Regex mode", variable=self.regex_var, bg="#1e1e1e", fg="#ffffff", selectcolor="#1e1e1e")
        chk_regex.grid(row=3, column=1, sticky="w")
        chk_folder = tk.Checkbutton(frame, text="Apply to folders", variable=self.folder_rename_var, bg="#1e1e1e", fg="#ffffff", selectcolor="#1e1e1e")
        chk_folder.grid(row=4, column=1, sticky="w")

        ToolTip(chk_regex, "If checked, 'Find' is treated as a Python regular expression.")
        ToolTip(chk_folder, "If checked, this rule also renames folders.")

        # Extensions filter
        lbl_ext = tk.Label(frame, text="Extensions filter (.jpg,.mp4):", bg="#1e1e1e", fg="#ffffff")
        lbl_ext.grid(row=5, column=0, padx=5, sticky="e")
        entry_ext = tk.Entry(frame, textvariable=self.extensions_var, width=60, bg="#2d2d2d", fg="#ffffff", insertbackground="#ffffff")
        entry_ext.grid(row=5, column=1, padx=5)

        ToolTip(lbl_ext, "Comma-separated list of extensions. Leave empty for all files.")
        ToolTip(entry_ext, "Example: .jpg,.png,.mp4")

        # Rule buttons
        btn_frame = tk.Frame(self.root, bg="#1e1e1e")
        btn_frame.pack(pady=5)

        btn_add_rule = ttk.Button(btn_frame, text="Add Rule", command=self.add_rule)
        btn_remove_rule = ttk.Button(btn_frame, text="Remove Selected Rule", command=self.remove_rule)
        btn_clear_rules = ttk.Button(btn_frame, text="Clear Rules", command=self.clear_rules)
        btn_preset_spaces = ttk.Button(btn_frame, text="Preset: Remove Spaces", command=self.preset_remove_spaces)
        btn_preset_lower = ttk.Button(btn_frame, text="Preset: Normalize Case (lower)", command=self.preset_lowercase)

        btn_add_rule.grid(row=0, column=0, padx=5)
        btn_remove_rule.grid(row=0, column=1, padx=5)
        btn_clear_rules.grid(row=0, column=2, padx=5)
        btn_preset_spaces.grid(row=0, column=3, padx=5)
        btn_preset_lower.grid(row=0, column=4, padx=5)

        ToolTip(btn_add_rule, "Add the current Find/Replace as a rule in the pipeline.")
        ToolTip(btn_remove_rule, "Remove the selected rule from the pipeline.")
        ToolTip(btn_clear_rules, "Remove all rules.")
        ToolTip(btn_preset_spaces, "Add rules to remove spaces from filenames.")
        ToolTip(btn_preset_lower, "Add a rule to convert filenames to lowercase.")

        # Rules list
        rules_frame = tk.LabelFrame(self.root, text="Rules Pipeline (applied top to bottom)", bg="#1e1e1e", fg="#ffffff")
        rules_frame.pack(fill="x", padx=10, pady=5)
        self.rules_listbox = tk.Listbox(rules_frame, height=5, bg="#252526", fg="#ffffff", selectbackground="#3e3e3e")
        self.rules_listbox.pack(fill="x", padx=5, pady=5)

        ToolTip(self.rules_listbox, "Rules are applied in order. You can stack multiple transformations.")

        # Action buttons
        action_frame = tk.Frame(self.root, bg="#1e1e1e")
        action_frame.pack(pady=5)

        btn_preview = ttk.Button(action_frame, text="Preview", command=self.preview)
        btn_execute = ttk.Button(action_frame, text="Execute Rename", command=self.execute)
        btn_undo = ttk.Button(action_frame, text="Undo", command=self.undo)
        btn_export = ttk.Button(action_frame, text="Export Preview to CSV", command=self.export_csv)

        btn_preview.grid(row=0, column=0, padx=5)
        btn_execute.grid(row=0, column=1, padx=5)
        btn_undo.grid(row=0, column=2, padx=5)
        btn_export.grid(row=0, column=3, padx=5)

        ToolTip(btn_preview, "Generate a preview of all renames without changing anything.")
        ToolTip(btn_execute, "Apply all renames shown in the preview.")
        ToolTip(btn_undo, "Undo the last rename operation.")
        ToolTip(btn_export, "Export the current preview list to a CSV file.")

        # Preview list
        self.tree = ttk.Treeview(self.root, columns=("old", "new"), show="headings", height=15)
        self.tree.heading("old", text="Old Path")
        self.tree.heading("new", text="New Path")
        self.tree.column("old", width=480)
        self.tree.column("new", width=480)
        self.tree.pack(fill="both", expand=True, padx=10, pady=10)

        ToolTip(self.tree, "Shows the planned renames: from old path to new path.")

        # Progress bar
        self.progress = ttk.Progressbar(self.root, length=400)
        self.progress.pack(pady=10)
        ToolTip(self.progress, "Shows progress while renaming.")

    # ---------- Drag & Drop ----------
    def _enable_drag_and_drop(self):
        # Basic folder drop support if tkdnd is available
        try:
            self.root.drop_target_register("DND_Files")
            self.root.dnd_bind("<<Drop>>", self._on_drop)
        except Exception:
            pass

    def _on_drop(self, event):
        data = event.data
        # Data may come like '{C:/path/to/folder}'
        path = data.strip("{}")
        if os.path.isdir(path):
            self.folder_var.set(path)

    # ---------- Live preview ----------
    def _bind_live_preview(self):
        for var in (self.find_var, self.replace_var, self.extensions_var):
            var.trace_add("write", lambda *args: self._debounced_preview())
        self.regex_var.trace_add("write", lambda *args: self._debounced_preview())
        self.folder_rename_var.trace_add("write", lambda *args: self._debounced_preview())

        self._preview_after_id = None

    def _debounced_preview(self):
        if self._preview_after_id:
            self.root.after_cancel(self._preview_after_id)
        self._preview_after_id = self.root.after(600, self.preview)

    # ---------- Rule management ----------
    def add_rule(self):
        find = self.find_var.get()
        if not find:
            messagebox.showwarning("Missing Find", "Enter a Find pattern first.")
            return
        replace = self.replace_var.get()
        rule = Rule(find, replace, self.regex_var.get(), self.folder_rename_var.get())
        self.rules.append(rule)
        self.rules_listbox.insert(tk.END, str(rule))
        self.preview()

    def remove_rule(self):
        sel = self.rules_listbox.curselection()
        if not sel:
            return
        index = sel[0]
        self.rules_listbox.delete(index)
        del self.rules[index]
        self.preview()

    def clear_rules(self):
        self.rules.clear()
        self.rules_listbox.delete(0, tk.END)
        self.preview()

    # ---------- Presets ----------
    def preset_remove_spaces(self):
        # Simple preset: replace spaces with underscores (files only)
        rule = Rule(" ", "_", False, False)
        self.rules.append(rule)
        self.rules_listbox.insert(tk.END, str(rule))
        self.preview()

    def preset_lowercase(self):
        # Lowercase is not a simple find/replace; we approximate via regex:
        # Use a regex that matches the whole name and lower it via a function is not supported in this simple engine.
        # Instead, we add a note: this preset is conceptual; for real lowercase, you'd extend the engine.
        messagebox.showinfo(
            "Preset info",
            "Normalize case (lower) is non-trivial with simple regex replace.\n"
            "This preset is a placeholder—extend the engine with a custom transform if you want full control."
        )

    # ---------- Core actions ----------
    def choose_folder(self):
        folder = filedialog.askdirectory()
        if folder:
            self.folder_var.set(folder)
            self.preview()

    def _build_renamer(self):
        folder = self.folder_var.get()
        if not folder:
            messagebox.showwarning("Missing folder", "Choose a folder first.")
            return None

        extensions = [e.strip().lower() for e in self.extensions_var.get().split(",") if e.strip()]
        if not self.rules:
            # If no rules, create one from current fields for convenience
            if self.find_var.get():
                self.add_rule()
            else:
                messagebox.showwarning("No rules", "Add at least one rule.")
                return None

        return Renamer(folder, self.rules, extensions)

    def preview(self):
        renamer = self._build_renamer()
        if not renamer:
            return

        self.preview_data = renamer.preview()

        # Update preview table
        for row in self.tree.get_children():
            self.tree.delete(row)

        for old, new in self.preview_data:
            self.tree.insert("", "end", values=(old, new))

    def execute(self):
        if not self.preview_data:
            messagebox.showwarning("No preview", "Nothing to rename. Adjust rules or folder.")
            return

        renamer = self._build_renamer()
        if not renamer:
            return

        def update_progress(done, total):
            self.progress["value"] = (done / total) * 100
            self.root.update_idletasks()

        renamer.execute(self.preview_data, update_progress)
        self.undo_manager = renamer.undo
        messagebox.showinfo("Done", "Renaming completed.")

    def undo(self):
        if self.undo_manager:
            self.undo_manager.undo_all()
            messagebox.showinfo("Undo", "All changes restored.")
        else:
            messagebox.showwarning("Nothing to undo", "No rename operations recorded.")

    def export_csv(self):
        if not self.preview_data:
            messagebox.showwarning("No data", "No preview data to export.")
            return
        path = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")]
        )
        if not path:
            return
        try:
            with open(path, "w", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)
                writer.writerow(["Old Path", "New Path"])
                for old, new in self.preview_data:
                    writer.writerow([old, new])
            messagebox.showinfo("Exported", f"Preview exported to {path}")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to export CSV: {e}")


# ------------------------------
# Run App (use pythonw.exe to hide console on Windows)
# ------------------------------
if __name__ == "__main__":
    root = tk.Tk()
    App(root)
    root.mainloop()
