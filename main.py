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
        self.after(100, self._activate_on_windows)  # Activate the window after a short delay

    def _activate_on_windows(self):
        # Lift the window to the top and focus it
        self.lift()
        self.focus_force()
        self.desc_entry.focus_set()

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
        
        # A read‐only Entry for filename so users can select/copy them
        self.filename_var = tk.StringVar()
        self.filename_entry = ttk.Entry(
            self.info_frame,
            textvariable=self.filename_var,
            state='readonly',
            width=0,
        )
        self.filename_entry.config(width=len(self.filename_var.get()) + 2)
        self.filename_var.trace_add("write", lambda *args: self.filename_entry.config(width=len(self.filename_var.get()) + 2))
        self.filename_entry.pack(side=tk.LEFT)
        
        self.progress_label = ttk.Label(self.info_frame, text="")
        self.progress_label.pack(side=tk.RIGHT)

        # Input area
        self.desc_frame = ttk.Frame(self)
        self.desc_frame.pack(fill=tk.X, padx=5, pady=5)

        # - Input box
        self.desc_entry_row = ttk.Frame(self.desc_frame)
        self.desc_entry_row.pack(fill=tk.X)
        self.desc_entry = tk.Entry(self.desc_entry_row, width=60)
        self.desc_entry.pack(side=tk.LEFT, padx=(0,10), fill=tk.X, expand=True)
        self.desc_entry.bind("<KeyRelease>", lambda e: self.save_current_annotation())

        # - Description options
        desc_options = self.data_config.get("common_phrases", {})
        seperator = self.data_config.get("seperator", "")

        # --- dynamic description options container ---
        # we create an empty frame; options will be injected based on selected labels
        # – Reserve space for 3 rows of buttons –
        # estimate each row ~30px high (tweak as needed)
        row_height = 30
        reserve = 3
        # store for dynamic resizing later
        self.desc_row_height = row_height
        self.desc_reserve = reserve

        self.desc_options_container = ttk.Frame(self.desc_frame, height=row_height * reserve)
        self.desc_options_container.pack(fill=tk.X, pady=(2,0))
        self.desc_options_container.pack_propagate(False)  # do not let children shrink it below its set height

        # keep track of each label’s Frames so we can remove them individually
        self.desc_option_frames = {}

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
        # self.bind("<Configure>", self._resize_image)
        self.canvas.bind("<Configure>", lambda e: self._show_image())
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
        # self.filename_label.config(text=os.path.basename(image_path))
        # Update UI elements
        # now using the read-only Entry’s StringVar
        self.filename_var.set(os.path.basename(image_path))
        self.progress_label.config(
            text=f"{self.data_manager.current_index+1}/{len(self.data_manager.image_files)}"
        )
        self.log_message(f"Loaded image: {os.path.basename(image_path)}")

        # Load current annotation
        annotation = self.data_manager.get_current_annotation()
        # - Fill description entry
        self.desc_entry.delete(0, tk.END)
        self.desc_entry.insert(0, annotation.get("description", ""))
        # - Update selected labels
        self.selected_labels = set(annotation.get("labels", []))
        self.refresh_label_buttons()
        # after refreshing labels, populate options for existing labels
        self.update_desc_options()

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
        """Toggle label, then add or remove its option rows."""
        if label in self.selected_labels:
            self.selected_labels.remove(label)
            self._remove_desc_options(label)
        else:
            self.selected_labels.add(label)
            self._add_desc_options(label)
        self.refresh_label_buttons()
        self.save_current_annotation()

    def _add_desc_options(self, label):
        """Append this label’s option‐rows at the bottom of the container."""
        phrases_map = self.data_config.get("common_phrases", {})
        sep = self.data_config.get("seperator", "")
        frames = []
        for row in phrases_map.get(label, []):
            rf = ttk.Frame(self.desc_options_container)
            rf.pack(fill=tk.X, pady=(2,0))
            for opt in row:
                btn = ttk.Button(rf, text=opt,
                                 command=lambda o=opt, s=sep: self.append_desc_option(o, s))
                btn.pack(side=tk.LEFT, padx=2)
            frames.append(rf)
        self.desc_option_frames[label] = frames

    def _remove_desc_options(self, label):
        """Destroy Frames for that label’s options (when deselected)."""
        for rf in self.desc_option_frames.pop(label, []):
            rf.destroy()

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

    def update_desc_options(self):
        """
        For each selected label, inject its option-rows under the entry.
        Then adjust container height to show all rows, but at least reserve rows.
        """
        # clear old
        for child in self.desc_options_container.winfo_children():
            child.destroy()
        self.desc_option_frames.clear()

        phrases_map = self.data_config.get("common_phrases", {})
        sep = self.data_config.get("seperator", "")

        total_rows = 0
        # add new rows for each selected label
        for label in self.selected_labels:
            rows = phrases_map.get(label, [])
            for row in rows:
                rf = ttk.Frame(self.desc_options_container)
                rf.pack(fill=tk.X, pady=(2,0))
                for opt in row:
                    btn = ttk.Button(rf, text=opt,
                                     command=lambda o=opt: self.append_desc_option(o, sep))
                    btn.pack(side=tk.LEFT, padx=2)
                total_rows += 1
                # store if later removal per-label needed
                self.desc_option_frames.setdefault(label, []).append(rf)

        # compute new container height
        display_rows = max(total_rows, self.desc_reserve)
        new_height = display_rows * self.desc_row_height
        self.desc_options_container.configure(height=new_height)

    def append_desc_option(self, option_text, separator=""):
        """
        Append option_text + separator to the end of desc_entry,
        and immediately save annotation.
        """
        current = self.desc_entry.get()
        self.desc_entry.delete(0, tk.END)
        self.desc_entry.insert(tk.END, current + option_text + separator)
        self.save_current_annotation()

if __name__ == "__main__":
    app = AnnotationUI()
    app.mainloop()