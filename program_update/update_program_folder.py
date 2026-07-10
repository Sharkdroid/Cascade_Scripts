import copy
import csv
import json
import requests
import tomllib
from typing import Dict, Any
from sys import exit
from datetime import datetime
from folder_template import folder_template_dict

# logging
log_file = open(f'./{datetime.now().isoformat()}.log', 'w', buffering=1)

with open("./config.toml", "rb") as f:
    config = tomllib.load(f)

# read configuration values with error handling, so missing fields are reported
try:
    api_key = config["global"]["api_key"]
    platform = config["global"]["platform"]

    script_settings = config["program_update"]
    csv_path = script_settings["rename_csv_path"]
    root_folder_path = script_settings["root_folder_path"]
    sitename = script_settings["sitename"]
except KeyError as err:
    print(f"Configuration error: {err}")
    exit(1)

# platform-specific base url evaluation
if platform == "apptest":
    base_url = "https://cascadeapptest.csi.edu:8443/api/v1"
    print("Using apptest")
elif platform == "prod":
    base_url = "https://cascade.csi.edu:8443/api/v1"
    print("Using prod")
else:
    raise EnvironmentError("Configuration error: 'platform' must be 'apptest' or 'prod'")

header = {
    "Content-Type": "application/json",
    "Authorization": f"Bearer {api_key}"
}


# extracts the actual asset fields
def strip_cascade_object(raw_response: Dict[str, Any], type_asset) -> Dict[str, Any]:
    return raw_response["asset"][type_asset]


# walks the template down through single-key nested dicts (e.g. asset -> folder)
# to find the actual object to populate, so the script doesn't need to hardcode
# the template's wrapper keys.
def get_innermost_dict(d: Dict[str, Any]) -> Dict[str, Any]:
    while isinstance(d, dict) and len(d) == 1:
        (_, only_value), = d.items()
        if isinstance(only_value, dict):
            d = only_value
        else:
            break
    return d



template = folder_template_dict

try:
    log_file.write(f"Running {__file__} @{datetime.now()}\n")
    print("Program running. This may take a few minutes...")

    with requests.session() as session:
        session.headers.update(header)

        with open(csv_path, newline="") as csv_file:
            reader = csv.reader(csv_file)
            next(reader, None)  # skip header row

            for row in reader:
                name_value, display_value = row[0], row[1]

                row_payload = copy.deepcopy(template)
                inner = get_innermost_dict(row_payload)
                inner["name"] = name_value
                inner["siteName"] = sitename
                inner["parentFolderPath"] = root_folder_path
                inner["metadata"]["displayName"] = display_value
                inner["metadata"]["title"] = display_value

                create_request = session.post(f"{base_url}/create", json=row_payload)
                create_response: Dict[str, Any] = create_request.json()

                if create_request.status_code == 200 and not create_response.get("message"):
                    log_file.write(f"SUCCESS: created folder '{name_value}'\n")
                else:
                    log_file.write(
                        f"ERROR: failed to create folder '{name_value}': {create_response.get('message')}\n"
                    )

except Exception as e:
    log_file.write(f"ERROR: something else has occured program terminated prematurely: {e}\n")
finally:
    log_file.close()
    print("Cleanup")
