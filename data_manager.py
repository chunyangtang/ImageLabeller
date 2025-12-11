import json
import os
import re
import random

class DataManager:
    """Image data management class"""
    def __init__(self, data_folder, config=None):
        self.data_folder = data_folder
        self.config = config or {}
        self.meta_file = os.path.join(data_folder, "annotations.json")
        self.image_files = []
        self.annotations = {}
        self.current_index = 0
        self.load_data()

    def load_data(self):
        """Load images and annotations from the data folder."""
        # 1. List valid files
        all_files = [f for f in os.listdir(self.data_folder)
                     if f.lower().endswith(('.png', '.jpg', '.jpeg', '.bmp', '.tiff', '.tif'))]

        # 2. Filter (Regex)
        include_patterns = self.config.get("regex_include", [])
        exclude_patterns = self.config.get("regex_exclude", [])
        
        filtered_files = []
        for f in all_files:
            # "and" logic for includes: must match ALL patterns if any exist
            if include_patterns:
                if not all(re.search(p, f) for p in include_patterns):
                    continue
            
            # "and" logic for excludes: exclude if matches ALL patterns if any exist
            # Note: User request "program will treat them as 'and' logic". 
            # If exclude = ["a", "b"], exclude file if it contains 'a' AND 'b'.
            if exclude_patterns:
                if all(re.search(p, f) for p in exclude_patterns):
                    continue
            
            filtered_files.append(f)
        
        self.image_files = filtered_files

        # 3. Sort
        sort_by = self.config.get("sort_by", "date") # Default to date (old behavior)
        sort_reverse = self.config.get("sort_reverse", False)

        if sort_by == "name":
            self.image_files.sort(key=lambda x: x.lower(), reverse=sort_reverse)
        elif sort_by == "natural":
            def natural_keys(text):
                return [int(c) if c.isdigit() else c.lower() for c in re.split(r'(\d+)', text)]
            self.image_files.sort(key=natural_keys, reverse=sort_reverse)
        elif sort_by == "random":
            # Fixed seed could be useful, but random usually implies different every time? 
            # Or maybe just shuffled once. Random sort usually ignores 'reverse'.
            random.shuffle(self.image_files)
        else: # "date" or unknown
            # Default behavior: sort by mtime
            self.image_files.sort(key=lambda x: os.path.getmtime(os.path.join(self.data_folder, x)), reverse=sort_reverse)

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