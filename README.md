# Cascade-Scripts
Contains all scripts for Cascade CMS<br>
**NOTE:** Make sure you follow the instructions and install the tools needed before running scripts.
|scripts| description |
|---------|----------|
|[sitemap](https://github.com/Sharkdroid/Cascade-Scripts/tree/sitemap)| creating sitemap out of csv files |
|[image_rename](https://github.com/Sharkdroid/Cascade-Scripts/tree/image_rename)| renaming images |
|[xml_edit](https://github.com/Sharkdroid/Cascade-Scripts/tree/xml_edit)| editing XML property |

### Toolchain
| programs| links |
|--------|--------------------------|
| Python | https://www.python.org/  (install >=3.12)|
| VSCode | https://code.visualstudio.com/download (required for VSCode extension)|
|Rainbow CSV|https://marketplace.visualstudio.com/items?itemName=mechatroner.rainbow-csv (for formatting csv files)|
### How to use
1. Clone this repo and open the working directory with VSCode
2. [Create a virtual environment](#creating-virtual-environment-for-python-in-vscode)

### Getting API key in Cascade
1. Click on the User Menu: The circle with your profile picture
2. Click `API Key`
3. Click `Regenerate API Key`
4. Copy & paste into the `.env`

### Creating virtual environment for Python in VSCode
1. Press `Ctrl+Shift+P` type "create environment"
2. select option starting with 'Python:Create Environment...'
3. Select your installed version of Python
4. When prompted select `requirements.txt`
