import requests
from typing import Dict, Any, Iterator
from sys import exit
import configparser
from warnings import warn
from datetime import datetime
import json

#logging
log_file = open(f'./{datetime.now().isoformat()}.log', 'w', buffering=1)
config = configparser.ConfigParser()
config.read('config.ini')

# fetch required configuration values with explicit error handling
try:
    api_key = config.get("GLOBAL", "api_key")
    platform = config.get("GLOBAL", "platform")
    sitename = config.get("xml_edit", "cascade_site")
    asset_type = config.get("xml_edit", "asset_type")
    target_page = config.get("xml_edit", "target_page_path")
    search_path = config.get("xml_edit", "search_path")
    new_asset_path = config.get("xml_edit", "new_asset_path")
except (configparser.NoSectionError, configparser.NoOptionError) as err:
    print(f"Configuration error: {err}")
    exit(1)

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

def rebuild_cascade_object(flatten_fields: Dict[str, Any], type_asset) -> Dict[str, Dict[str, Any]]:
    return {
                "asset":{
                    type_asset:flatten_fields
                }
            }


header = {
    "Content-Type": "application/json",
    "Authorization": f"Bearer {api_key}"
}

# recursive logic
def traverseStruct(cur_node: Dict[str, Any] | list[Dict[str, Any]], next_search: Iterator[str]) -> Dict[str, Any]:
    if isinstance(cur_node, list):
        search_term = next(next_search, None)
        if search_term is None:
            raise ValueError(f"Ambiguous search: Path ended at a list. Use a more specific path.")
        log_file.write(f"|     |---Current Search Term:{search_term}\n")
        for child in cur_node: # traverse all children nodes
            if child.get('identifier') == search_term and child.get('type') != "group": # terminal node
                return child
            elif child.get('identifier') == search_term:
                return traverseStruct(child, next_search)
        raise RuntimeError(f"[ERROR]: Supplied search term {search_term} does not exist at this layer")
    else:
        log_file.write(f"|--Parent Node:{cur_node.get('identifier')}\n")
        
        childrens = cur_node.get('structuredDataNodes')
        
        if childrens:
            return traverseStruct(childrens, next_search)
        raise RuntimeError(f"Reached a terminal node {cur_node.get('identifier')} but still have path terms left to find.")

try:
    log_file.write(f"Running {__file__} @{datetime.now()}\n")
    print("Program running. This may take a few minutes...")
    with requests.session() as session:
        session.headers.update(header)
        
        # Retrieve information for the new asset like id and path (also verify that the asset exists)
        # This is the asset that
        inject_asset_request = session.get(
            f"{base_url}/read/{asset_type}/{sitename}/{new_asset_path}"
        )

        # This is the page you are trying to edit
        page_request = session.get(
            f"{base_url}/read/{asset_type}/{sitename}/{target_page}"
        )

        if page_request.status_code == 200 and inject_asset_request.status_code == 200:
            page_response: Dict[str, Any] = page_request.json()
            new_asset_response: Dict[str, Any] = inject_asset_request.json()
            if page_response.get("message") or new_asset_response.get("message"):
                log_file.write(
f"""[ERROR]: Something went wrong with the following fetches:
*** Edit Page Failed:{page_response.get("message")}
*** Injecting Asset:{new_asset_response.get("message")}
"""
                )
                raise RuntimeError("Cascade Error: refer to the log file for more info.")

            search_iter = iter(search_path.split("/"))

            asset = strip_cascade_object(page_response, asset_type)
            new_asset = strip_cascade_object(new_asset_response, asset_type)

            root = asset["structuredData"]["structuredDataNodes"]
            log_file.write("Attempting to traverse structureData:\n")
            log_file.write("|--Parent Node:/\n")
            widget = traverseStruct(root, search_iter)
            widget["pageId"] = new_asset["id"]
            widget["pagePath"] = new_asset["path"]
            
            
            log_file.write(f"Attempting edits on {target_page}\n")
            #make edits
            edit_request = session.post(
                f"{base_url}/edit/{asset_type}/{sitename}/{target_page}",
                json=rebuild_cascade_object(asset, asset_type)
            )
            edit_response: Dict[str, Any] = edit_request.json()
            if edit_request.status_code == 200 and not edit_response.get("message"):
                log_file.write("    Write operation was a success\n")
            else:
                log_file.write(f"   Write operation was not successful Cascade returned:{edit_response.get("message")}\n")


        # NOTE: The following are rules that the structure follows when viewing the XML preview in Cascade.
        # 1. identifier fields in the structure translates to XML tag names
        # 2. in the presents of type text in the structure it translates to value between tags 
        #    EDGE CASE: if text field not present it represents a self-closing tag in XML e.g. <identifier/>
        # 3. besides text types, asset type embed the <system-data-structure> of the asset into the current data-structure tag. 
        #    These nodes requires the "assetType" field. Optionally, a path or id to the asset.
        #    It must be in this format "[asset]Id" or "[asset]Path" [asset] is the placeholder for the asset type (lower case)
        # 4. the text values are often raw unparsed XML so it contains "::CONTENT-XML-CHECKBOX::" prefixes,
        #    requiring some regex filtering. However, I'm uncertain about the exact prefix so use regex to
        #    capture this pattern. Within the preview they translate to


except Exception as e:
    log_file.write("ERROR: something else has occured program terminated prematurely")
finally:
    log_file.close()
    print("Cleanup")
