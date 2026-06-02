import csv
import json
import requests
import tomllib
from typing import Dict, Any, List
from sys import exit
from warnings import warn
from datetime import datetime
import io
from PIL import Image
from collections import deque
from jsonpath_ng.ext import parse

# RUN SCRIPT WITH THE WORKING DIRECTORY UNDER image_rename/ OTHERWISE SCRIPT CANNOT FIND THE JSON SAMPLE USING RELATIVE PATH.

# Currently, the "Impact Image" should always be 1920x400px.

# logging
LOG_PREFIX = datetime.now().strftime("%Y%m%dT%H%M%S")
log_file = open(f"./{LOG_PREFIX}.log", "w", buffering=1)
possible_impact_log = open(f"./{LOG_PREFIX}.possible-impact-images.log", "w", buffering=1)
in_use_impact_wrong_size_log = open(f"./{LOG_PREFIX}.in-use-impact-wrong-size.log", "w", buffering=1)
impact_filename_wrong_size_log = open(f"./{LOG_PREFIX}.impact-name-wrong-size.log", "w", buffering=1)

IMPACT_GROUP_JSONPATH = parse("$..structuredDataNodes[?(@.identifier=='impact')]")
IMPACT_IMG_JSONPATH = parse("$[?(@.identifier=='img')]")
 
# Goal: detect every image with exactly that pixel size that exists in _files/images, move it to a dedicated folder for "old impact images" (real name tbd), then republish those images and all pages that use them.
 
# Cleanup goal 1: detect any image within ~20% (exact value tbd) of that specific size and output a list of 'possible impact images to manually check'
# Cleanup goal 2: detect any image attached to the Impact area of a data definition that ISN'T the correct specified pixel size and output a list to check manually
# Cleanup goal 3: detect any image with a filename that includes the word "impact" that ISN'T the correct pixel size and output a list to check


with open("./config.toml", "rb") as f:
    config = tomllib.load(f)

# read configuration values with error handling, so missing fields are reported
try:
    #GLOBAL
    api_key = config["global"]["api_key"]
    platform = config["global"]["platform"]

    # iamge_rename specific settings
    script_settings = config["image_rename"]
    sitename = script_settings["cascade_site"]
    root_folder_path = script_settings["root_folder_path"]
    target_percent = int(script_settings["within_percent"])
    target_dim_split = script_settings["target_dimensions"].split("x", maxsplit=1)
    if len(target_dim_split) == 2:
        t_width, t_height = target_dim_split
        target_dim = ( int(t_width), int(t_height) )
    else:
        raise IndexError("too many values to unpack only: [WIDTH]x[HEIGHT]") 


except KeyError as err:
    print(f"Configuration error: {err}")
    exit(1)


SEARCH_PARMETER = {
    "searchInformation": {
      "searchTerms":f"{root_folder_path} *.jpg *.png",
      "siteName": sitename,
      "searchFields": ["path"],
      "searchTypes": ["file"]
    }
  }

# setup header after obtaining api_key
header = {
    "Content-Type": "application/json",
    "Authorization": f"Bearer {api_key}"
}

# platform-specific base url evaluation
if platform == "apptest":
    base_url = "https://cascadeapptest.csi.edu:8443/api/v1"
    print("Using apptest")
elif platform == "prod":
    print("Using prod")
    base_url = "https://cascade.csi.edu:8443/api/v1"
else:
    raise EnvironmentError("Configuration error: 'platform' must be 'apptest' or 'prod'")

# extracts the actual asset fields
def strip_cascade_object(raw_response: Dict[str, Any], type_asset) -> Dict[str, Any]:
    return raw_response["asset"][type_asset]



# Helper functions
def ret_by_id(id:str, type:str):
    return f"{base_url}/read/{type}/{id}"
def ret_by_path(path: str, type:str):
    return f"{base_url}/read/{type}/{sitename}/{path}"

def is_file(child: Dict[str, Any]):
    return child["type"] == "file"
def is_folder(child: Dict[str, Any]):
    return child["type"] == "folder"

def is_within_tolerance(img_dim:tuple[int, int], target_dim:tuple[int, int], tolerance_pct: int) -> bool:
    
    target_w, target_h = target_dim
    w, h = img_dim

    # Calculate the allowed margin
    w_margin = target_w * (tolerance_pct / 100)
    h_margin = target_h * (tolerance_pct / 100)
    
    # Check if both dimensions are within the bounds
    width_ok = (target_w - w_margin) <= w <= (target_w + w_margin)
    height_ok = (target_h - h_margin) <= h <= (target_h + h_margin)
    
    return width_ok and height_ok


        

def get_page_relationship_ids(session: requests.Session, asset: Dict[str, Any]) -> List[str]:
    relationship_url = f"{base_url}/relationships/file/{asset.get('id')}"
    response = session.get(relationship_url)
    if response.status_code != 200:
        log_file.write(f"ERROR: relationship lookup failed for {asset.get('name')} id={asset.get('id')} status={response.status_code}\n")
        return []

    body = response.json()
    relationships = body.get("relationships")
    if not isinstance(relationships, list):
        log_file.write(f"ERROR: invalid relationships payload for {asset.get('name')} id={asset.get('id')}\n")
        return []

    page_ids: List[str] = []
    for relationship in relationships:
        identifier = relationship.get("identifier")
        if isinstance(identifier, dict) and identifier.get("type") == "page":
            page_id = identifier.get("id") or relationship.get("id")
            if isinstance(page_id, str):
                page_ids.append(page_id)
            else:
                log_file.write(f"WARNING: page relationship missing id for {asset.get('name')}\n")

    return page_ids


def fetch_related_page_assets(session: requests.Session, page_ids: List[str]) -> List[Dict[str, Any]]:
    pages: List[Dict[str, Any]] = []
    for page_id in page_ids:
        req = session.get(ret_by_id(page_id, "page"))
        if req.status_code != 200:
            log_file.write(f"ERROR: failed to read related page id={page_id} status={req.status_code}\n")
            continue

        res = req.json()
        if res.get("message"):
            log_file.write(f"ERROR: cascade returned message for related page id={page_id}: {res.get('message')}\n")
            continue

        try:
            page_asset = strip_cascade_object(res, "page")
            pages.append(page_asset)
        except Exception as exc:
            log_file.write(f"ERROR: malformed page asset for id={page_id}: {exc}\n")

    return pages


def get_impact_img_paths(page_asset: Dict[str, Any]) -> List[str]:
    paths: List[str] = []
    for group_match in IMPACT_GROUP_JSONPATH.find(page_asset):
        group_nodes = group_match.value.get("structuredDataNodes", [])
        has_display_impact = any(
            n.get("identifier") == "display-impact" and n.get("text") == "Yes"
            for n in group_nodes
        )
        if not has_display_impact:
            continue
        for img_match in IMPACT_IMG_JSONPATH.find(group_nodes):
            file_path = img_match.value.get("filePath")
            if file_path:
                paths.append(file_path)
    return paths


def log_dims(s: requests.Session, l: List[Dict[str, Any]]):
    if len(l) == 0:
        log_file.write("No files contained on this directory level\n")
        return

    for asset_file in l:
        asset_id = asset_file.get("id")
        if not asset_id:
            log_file.write("ERROR: asset entry missing id\n")
            continue

        req = s.get(ret_by_id(asset_id, "file"))
        if req.status_code != 200:
            log_file.write(f"ERROR: failed to read file asset id={asset_id} status={req.status_code}\n")
            continue

        res = req.json()
        if res.get("message"):
            log_file.write(f"ERROR: Cascade returned message for file id={asset_id}: {res.get('message')}\n")
            continue

        asset = strip_cascade_object(res, "file")
        asset_path = asset.get("path", "")
        asset_name = asset.get("name", asset_path)

        if asset_path.lower().endswith((".svg", ".pdf")):
            log_file.write(f"SKIP: {asset_name} ({asset_path}) not a valid image format\n")
            continue

        try:
            decoded_data = bytes([b & 0xFF for b in asset["data"]])
            img_info = Image.open(io.BytesIO(decoded_data))
        except Exception as exc:
            log_file.write(f"ERROR: failed to decode/open image for {asset_name} ({asset_path}): {exc}\n")
            continue

        within_tolerance = is_within_tolerance(img_info.size, target_dim, target_percent)
        status = "OKAY" if within_tolerance else "WARN"
        log_file.write(f"{status}: {asset_name} ({asset_path}) size={img_info.size} within_tolerance={within_tolerance}\n")

        if within_tolerance:
            possible_impact_log.write(f"{asset_name}\t{asset_path}\t{img_info.size}\n")
            log_file.write(f"SUCCESS: logged {asset_name} to possible impact images\n")
        else:
            log_file.write(f"FAILURE: {asset_name} is outside the configured tolerance\n")

        if "impact" in asset_path.lower() or "impact" in asset_name.lower():
            if not within_tolerance and not asset_path.startswith("_files/images/homepage/"):
                impact_filename_wrong_size_log.write(f"{asset_name}\t{asset_path}\t{img_info.size}\n")
                log_file.write(f"SUCCESS: logged {asset_name} to impact filename wrong size log\n")
            else:
                log_file.write(f"INFO: {asset_name} contains 'impact' in the filename but is within tolerance\n")

        related_page_ids = get_page_relationship_ids(s, asset)
        if related_page_ids:
            log_file.write(f"SUCCESS: found {len(related_page_ids)} related page relationship(s) for {asset_name}\n")
            related_pages = fetch_related_page_assets(s, related_page_ids)
            if related_pages:
                impact_file_paths: List[str] = []
                for page in related_pages:
                    impact_file_paths.extend(get_impact_img_paths(page))

                if asset_path in impact_file_paths:
                    if not within_tolerance:
                        paths_str = ",".join(impact_file_paths)
                        in_use_impact_wrong_size_log.write(
                            f"{asset_name}\t{asset_path}\t{img_info.size}\t"
                            f"related_pages={','.join(related_page_ids)}\t"
                            f"impact_img_paths={paths_str}\n"
                        )
                        log_file.write(f"SUCCESS: logged {asset_name} to in-use impact wrong size log\n")
                    else:
                        log_file.write(f"INFO: {asset_name} is related to an impact page and is within tolerance\n")
                elif impact_file_paths:
                    log_file.write(f"INFO: {asset_name} is not the impact image on its related page(s)\n")
                else:
                    log_file.write(f"INFO: related pages for {asset_name} do not contain display-impact=Yes\n")
            else:
                log_file.write(f"WARNING: no related page assets could be fetched for {asset_name}\n")
        else:
            log_file.write(f"INFO: no related page relationships found for {asset_name}\n")


try:
    log_file.write(f"Running {__file__} @{datetime.now()}\n")
    print("Program running. This may take a few minutes...")

    with requests.session() as session:
        session.headers.update(header)
        
        init_resq = session.post(f"{base_url}/search",json=SEARCH_PARMETER)
        body = init_resq.json()
        if init_resq.status_code == 200 and "message" not in body:
            matches: List[Dict[str, Any]] = body['matches']
            log_dims(session, matches)
        else:
            log_file.write(f"A network error occurred:[CASCADE] {init_resq.text} ")



except RuntimeWarning as e:
    print(f"RuntimeWarning: {str(e)}")
finally:
    log_file.close()
    possible_impact_log.close()
    in_use_impact_wrong_size_log.close()
    impact_filename_wrong_size_log.close()
    print("Cleanup")