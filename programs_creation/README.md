# Program Folder Creation Script

### Description
Bulk-creates "Program Folder" folder assets in Cascade from a CSV file. For each row, the script fills in `folder_template.json` with the folder's name, display name/title, site name, and parent folder path, then POSTs the result to Cascade's `/create` endpoint.

The script is `create_folders.py` and it creates folders under the site configured in `program_creation.sitename`.

### Prequisites
Make sure you follow the installation process [here](https://github.com/Sharkdroid/Cascade-Scripts) before continuing.

### Usage
Run from the root directory so the script can resolve its relative paths correctly:
```bash
python3 program_creation/create_folders.py
```

### Configuration
The `config.toml` file contains the `program_creation` section used by this script:
- `rename_csv_path` — path to the CSV file of folders to create
- `root_folder_path` — parent folder path the new folders are created under
- `sitename` — Cascade site name

Example config values:
```toml
[program_creation]
rename_csv_path = "./programs_creation/<filename>.csv"
root_folder_path = "programs"
sitename = "www.csi.edu"
```

### CSV format
The header row is skipped. For each remaining row:
- column 1 — folder `name`
- column 2 — `displayName`/`title` value

### Log output
The script writes a single log file into the current folder:
- `<timestamp>.log`

### Notes
This script only creates folders; it does not check whether a folder with the same name already exists at the target path.
