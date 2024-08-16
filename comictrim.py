import tkinter as tk
from tkinter import filedialog, messagebox
from tkinterdnd2 import DND_FILES, TkinterDnD
from PIL import Image, ImageTk
import os

class ImageTrimmerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Image Trimming Tool")
        self.root.geometry("600x860")  # Set a default window size

        self.image_path = None
        self.start_y = None
        self.end_y = None
        self.scale_ratio = 1  # Ratio to scale Y positions
        self.image_format = None  # To store the image format

        # Create and place widgets
        tk.Label(root, text="Drag and drop an image file here or use the Browse button:").pack(pady=3)
        self.entry_file_path = tk.Entry(root, width=50)
        self.entry_file_path.pack(pady=5)

        # Create a frame for the buttons
        button_frame = tk.Frame(root)
        button_frame.pack(pady=3)

        tk.Button(button_frame, text="Browse", command=self.browse_file).pack(side=tk.LEFT, padx=5)
        tk.Button(button_frame, text="Trim Image", command=self.process_image).pack(side=tk.LEFT, padx=5)

        # Create a checkbox
        self.overwrite_var = tk.BooleanVar(value=True)  # Default to True
        self.overwrite_checkbox = tk.Checkbutton(root, text="Overwrite original image", variable=self.overwrite_var)
        self.overwrite_checkbox.pack(pady=5)

        # Create a canvas to display the image
        self.canvas = tk.Canvas(root, bg='white')
        self.canvas.pack(fill=tk.BOTH, expand=True)

        # Enable drag-and-drop functionality
        self.setup_drag_and_drop()
        self.setup_y_position_selection()

        # Initialize draggable indicators
        self.indicator_id_start = None
        self.indicator_id_end = None

        # Variables for dragging indicators
        self.dragging_start = False
        self.dragging_end = False

        self.top_padding = 20  # Padding from the top of the image viewer
        self.bottom_padding = 20  # Padding from the bottom of the image viewer

    def setup_drag_and_drop(self):
        # Register the window as a drop target for files
        self.root.drop_target_register(DND_FILES)
        self.root.dnd_bind('<<Drop>>', self.on_drop)

    def setup_y_position_selection(self):
        self.canvas.bind("<Button-1>", self.on_control_click)  # Use left mouse button for selecting Y positions

    def on_drop(self, event):
        file_path = event.data.strip('{}')
        if file_path and os.path.isfile(file_path):
            self.image_path = file_path
            self.entry_file_path.delete(0, tk.END)
            self.entry_file_path.insert(0, self.image_path)
            self.load_image(self.image_path)

    def browse_file(self):
        self.image_path = filedialog.askopenfilename(filetypes=[("Image Files", "*.png;*.jpg;*.jpeg;*.webp;*.gif")])
        if self.image_path:
            self.entry_file_path.delete(0, tk.END)
            self.entry_file_path.insert(0, self.image_path)
            self.load_image(self.image_path)

    def load_image(self, file_path):
        try:
            # Load the image
            img = Image.open(file_path)
            
            # Resize image to fit height
            available_height = self.root.winfo_height() - 150 - self.top_padding - self.bottom_padding
            ratio = available_height / img.height
            new_width = int(img.width * ratio)
            img = img.resize((new_width, available_height), Image.Resampling.LANCZOS)
            
            # Convert image to PhotoImage
            img_tk = ImageTk.PhotoImage(img)

            # Update image on canvas
            self.canvas.delete("all")
            self.canvas.create_image(0, self.top_padding, image=img_tk, anchor=tk.NW, tags="image")
            self.canvas.image = img_tk
            
            # Save image dimensions and scaling ratio
            self.img_width = img.width
            self.img_height = img.height
            self.original_img = Image.open(file_path)  # Keep original image for cropping
            self.scale_ratio = img.height / self.original_img.height
            self.image_format = self.original_img.format

            # Clear previous indicators and reset state
            self.canvas.delete("indicators")
            self.start_y = None
            self.end_y = None
            self.indicator_id_start = None
            self.indicator_id_end = None
            self.dragging_start = False
            self.dragging_end = False
        except Exception as e:
            print(f"An error occurred while loading the image: {e}")

    def on_drag_start(self, event):
        self.drag_start_x = event.x
        self.drag_start_y = event.y

    def on_drag_move(self, event):
        self.canvas.scan_dragto(event.x, event.y, gain=1)

    def on_control_click(self, event):
        if self.image_path:
            try:
                y = event.y - self.top_padding
                y = min(max(y, 0), self.img_height)  # Ensure y is within image boundaries
                if self.start_y is None:
                    self.start_y = y / self.scale_ratio
                    self.draw_indicators()
                elif self.end_y is None:
                    self.end_y = y / self.scale_ratio
                    if self.start_y > self.end_y:
                        self.start_y, self.end_y = self.end_y, self.start_y
                    self.draw_indicators()
            except Exception as e:
                print(f"An error occurred while processing mouse click: {e}")

    def draw_indicators(self):
        # Clear previous indicators
        self.canvas.delete("indicators")

        if self.start_y is not None:
            start_y_display = int(self.start_y * self.scale_ratio) + self.top_padding
            self.indicator_id_start = self.canvas.create_line(0, start_y_display, self.img_width, start_y_display, fill="red", dash=(4, 4), tags="indicators")
            self.canvas.tag_bind(self.indicator_id_start, "<Button-1>", self.start_drag_start)

        if self.end_y is not None:
            end_y_display = int(self.end_y * self.scale_ratio) + self.top_padding
            self.indicator_id_end = self.canvas.create_line(0, end_y_display, self.img_width, end_y_display, fill="blue", dash=(4, 4), tags="indicators")
            self.canvas.tag_bind(self.indicator_id_end, "<Button-1>", self.start_drag_end)

    def start_drag_start(self, event):
        self.dragging_start = True
        self.canvas.bind("<B1-Motion>", self.dragging_start_move)

    def start_drag_end(self, event):
        self.dragging_end = True
        self.canvas.bind("<B1-Motion>", self.dragging_end_move)

    def dragging_start_move(self, event):
        if self.dragging_start:
            y = event.y - self.top_padding
            y = min(max(y, 0), self.img_height)  # Ensure y is within image boundaries
            self.start_y = y / self.scale_ratio
            if self.start_y > (self.end_y if self.end_y else self.img_height):
                self.start_y = self.end_y - 1  # Ensure start is not below end
            self.draw_indicators()

    def dragging_end_move(self, event):
        if self.dragging_end:
            y = event.y - self.top_padding
            y = min(max(y, 0), self.img_height)  # Ensure y is within image boundaries
            self.end_y = y / self.scale_ratio
            if self.end_y < (self.start_y if self.start_y else 0):
                self.end_y = self.start_y + 1  # Ensure end is not above start
            self.draw_indicators()

    def crop_and_merge_image(self, output_path):
        try:
            # Load original image
            with self.original_img as img:
                # Get image dimensions
                width, height = img.size

                # Define cropping areas
                top_img = img.crop((0, 0, width, int(self.start_y)))
                bottom_img = img.crop((0, int(self.end_y), width, height))

                # Merge the top and bottom images
                merged_img = Image.new('RGB', (width, top_img.height + bottom_img.height))
                merged_img.paste(top_img, (0, 0))
                merged_img.paste(bottom_img, (0, top_img.height))

                # Save the merged image
                merged_img.save(output_path, format=self.image_format)
                
                return output_path
        except Exception as e:
            print(f"An error occurred while cropping and merging the image: {e}")
            return None
    
    def process_image(self):
        if self.start_y is not None and self.end_y is not None:
            # Determine the output path based on the checkbox state
            if self.overwrite_var.get():
                output_path = self.image_path
            else:
                base, ext = os.path.splitext(self.image_path)
                output_path = f"{base}_trimmed{ext}"

            # Crop and merge the image
            merged_path = self.crop_and_merge_image(output_path)
            if merged_path:
                print(f"Trimmed image saved: {merged_path}")
                self.load_image(merged_path)
        else:
            messagebox.showerror("Error", "Please select both start and end Y positions.")

# Create the main window
root = TkinterDnD.Tk()
app = ImageTrimmerApp(root)
root.mainloop()
