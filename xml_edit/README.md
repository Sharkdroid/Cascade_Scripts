## XML Edit Script

### Description
This script edits a page in Cascade by traversing its structured data to locate a specific widget and replacing its referenced asset (pageId and pagePath) with a new asset. It uses the Cascade API to read the target page and the new asset, perform the update, and save the changes back to Cascade.

### Prerequisites
Make sure you follow the installation process [here](https://github.com/Sharkdroid/Cascade-Scripts) before continuing.

### Use Cases
- Updating page widgets to reference different assets, such as swapping out content blocks or pages in a site's structure.
- Automating content updates for dynamic pages where widget references need to be changed programmatically.
- Maintaining consistency in asset references across multiple pages by injecting new or updated assets into existing structures.

### Required Inputs in config.ini
The script relies on configuration values from `config.ini`. Ensure the following sections and keys are properly set:

- **[GLOBAL]**
  - `api_key`: Your Cascade API key for authentication.
  - `platform`: The Cascade environment to use. Must be either "apptest" (for testing) or "prod" (for production).

- **[xml_edit]**
  - `cascade_site`: The name of the Cascade site (e.g., "www.csi.edu").
  - `asset_type`: The type of asset being edited (e.g., "page").
  - `target_page_path`: The path to the page you want to edit (e.g., "dev-misc/test").
  - `search_path`: The path within the structured data to locate the widget (e.g., "page-content/right-column/widget"). This is used to traverse the data structure.
  - `new_asset_path`: The path to the new asset to inject into the widget (e.g., "_widgets/recreation-center/ski-swap").

Update these values in `config.ini` before running the script. The script will log its progress and any errors to a timestamped `.log` file.