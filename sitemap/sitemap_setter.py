import csv
import json
import requests
from typing import Dict, Any
from os import getenv
from sys import exit
import configparser
from warnings import warn
from datetime import datetime

#logging
log_file = open(f'./{datetime.now().isoformat()}.log', 'w', buffering=1)

config = configparser.ConfigParser()
config.read('config.ini')

# fetch required configuration values with explicit error handling
try:
    api_key = config.get("GLOBAL", "api_key")
    platform = config.get("GLOBAL", "platform")
    csv_path = config.get("sitemap", "csv_path")
    sitename = config.get("sitemap", "cascade_site")
    asset_type = config.get("sitemap", "asset_type")
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
def strip_cascade_object(raw_response: Dict[str, Any]) -> Dict[str, Any]:
    return raw_response["asset"][asset_type]

# retrieves the location of the sitemap metadata then changes its value. 
def set_sitemap_if_exists(asset: Dict[str, Any]) -> Dict[str, Any]:
    # check if should be published
    if "shouldBePublished" in asset and asset["shouldBePublished"]:
        fields = asset["metadata"]["dynamicFields"]
        sitemap_field = [ field for field in fields if field['name'] == "sitemap" ]
        # check if sitemap exists
        if len(sitemap_field) > 0:
            field_value = sitemap_field[0]["fieldValues"][0]["value"]
            if field_value == 'No':
                sitemap_field[0]["fieldValues"][0]["value"] = 'Yes'
    else:
        print(f"{asset['path']} not set to publish")
    return asset
    
try:
    log_file.write(f"Running sitemap_setter.py @{datetime.now()}\n")
    print("Program running. This may take a few minutes...")
    with requests.session() as session:
        with open(csv_path, 'r') as file:
            reader = csv.reader(file)
            
            for row in reader:
                try:
                    # ignore header row
                    if row == ['id','path','site','is_published','has_sitemap_meta','sitemap_value_current']:
                        continue
                    (
                        _id, 
                        path,
                        site_name, 
                        is_published,
                        has_sitemap,
                        cur_sitemap_val
                    ) = row
                    print(f"Getting {path} ")
                    resp = session.get(
                        f"{base_url}/read/{asset_type}/{_id}",
                        headers=header
                    )
                    data = resp.json()
                    if not ("asset" in data and asset_type in data["asset"]):
                        log_file.write(f"Error: unable to parse the asset:{path} - cascade returned:{data}\n")
                        continue
                    asset = strip_cascade_object(data)
                    # if it contains metadata field
                    if "metadata" in asset and "dynamicFields" in asset["metadata"]:
                        asset = set_sitemap_if_exists(asset)
                        payload = json.dumps({"asset":{asset_type : asset}})                      
                        edit_response = session.post(
                            f"{base_url}/edit",
                            headers=header,
                            data=payload
                        )
                        edit_status = edit_response.json()
                        if "success" in edit_status and not edit_status["success"]:
                            log_file.write(f"Error: {path} unsuccessful at updating. Return message:{edit_status['message']}\n")
                        else:
                            log_file.write(f"Successfully updated {path}\n")
                except requests.JSONDecodeError:
                    print(f"Request did not return a valid JSON format. (Most likely a HTML response)")
                except requests.RequestException:
                    print(f"Unable to get extract data from {path}. ***Network issue*** ")
                    log_file.write(f"***Network issue occurred***")
                except ValueError:
                    problem_path = row[1]
                    raise RuntimeWarning(f"Please fix the row {problem_path} it contains too many columns")
except RuntimeWarning as e:
    print(f"RuntimeWarning: {str(e)}")
finally:
    log_file.close()
    print("Cleanup")