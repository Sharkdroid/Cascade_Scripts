# Cascade-Scripts
Contains all scripts for Cascade CMS<br>
**NOTE:** Make sure you follow the instructions and install the tools needed before running scripts.

|scripts| description |
|---------|----------|
|[sitemap](https://github.com/Sharkdroid/Cascade_Scripts/tree/master/sitemap) | creating sitemap out of csv files |
|[image_rename](https://github.com/Sharkdroid/Cascade_Scripts/tree/master/image_rename) | audits image assets for old/incorrect impact banner dimensions |
|[press_release_no_nav](https://github.com/Sharkdroid/Cascade_Scripts/tree/master/press_release_no_nav)| change display nav on Post assets |
|[programs_creation](https://github.com/Sharkdroid/Cascade_Scripts/tree/master/programs_creation)| bulk-creates Program Folder assets from a CSV file |
|[xml_edit](https://github.com/Sharkdroid/Cascade_Scripts/tree/master/xml_edit)| editing XML property / swapping widget asset references |

### Toolchain
| programs| links |
|--------|--------------------------|
| Python | https://www.python.org/  (install >=3.12)|
| VSCode | https://code.visualstudio.com/download (required for VSCode extension)|
| Rainbow CSV | https://marketplace.visualstudio.com/items?itemName=mechatroner.rainbow-csv (for formatting csv files)|

### How to use
1. Clone this repo and open the working directory with VSCode
2. [Create a virtual environment](#creating-virtual-environment-for-python-in-vscode)
3. Install dependencies from `requirements.txt` (done automatically if prompted during environment creation, otherwise run `pip install -r requirements.txt`)
4. Fill in [`config.toml`](https://github.com/Sharkdroid/Cascade_Scripts/blob/master/config.toml) with your API key and the settings for the script you want to run (see each script's README, linked in the table above, for its specific `config.toml` section)

### Getting API key in Cascade
1. Click on the User Menu: The circle with your profile picture
2. Click `API Key`
3. Click `Regenerate API Key`
4. Copy & paste into the `api_key` field under `[global]` in [`config.toml`](https://github.com/Sharkdroid/Cascade_Scripts/blob/master/config.toml)

### config.toml
All scripts read their settings from a single `config.toml` file in the repo root.
- `[global]` — `api_key` and `platform` (`apptest` or `prod`), shared by every script
- `[sitemap]` — settings for the sitemap script
- `[image_rename]` — settings for the image impact audit script
- `[press_script]` — settings for the press_release_no_nav script
- `[xml_edit]` — settings for the xml_edit script
- `[program_update]` — settings for the programs_creation script

### Creating virtual environment for Python in VSCode
1. Press `Ctrl+Shift+P` type "create environment"
2. select option starting with 'Python:Create Environment...'
3. Select your installed version of Python
4. When prompted select `requirements.txt`
