import json
import os

class DataManager:
    """Image data management class"""
    def __init__(self, data_folder):
        self.data_folder = data_folder
        self.meta_file = os.path.join(data_folder, "annotations.json")
        self.image_files = []
        self.annotations = {}
        self.current_index = 0
        self.load_data()

    def load_data(self):
        """Load images and annotations from the data folder."""
        all_files = [f for f in os.listdir(self.data_folder)
                     if f.lower().endswith(('.png', '.jpg', '.jpeg', '.bmp', '.tiff', '.tif'))]
        self.image_files = sorted(all_files, key=lambda x: os.path.getmtime(os.path.join(self.data_folder, x)))

        if not os.path.exists(self.meta_file):
            self._initialize_dataset()
        else:
            with open(self.meta_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            if isinstance(data, dict) and 'annotations' in data:
                # New format: { "last_index": <int>, "annotations": { ... } }
                self.annotations = data.get('annotations', {})
                self.current_index = data.get('last_index', 0)
            else:
                # Legacy format: just a dict of annotations
                self.annotations = data
                self.current_index = 0

    def _initialize_dataset(self):
        self.annotations = {}
        for image in self.image_files:
            self.annotations[image] = {
                "description": "",
                "labels": [],
            }

    def get_current_image(self):
        return os.path.join(self.data_folder, self.image_files[self.current_index])

    def get_current_annotation(self):
        image_name = self.image_files[self.current_index]
        return self.annotations.get(image_name, {})
    
    def set_current_annotation(self, annotation):
        image_name = self.image_files[self.current_index]
        self.annotations[image_name] = annotation
        self.save_annotations()

    def save_annotations(self):
        """Write annotations and the last viewed index back to disk."""
        data = {
            'last_index': self.current_index,
            'annotations': self.annotations
        }
        with open(self.meta_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)