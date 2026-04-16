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
        self.root.geometry("400x250")

        self.image_path = None
        self.output_folder = None

        # UI Elements
        Button(root, text="Choose Sprite Sheet", command=self.load_image).pack(pady=10)

        self.label_image = Label(root, text="No image selected")
        self.label_image.pack()

        frame = Frame(root)
        frame.pack(pady=10)

        Label(frame, text="Horizontal sprites:").grid(row=0, column=0, padx=5)
        self.entry_h = Entry(frame, width=5)
        self.entry_h.grid(row=0, column=1)

        Label(frame, text="Vertical sprites:").grid(row=1, column=0, padx=5)
        self.entry_v = Entry(frame, width=5)
        self.entry_v.grid(row=1, column=1)

        Button(root, text="Choose Output Folder", command=self.choose_output).pack(pady=10)

        self.label_output = Label(root, text="No folder selected")
        self.label_output.pack()

        Button(root, text="Cut Sprites", command=self.cut_sprites).pack(pady=15)

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

        try:
            h = int(self.entry_h.get())
            v = int(self.entry_v.get())
        except ValueError:
            messagebox.showerror("Error", "Horizontal/Vertical values must be numbers.")
            return

        img = Image.open(self.image_path)
        sheet_width, sheet_height = img.size

        sprite_width = sheet_width // h
        sprite_height = sheet_height // v

        count = 0
        for y in range(v):
            for x in range(h):
                left = x * sprite_width
                top = y * sprite_height
                right = left + sprite_width
                bottom = top + sprite_height

                sprite = img.crop((left, top, right, bottom))
                sprite.save(os.path.join(self.output_folder, f"sprite_{count}.png"))
                count += 1

        messagebox.showinfo("Done", f"Saved {count} sprites!")

# Run the app
root = Tk()
app = SpriteSheetCutter(root)
root.mainloop()
