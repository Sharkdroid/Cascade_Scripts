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

# read configuration values with error handling, so missing fields are reported
try:
    api_key = config.get("GLOBAL", "api_key")
    platform = config.get("GLOBAL", "platform")
    csv_path = config.get("image_rename", "csv_path")
    sitename = config.get("image_rename", "cascade_site")
    asset_type = config.get("image_rename", "asset_type")
except (configparser.NoSectionError, configparser.NoOptionError) as err:
    print(f"Configuration error: {err}")
    exit(1)


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



try:
    log_file.write(f"Running sitemap_setter.py @{datetime.now()}\n")
    print("Program running. This may take a few minutes...")
    with requests.session() as session:
        with open(csv_path, 'r') as file:
            reader = csv.reader(file)
            
            for row in reader:
                try:
                    # ignore header row
                    if row == ['destination_path','newname']:
                        continue
                    (
                        img_path,
                        new_name
                    ) = row
                    print(f"Getting {img_path} ")

                    parent_folder_path = img_path[:img_path.rindex("/")]
                    
                    new_name += img_path[img_path.rfind('.'):]

                    new_image_path = f"{parent_folder_path}/{new_name}"

                    resp = session.get(
                        f"{base_url}/read/{asset_type}/{sitename}/{img_path}",
                        headers=header
                    )
                    data = resp.json()
                    if not ("asset" in data and asset_type in data["asset"]):
                        log_file.write(f"Error: unable to parse the asset:{img_path} - cascade returned:{data}\n")
                        continue
                    asset = strip_cascade_object(data, asset_type)
                    
                    if "metadata" in asset and "displayName" in asset["metadata"]:
                        asset['metadata']['displayName'] = new_name
                        asset_payload = json.dumps({"asset":{asset_type : asset}})
                        
                        # rename the image before moving
                        edit_response = session.post(
                                f"{base_url}/edit",
                                headers=header,
                                data=asset_payload
                            )
                        edit_status = edit_response.json()
                        if "success" in edit_status and not edit_status["success"]:
                            log_file.write(f"Error: {img_path} unsuccessful at updating. Return message:{edit_status['message']}\n")
                        else:
                            log_file.write(f"{img_path} renamed display name to {new_name}\n")
                    else:
                        log_file.write(f"Warn: Skip renaming {img_path} DisplayName, displayName metadata does not exist\n")

                    move_parameters = {
                        "moveParameters": {
                            "destinationContainerIdentifier": {
                            "path": {
                                "path": parent_folder_path,
                                "siteName": sitename
                            },
                            "type": "folder"
                            },
                            "doWorkflow": False,
                            "newName": new_name,
                            "unpublish": True
                        }
                    }

                    # move the file/renaming it
                    move_response = session.post(
                            f"{base_url}/move/{asset_type}/{sitename}/{img_path}",
                            headers=header,
                            json=move_parameters
                        )
                    
                    move_status = move_response.json()
                    if "success" in move_status and not move_status["success"]:
                        log_file.write(f"Error: unsuccessful at moving {img_path}. Return message:{move_status['message']}\n")
                        raise RuntimeError('** OPERATION UNSUCCESSFUL **\nRefer to log file for details')
                    else:
                        log_file.write(f"Moved {img_path} and renamed to {new_name}\n")

                    # publish the image first
                    img_pub_response = session.post(
                            f"{base_url}/publish/{asset_type}/{sitename}/{new_image_path}",
                            headers=header,
                        )
                    
                    img_pub_status = img_pub_response.json()
                    if "success" in img_pub_status and not img_pub_status["success"]:
                        log_file.write(f"Error: unsuccessful publish {new_image_path}. Return message:{img_pub_status['message']}\n")
                        raise RuntimeError('** OPERATION UNSUCCESSFUL **\nRefer to log file for details')
                    else:
                        log_file.write(f"Published {new_image_path}\n")

                    # pull relationships for the image
                    list_sub_response = session.get(
                            f"{base_url}/listSubscribers/{asset_type}/{sitename}/{new_image_path}",
                            headers=header,
                        )
                    
                    relationships_result = list_sub_response.json()
                    
                    if "success" in relationships_result and not relationships_result["success"]:
                        log_file.write(f"Error: unsuccessful getting relationships for {new_image_path}. Return message:{relationships_result['message']}\n")
                        raise RuntimeError('** OPERATION UNSUCCESSFUL **\nRefer to log file for details')
                    

                    log_file.write(f"Publishing related asset to {new_image_path}\n")
                    print(f"{img_path} relationships:")
                    
                    if len(relationships_result["subscribers"]) == 0:
                        log_file.write(f">> No other assets associated\n")
                        continue
                    
                    for relation_object in relationships_result["subscribers"]:
                        asset_path = relation_object['path']['path']
                        r_asset_type = relation_object['type'] # prevent naming conflict with the asset_type used for images
                        
                        # Make the the asset is publishable
                        is_publish_response = session.get(
                            f"{base_url}/read/{r_asset_type}/{sitename}/{asset_path}",
                            headers=header
                        )
                        
                        is_publish_status = strip_cascade_object(is_publish_response.json(), r_asset_type)
                        if not is_publish_status.get("shouldBePublished"):
                            log_file.write(f"*{asset_path} Skipped: shouldBePublished to False\n")
                            continue

                        print(asset_path)
                        # publish each related asset
                        publish_response = session.post(
                            f"{base_url}/publish/{r_asset_type}/{sitename}/{asset_path}",
                            headers=header,
                        )
                        publish_status = publish_response.json()
                        if "success" in publish_status and not publish_status["success"]:
                            log_file.write(f"Error: unsuccessful at publishing {asset_path}. Return message:{publish_status['message']}\n")
                            raise RuntimeError('** OPERATION UNSUCCESSFUL **\nRefer to log file for details')
                        else:
                            log_file.write(f">> Published {asset_path}\n")
                
                except requests.JSONDecodeError:
                    print(f"Request did not return a valid JSON format. (Most likely a HTML response)")
                except requests.RequestException:
                    print(f"Unable to get extract data from {img_path}. ***Network issue*** ")
                    log_file.write(f"***Network issue occurred***")
                except ValueError:
                    problem_path = row[1]
                    raise RuntimeWarning(f"Please fix the row {problem_path} it contains too many columns")
except RuntimeWarning as e:
    print(f"RuntimeWarning: {str(e)}")
finally:
    log_file.close()
    print("Cleanup")