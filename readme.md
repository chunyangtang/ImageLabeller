# ImageLabeller

A minimal image labelling tool to label tag and discription for images. Built with Python and Tkinter.

## Features
- Add tags and descriptions to images
- Keyboard shortcut support for quick tagging and navigation
- Save and load tags and descriptions from a JSON file

## Requirements
- Python 3.x
- Tkinter
- Pillow (PIL)

## Usage
1. Clone the repository & install the requirements (or just download the binary executable).
2. Prepare `data_config.json` file, `program_config.json` file and a folder with images you want to label
3. Run the script `main.py` or the executable file.
4. Use the interface to navigate through images, add tags and descriptions, your work will be automatically saved in `annotations.json` within the same folder as the images.

### `data_config.json` example
```json
{
    "folder_path": "path/to/your/images",
    "label_groups": [
        {
            "name_1": "<key-1>",
            "name_2": "<key-2>",
        },
        {
            "name_3": "<key-3>",
            "name_4": "<key-4>",
        }
    ],
    "common_phrases": {
        "name_1": [
            [
                "Example1",
                "Example2"
            ],
            [
                "Example3",
                "Example4"
            ]
        ],
        "name_2": [
            [
                "Example5",
                "Example6"
            ],
            [
                "Example7",
                "Example8"
            ]
        ]
    },
    "seperator": "suffix of your common phrase"
}
```
- "<key-1>", "<key-2>" should be a single character, which will be used as a keyboard shortcut to add the tag.
- Use multiple items in the list to create multiple lines of tags in `label_groups` and `common_phrases`.
- The content of `common_phrases["label_name"]` will only appear when the label is selected in the `label_groups` section.
- The `seperator` will be added to the end of each common phrase when it is added to the description field.


### `program_config.json` example
(Currently no options available)
```json
{

}
```
