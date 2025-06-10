import os
import sys
import tkinter as tk
from tkinter import ttk, messagebox, filedialog

from PIL import Image, ImageTk

from config import ProgramConfig, DataConfig
from data_manager import DataManager

def resource_path(relative_path):
    """
    Get the absolute path to the resource, works for both development and PyInstaller.
    If the application is frozen (e.g., using PyInstaller), it will return the path to the executable.
    If not frozen, it will return the path relative to the script location.
    :param relative_path: The relative path to the resource.
    :return: Absolute path to the resource.
    """
    import sys
    import os
    if getattr(sys, 'frozen', False):
        # Application is frozen (e.g., PyInstaller)
        exec_path = sys.executable
        if sys.platform == "darwin":
            # macOS: .app/Contents/MacOS/yourprog
            base_path = os.path.abspath(os.path.join(os.path.dirname(exec_path), "../../../"))
        else:
            # Windows/Linux: yourprog.exe or yourprog
            base_path = os.path.dirname(exec_path)
    else:
        # Application is not frozen (e.g., running from source)
        base_path = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base_path, relative_path)

class AnnotationUI(tk.Tk):
    """
    Main application class for image annotation.
    This class initializes the main window, loads configurations, sets up the UI,
    and handles user interactions for annotating images.
    """
    def __init__(self):
        super().__init__()
        self.geometry("800x800")
        # Check if the resource files in the same directory exist
        program_config_path = resource_path("program_config.json")
        data_config_path = resource_path("data_config.json")

        if not os.path.exists(program_config_path):
            program_config_path = filedialog.askopenfilename(
                title="Choose ProgramConfig file (optional)",
                filetypes=[("JSON files", "*.json")],
            )
            if not program_config_path:
                program_config_path = None  # Allow skipping ProgramConfig
        if not os.path.exists(data_config_path):
            while True:
                data_config_path = filedialog.askopenfilename(
                    title="Choose DataConfig file",
                    filetypes=[("JSON files", "*.json")],
                )
                if data_config_path:
                    break
                if not data_config_path:
                    if messagebox.askyesno("Warning", "DataConfig file is required. Do you want to quit?"):
                        self.destroy()
                        sys.exit(0)
                    else:
                        messagebox.showwarning("Warning", "Please select a valid DataConfig file.")

        # Load configurations
        self.program_config = ProgramConfig(program_config_path) if program_config_path else ProgramConfig()
        self.data_config = DataConfig(data_config_path)

        self.data_folder = self.data_config.get("folder_path", "")
        # If no folder path is set, prompt the user to select one
        while not self.data_folder or not os.path.isdir(self.data_folder):
            self.data_folder = filedialog.askdirectory(
                title="Please select the image data folder",
            )
            if not self.data_folder:
                if messagebox.askyesno("Warning", "No data folder selected. Do you want to quit?"):
                    self.destroy()
                    sys.exit(0)
                else:
                    messagebox.showwarning("Warning", "Please select a valid image data folder.")
        self.title(os.path.basename(self.data_folder))
        self.data_manager = DataManager(self.data_folder)
        
        self._setup_ui()
        self._bind_events()
        self.load_image()

    def _setup_ui(self):
        # Title
        self.label_frame = ttk.Frame(self)
        self.label_frame.pack(fill=tk.X, padx=5, pady=5)

        # Label buttons
        self.label_buttons = []
        self.selected_labels = set()
        self.label_key_map = {}  # 用于存储标签和快捷键的映射
        label_groups = self.data_config.get("label_groups", [])
        color_list = ["#e57373", "#64b5f6", "#81c784", "#ffd54f", "#ba68c8", "#4db6ac", "#f06292", "#a1887f"]

        for group in label_groups:
            row_frame = ttk.Frame(self.label_frame)
            row_frame.pack(anchor="w", pady=2)
            for col_idx, (label, key) in enumerate(group.items()):
                color = color_list[col_idx % len(color_list)]
                btn = tk.Label(
                    row_frame,
                    text=f'{label}: {key}',
                    bg=color,
                    fg="white",
                    padx=8,
                    pady=2,
                    cursor="hand2",
                    relief="raised",
                    borderwidth=2,  # Fix border width
                    height=2        # Fix height for better visibility
                )
                btn.pack(side=tk.LEFT, padx=4)
                btn.bind("<Button-1>", lambda e, l=label, k=key: self.toggle_label(l, k))
                self.label_buttons.append((btn, label, key, color))
                if len(str(key).strip()) == 1:
                    self.label_key_map[str(key).lower()] = (label, key)

        # Image display area
        self.image_frame = ttk.Frame(self)
        self.image_frame.pack(expand=True, fill=tk.BOTH)
        self.canvas = tk.Canvas(self.image_frame, bg='white')
        self.canvas.pack(expand=True, fill=tk.BOTH)

        # Info area
        self.info_frame = ttk.Frame(self)
        self.info_frame.pack(fill=tk.X, padx=5, pady=5)
        
        self.filename_label = ttk.Label(self.info_frame, text="")
        self.filename_label.pack(side=tk.LEFT)
        
        self.progress_label = ttk.Label(self.info_frame, text="")
        self.progress_label.pack(side=tk.RIGHT)

        # Input area
        self.desc_frame = ttk.Frame(self)
        self.desc_frame.pack(fill=tk.X, padx=5, pady=5)

        # - Input box
        self.desc_entry_row = ttk.Frame(self.desc_frame)
        self.desc_entry_row.pack(fill=tk.X)
        self.desc_entry = tk.Entry(self.desc_entry_row, width=60)
        self.desc_entry.pack(side=tk.LEFT, padx=(0, 10), fill=tk.X, expand=True)
        self.desc_entry.bind("<KeyRelease>", lambda e: self.save_current_annotation())

        # - Description options
        desc_options = self.data_config.get("common_phrases", [])
        seperator = self.data_config.get("seperator", "")
        for row in desc_options:
            row_frame = ttk.Frame(self.desc_frame)
            row_frame.pack(fill=tk.X, pady=(2, 0))
            for opt in row:
                btn = ttk.Button(
                    row_frame,
                    text=opt,
                    command=lambda o=opt: self.append_desc_option(o, seperator)
                )
                btn.pack(side=tk.LEFT, padx=2)

        # Log area
        self.log_frame = ttk.Frame(self)
        self.log_frame.pack(fill=tk.X, padx=5, pady=5)

        self.log_text = tk.Text(self.log_frame, wrap=tk.WORD, state=tk.DISABLED, height=3)  # Set a fixed height for the log area
        scrollbar = ttk.Scrollbar(self.log_frame, command=self.log_text.yview)
        self.log_text.configure(yscrollcommand=scrollbar.set)

        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.log_text.pack(side=tk.LEFT, fill=tk.X, expand=True)

    def _bind_events(self):
        self.bind("<Return>", self.next_image)
        self.bind("<Right>", self.next_image)
        self.bind("<Left>", self.previous_image)

        self.bind("<Control-z>", self.undo_last_action)
        self.bind("<Configure>", self._resize_image)
        # Bind label keys
        for key in self.label_key_map:
            self.bind(f"<Key-{key}>", self._on_label_key_press)

        # Allow clicking on the canvas to focus the window
        self.canvas.bind("<Button-1>", lambda e: self.focus_set())

    def load_image(self):
        # Load the current image
        image_path = self.data_manager.get_current_image()
        self.current_image = Image.open(image_path)
        self._show_image()
        
        # Update UI elements
        self.filename_label.config(text=os.path.basename(image_path))
        self.progress_label.config(
            text=f"{self.data_manager.current_index+1}/{len(self.data_manager.image_files)}"
        )
        self.log_message(f"Loaded image: {self.filename_label.cget('text')}")

        # Load current annotation
        annotation = self.data_manager.get_current_annotation()
        # - Fill description entry
        self.desc_entry.delete(0, tk.END)
        self.desc_entry.insert(0, annotation.get("description", ""))
        # - Update selected labels
        self.selected_labels = set(annotation.get("labels", []))
        self.refresh_label_buttons()

    def _show_image(self):
        # Resize and display the current image on the canvas
        canvas_width = self.canvas.winfo_width()
        canvas_height = self.canvas.winfo_height()
        
        img = self.current_image.copy()
        img.thumbnail((canvas_width, canvas_height), Image.Resampling.LANCZOS)
        self.tk_image = ImageTk.PhotoImage(img)
        
        self.canvas.delete("all")
        self.canvas.create_image(
            canvas_width//2, 
            canvas_height//2,
            anchor=tk.CENTER,
            image=self.tk_image
        )
        
    def _resize_image(self, event=None):
        if hasattr(self, 'current_image'):
            self._show_image()

    def next_image(self, event=None):
        self.data_manager.current_index = (self.data_manager.current_index + 1) % len(self.data_manager.image_files)
        self.load_image()
        
    def previous_image(self, event=None):
        self.data_manager.current_index = (self.data_manager.current_index - 1) % len(self.data_manager.image_files)
        self.load_image()


    def undo_last_action(self, event=None):
        # TODO: Implement undo functionality
        pass

    def log_message(self, message):
        self.log_text.configure(state=tk.NORMAL)
        self.log_text.insert(tk.END, message + "\n")
        self.log_text.see(tk.END)
        self.log_text.configure(state=tk.DISABLED)

    def refresh_label_buttons(self):
        for btn, label, key, color in self.label_buttons:
            if label in self.selected_labels:
                # Use a darker shade of the color when selected
                def darken(hex_color, factor=0.7):
                    hex_color = hex_color.lstrip('#')
                    rgb = tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
                    dark_rgb = tuple(int(c * factor) for c in rgb)
                    return '#{:02x}{:02x}{:02x}'.format(*dark_rgb)
                btn.config(relief="sunken", bg=darken(color))
            else:
                btn.config(relief="raised", bg=color)      # Reset to original color when not selected

    def toggle_label(self, label, key):
        # Toggle the label selection state
        if label in self.selected_labels:
            self.selected_labels.remove(label)
        else:
            self.selected_labels.add(label)
        self.refresh_label_buttons()
        self.save_current_annotation()

    def on_label_click(self, label, key):
        # Handle label button click
        self.toggle_label(label, key)

    def _on_label_key_press(self, event):
        # Handle label key press events (if the focus is not on the description entry)
        if self.focus_get() == self.desc_entry:
            return
        key = event.keysym.lower()
        if key in self.label_key_map:
            label, label_key = self.label_key_map[key]
            self.toggle_label(label, label_key)

    def save_current_annotation(self):
        annotation = {
            "description": self.desc_entry.get(),
            "labels": list(self.selected_labels)
        }
        self.data_manager.set_current_annotation(annotation)

    def append_desc_option(self, option_text, seperator=""):
        # Append the selected description option to the entry field
        current = self.desc_entry.get()
        self.desc_entry.delete(0, tk.END)
        self.desc_entry.insert(tk.END, current + option_text + seperator)
        self.save_current_annotation()

if __name__ == "__main__":
    app = AnnotationUI()
    app.mainloop()