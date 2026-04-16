# Author: Mosberg
# Github: https://github.com/Mosberg

import os
from tkinter import *
from tkinter import filedialog, messagebox
from PIL import Image

class SpriteSheetCutter:
    def __init__(self, root):
        self.root = root
        self.root.title("Sprite Sheet Cutter")
        self.root.geometry("420x350")

        self.image_path = None
        self.output_folder = None

        Button(root, text="Choose Sprite Sheet", command=self.load_image).pack(pady=10)

        self.label_image = Label(root, text="No image selected")
        self.label_image.pack()

        # Mode selection
        self.mode = StringVar(value="count")
        frame_mode = Frame(root)
        frame_mode.pack(pady=10)

        Radiobutton(frame_mode, text="By number of sprites", variable=self.mode, value="count",
                    command=self.update_mode).grid(row=0, column=0, padx=10)
        Radiobutton(frame_mode, text="By pixel size", variable=self.mode, value="size",
                    command=self.update_mode).grid(row=0, column=1, padx=10)

        # Frame for sprite count
        self.frame_count = Frame(root)
        Label(self.frame_count, text="Horizontal sprites:").grid(row=0, column=0, padx=5)
        self.entry_h = Entry(self.frame_count, width=5)
        self.entry_h.grid(row=0, column=1)

        Label(self.frame_count, text="Vertical sprites:").grid(row=1, column=0, padx=5)
        self.entry_v = Entry(self.frame_count, width=5)
        self.entry_v.grid(row=1, column=1)
        self.frame_count.pack()

        # Frame for pixel size
        self.frame_size = Frame(root)
        Label(self.frame_size, text="Sprite width (px):").grid(row=0, column=0, padx=5)
        self.entry_w = Entry(self.frame_size, width=5)
        self.entry_w.grid(row=0, column=1)

        Label(self.frame_size, text="Sprite height (px):").grid(row=1, column=0, padx=5)
        self.entry_h_px = Entry(self.frame_size, width=5)
        self.entry_h_px.grid(row=1, column=1)

        # Start with count mode visible
        self.frame_size.pack_forget()

        Button(root, text="Choose Output Folder", command=self.choose_output).pack(pady=10)

        self.label_output = Label(root, text="No folder selected")
        self.label_output.pack()

        Button(root, text="Cut Sprites", command=self.cut_sprites).pack(pady=15)

    def update_mode(self):
        if self.mode.get() == "count":
            self.frame_size.pack_forget()
            self.frame_count.pack()
        else:
            self.frame_count.pack_forget()
            self.frame_size.pack()

    def load_image(self):
        path = filedialog.askopenfilename(
            filetypes=[("Image files", "*.png;*.jpg;*.jpeg;*.bmp")]
        )
        if path:
            self.image_path = path
            self.label_image.config(text=os.path.basename(path))

    def choose_output(self):
        folder = filedialog.askdirectory()
        if folder:
            self.output_folder = folder
            self.label_output.config(text=folder)

    def cut_sprites(self):
        if not self.image_path:
            messagebox.showerror("Error", "No image selected.")
            return
        if not self.output_folder:
            messagebox.showerror("Error", "No output folder selected.")
            return

        img = Image.open(self.image_path)
        sheet_width, sheet_height = img.size

        mode = self.mode.get()

        if mode == "count":
            try:
                h = int(self.entry_h.get())
                v = int(self.entry_v.get())
            except ValueError:
                messagebox.showerror("Error", "Horizontal/Vertical values must be numbers.")
                return

            sprite_width = sheet_width // h
            sprite_height = sheet_height // v

        else:
            try:
                sprite_width = int(self.entry_w.get())
                sprite_height = int(self.entry_h_px.get())
            except ValueError:
                messagebox.showerror("Error", "Width/Height must be numbers.")
                return

            h = sheet_width // sprite_width
            v = sheet_height // sprite_height

        saved = 0

        for y in range(v):
            for x in range(h):
                left = x * sprite_width
                top = y * sprite_height
                right = left + sprite_width
                bottom = top + sprite_height

                sprite = img.crop((left, top, right, bottom))

                # Ensure RGBA
                if sprite.mode != "RGBA":
                    sprite = sprite.convert("RGBA")

                # Check transparency
                alpha = sprite.split()[-1]
                if not alpha.getextrema()[1]:  # max alpha == 0 → fully transparent
                    continue

                sprite.save(os.path.join(self.output_folder, f"sprite_{saved}.png"))
                saved += 1

        messagebox.showinfo("Done", f"Saved {saved} sprites!")

# Run the app
root = Tk()
app = SpriteSheetCutter(root)
root.mainloop()
