import json
import traceback
import requests
from typing import Dict, Any
from sys import exit
import configparser
from warnings import warn
from datetime import datetime

"""
TODO
    1. configs
        - path to parent folder of the posts
        - content-type: page
    2. read the parent folder
    3. get children with the 'contentTypePath' of 'Path' only
    4. traverse 'structuredData'


"""
#logging
log_file = open(f'./{datetime.now().isoformat()}.log', 'w', buffering=1)

config = configparser.ConfigParser()
config.read('config.ini')

# fetch required configuration values with explicit error handling
try:
    api_key = config.get("GLOBAL", "api_key")
    platform = config.get("GLOBAL", "platform")
    parent_folder_path = config.get("press_script", "post_folder_path")
    sitename = config.get("press_script", "cascade_site")
    asset_type = config.get("press_script", "file_types")
except (configparser.NoSectionError, configparser.NoOptionError) as err:
    print(f"Configuration error: {err}")
    exit(1)

header = {
    "Content-Type": "application/json",
    "Authorization": f"Bearer {api_key}"
}

# interpret platform setting
if platform == "apptest":
    base_url = "https://cascadeapptest.csi.edu:8443/api/v1"
    print("Using apptest")
elif platform == "prod":
    base_url = "https://cascade.csi.edu:8443/api/v1"
    print("Using prod")
else:
    raise EnvironmentError("Configuration error: 'platform' must be 'apptest' or 'prod'")


# extracts the actual asset fields
def strip_cascade_object(raw_response: Dict[str, Any], type_asset) -> Dict[str, Any]:
    return raw_response["asset"][type_asset]

def rebuild_cascade_object(flatten_fields: Dict[str, Any], type_asset):
    return {
                "asset":{
                    type_asset:flatten_fields
                }
            }
    

try:
    log_file.write(f"Running no_nav_press.py @{datetime.now()}\n")
    print("Program running. This may take a few minutes...")
    with requests.session() as session:
        session.headers.update(header)
        base_folder_request = session.get(f"{base_url}/read/folder/{sitename}/{parent_folder_path}")
        data = base_folder_request.json()
        all_pages = strip_cascade_object(data, "folder")["children"]
        log_file.write(f"List of pages in the {parent_folder_path}:\n")
        for page in all_pages:
            uuid = page['id']
            page_path = page["path"]["path"]
            log_file.write(f"|- Getting {page_path}\n")
            page_request = session.get(f"{base_url}/read/{asset_type}/{uuid}")
            data = page_request.json()
            page_asset = strip_cascade_object(data, asset_type)
            log_file.write("    |-- Checking if asset is a post\n")
            if page_asset["contentTypePath"] == "Post":
                root_node = page_asset["structuredData"]["structuredDataNodes"]
                is_type_press_release = False
                [
                    is_type_press_release := field["text"] == 'press' or field["text"] == 'faculty'
                    for node in root_node 
                    for field in node["structuredDataNodes"] 
                    if node["identifier"] == "post_details" and field["identifier"] == "postType"
                ]
                if not is_type_press_release:
                    log_file.write("*skipped: not a press release*")
                    continue
                # edit the asset metadata
                if page_asset["metadata"] and page_asset["metadata"]["dynamicFields"]:
                    metadata_fields = page_asset["metadata"]["dynamicFields"]
                    for field in metadata_fields:
                        if field["name"] == 'display-navigation':
                            field["fieldValues"][0]["value"] = "No"
                else:
                    log_file.write("Unable to get metadata and dynamicFields from above asset ^^^^\n")
                edit_request = session.post(f"{base_url}/edit/{asset_type}/{uuid}",json=rebuild_cascade_object(page_asset, asset_type))
                edit_response = edit_request.json()
                if edit_response["success"]:
                    log_file.write("    |-- Succesfully edit \n")
                else:
                    log_file.write(f"    |-- Error updating: {edit_response}\n")
            else: #skip
                log_file.write(f"*skipped {page_path} not of Post content type*\n")
                continue
except Exception as e:
    log_file.write("ERROR: something else has occured program terminated prematurely")
    print(f"response:{data}")
    traceback.print_exc()
finally:
    log_file.close()
    print("Cleanup")
