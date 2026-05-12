# Image Impact Audit Script

### Description
Scan image assets in the configured `root_folder_path` and report:
- possible impact images within the configured size tolerance
- images with `impact` in the filename that are outside tolerance
- images related to pages with `display-impact == Yes` that are outside tolerance

The script is `banner_puller.py` and it runs against the site configured under `image_rename.cascade_site`.

### Prequisites
Make sure you follow the installation process [here](https://github.com/Sharkdroid/Cascade-Scripts) before continuing.

This script depends on the Python packages listed in `requirements.txt`, including `requests`, `Pillow`, and `jsonpath-ng`.

### Usage
Run from the `image_rename/` directory so the script can resolve its relative paths correctly:
```bash
python3 banner_puller.py
```

### Configuration
The `config.toml` file contains the `image_rename` section used by this script:
- `cascade_site` — Cascade site name
- `root_folder_path` — root image folder path to search
- `within_percent` — size tolerance percentage for the target dimensions
- `target_dimensions` — required image dimensions in `WIDTHxHEIGHT` format
- `new_folder_name` — descriptive folder name for old impact images

Example config values:
```toml
[image_rename]
cascade_site = "www.csi.edu"
root_folder_path = "_files/images"
within_percent = 20
target_dimensions = "1920x400"
new_folder_name = "old impact images"
```

### Log output
The script writes these files into the current folder:
- `<timestamp>.log`
- `<timestamp>.possible-impact-images.log`
- `<timestamp>.in-use-impact-wrong-size.log`
- `<timestamp>.impact-name-wrong-size.log`

### Notes
This script inspects image assets and reports candidates; it does not rename or move files.

##### Related Scripts
|scripts| description |
|---------|----------|
|[sitemap](https://github.com/Sharkdroid/Cascade-Scripts/tree/sitemap)| creating sitemap out of csv files |
|[xml_edit](https://github.com/Sharkdroid/Cascade-Scripts/tree/xml_edit)| editing XML property |
