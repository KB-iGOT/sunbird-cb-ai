import requests
import os
import json
import pandas as pd
from concurrent.futures import ThreadPoolExecutor
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from config import active_api, userID, ulcaApiKey, key_location, repo_url, sheet_name, sheet_id, folder_path, output_json_path
import time
import numpy as np

global global_dict
global_dict={}

# Function to fetch JSON files from GitHub
def fetch_github_json_names():
    
    global m_files, w_files
    repo_url_parts = repo_url.split('/')

    parent_repo = repo_url_parts[3]
    repo_name = repo_url_parts[4]
    

    contents_url = f"https://api.github.com/repos/{parent_repo}/{repo_name}/contents/{folder_path}"
    
    response = requests.get(contents_url)
    if response.status_code == 200:
        json_files = [file['name'] for file in response.json() if file['name'].endswith('.json')]
        m_files=[i for i in json_files if i.startswith("mobile")]
        w_files=[i for i in json_files if i.startswith("web")]
        return json_files
    else:
        print(f"Failed to fetch directory contents from GitHub. Status code: {response.status_code}")
        print(f"Response text: {response.text}")  

def fetch_github_json(file):
    # Replace 'blob' with 'raw' in the URL to get the raw content
    file_path = os.path.join(folder_path, file)
    file_path = file_path.replace("\\", "/")

    raw_url = f"{repo_url}/{file_path}".replace('tree', 'raw')
    response = requests.get(raw_url)
    print(response.status_code)
    if response.status_code == 200:        
        return response.json()
        
    else:
        print("Failed to fetch JSON from GitHub")
        return None

# Function to fetch data from Google Sheets
# def read_google_sheet():
#     scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
#     creds = ServiceAccountCredentials.from_json_keyfile_name(key_location, scope)
#     client = gspread.authorize(creds)

#     sheet = client.open_by_key(sheet_id).worksheet(sheet_name)
#     data = sheet.get_all_records()
#     df = pd.DataFrame(data)
#     return df
def read_google_sheet():
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    creds = ServiceAccountCredentials.from_json_keyfile_name(key_location, scope)
    client = gspread.authorize(creds)

    sheet = client.open_by_key(sheet_id).worksheet(sheet_name)
    data = sheet.get_all_records()

    # Ensure that "en_value (current)" column is included
    column_names = ["Column1", "languagekey", "en_value (current)", "hi_translated", "hi_transliterated", "hi_value(curated)",
                    "ta_translated", "ta_transliterated", "ta_value(curated)", "te_translated", "te_transliterated", "te_value(curated)",
                    "as_translated", "as_transliterated", "as_value(curated)", "bn_translated", "bn_transliterated", "bn_value(curated)",
                    "gu_translated", "gu_transliterated", "gu_value(curated)", "kn_translated", "kn_transliterated", "kn_value(curated)",
                    "ml_translated", "ml_transliterated", "ml_value(curated)", "mr_translated", "mr_transliterated", "mr_value(curated)",
                    "or_translated", "or_transliterated", "or_value(curated)", "pa_translated", "pa_transliterated", "pa_value(curated)"]

    df = pd.DataFrame(data, columns=column_names)
    return df


def update_google_sheet(merged_df):
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    creds = ServiceAccountCredentials.from_json_keyfile_name(key_location, scope)
    client = gspread.authorize(creds)

    sheet = client.open_by_key(sheet_id).worksheet(sheet_name)
    
    # Clear the existing data in the Google Sheet
    sheet.clear()

    # Convert DataFrame to list of lists for updating
    data = [merged_df.columns.tolist()] + merged_df.astype(str).values.tolist()

    # Update Google Sheet with the new data
    sheet.update("A1", data)

    return "Google Sheet updated successfully"

##############################################################################################
def parse_dict(filename, string1, dict1):
    filename=filename.split(".")[0]
    parent_dict = {}
    values = []

    for k, v in dict1.items():
        new_key = string1 + "." + k if string1 else k
        if isinstance(v, dict):
            child_dict = parse_dict(filename,new_key, v)
            parent_dict.update(child_dict)
        else:
            values.append(v)
            parent_dict[filename+"."+new_key] = v

    return parent_dict
#################################################################################################
# Function to create DataFrame from JSON files


def create_dataframe_from_json(file_name, data):
    dfs = []  
    string1=""
    dict_json = parse_dict(file_name,string1, data)
    global_dict.update(dict_json)

    df = pd.DataFrame.from_dict(dict_json, orient='index').reset_index()
    df.rename(columns={"index": "languagekey", 0: "en_value (current)"}, inplace=True)
    dfs.append(df)
    print(df)
    
    result_df = pd.concat(dfs, ignore_index=True)
    # result_df = result_df.groupby('languagekey').first()###################
    result_df.reset_index(inplace=True)

    return result_df

# Function to fetch active API
def get_active_api(taskType):
    url = "https://meity-auth.ulcacontrib.org/ulca/apis/v0/model/getModelsPipeline"
    payload = json.dumps({
      "pipelineTasks": [
        {
          "taskType": taskType,
          "config": {
            "language": {
              "sourceLanguage": "en"
            }
          }
        }
      ],
      "pipelineRequestConfig": {
        "pipelineId": "64392f96daac500b55c543cd"
      }
    })
    headers = {
      'userID': userID,
      'ulcaApiKey': ulcaApiKey,
      'Content-Type': 'application/json'
    }
    response = requests.post(url, headers=headers, data=payload)

    config_translation = response.text
    config_translation_data = json.loads(config_translation)
    api_translation = config_translation_data['pipelineResponseConfig'][0]['config'][0]['serviceId']
    try:
        with open("bhashini_api.txt", "r") as f:
            existing_content = f.readlines()
    except FileNotFoundError:
        existing_content = []
    
    with open("bhashini_api.txt", "w") as f:
        if existing_content:
            f.writelines(existing_content)  
            f.write(api_translation + "\n") 
        else:
            f.write(api_translation + "\n") 
    
    return api_translation

# Function to call Bhashini API
def bhashini_api_call(task, target_lang, active_api, string):
    if task == "translation":
        api = active_api[0]
    else:
        api = active_api[1]
    # time.sleep(15)
    url = "https://dhruva-api.bhashini.gov.in/services/inference/pipeline"
    payload = json.dumps({
        "pipelineTasks": [
            {
                "taskType": task,
                "config": {
                    "serviceId": api,
                    "language": {
                        "sourceLanguage": "en",
                        "targetLanguage": target_lang
                    },
                    "isSentence": True
                },
                "controlConfig": {
                    "dataTracking": True
                }
            }
        ],
        "inputData": {
            "input": [
                {
                    "source": string
                }
            ]
        }
    })
    headers = {
        'Accept': '*/*',
        'Authorization': '9uAUqhCxaept0FGxeOUkyJ1XQSZtp9GWHy5XLriwyBsS-sovl9RkTe2Gkthwrx2F',
        'Content-Type': 'application/json'
    }
    time.sleep(20)
    response = requests.post(url, headers=headers, data=payload)
    
    translation_json = response.text
    print("||||||||||||||||||||||||||||||||||||||||||||||||| translated json")
    print(translation_json)
    # time.sleep(2)
    translated_data = json.loads(translation_json)

    if task == "translation":
        
        return translated_data['pipelineResponse'][0]['output'][0]['target']
        
    else:
        
        return translated_data['pipelineResponse'][0]['output'][0]['target'][0]
        

# Function to process a single row for API calls
def process_row(row, task, target_lang):
    index, data = row
    return bhashini_api_call(task, target_lang, active_api, data["en_value (current)"])

# Function to make parallel API calls
def parallel_api_calls(df, task, target_lang, max_workers=5):
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        # results = list(executor.map(lambda row: process_row(row, task, target_lang), df.iterrows()), total=len(df))
        results = list(executor.map(lambda row: process_row(row, task, target_lang), df.iterrows()))


    return results

# Function to merge approved and new labels for approval
def merge_labels_for_approval(approved_df, new_df):
    # added_new_labels = pd.concat([approved_df, new_df])
    # Reorder columns of new_df to match the sequence of columns in approved_df
    new_df_reordered = new_df.reindex(columns=approved_df.columns)

    # Concatenate the DataFrames
    # added_new_labels = pd.concat([approved_df, new_df_reordered])
    # Concatenate new_df_reordered below the last record of approved_df
    # added_new_labels = approved_df.append(new_df_reordered, ignore_index=True)
    added_new_labels = pd.concat([approved_df, new_df_reordered], ignore_index=True)
    print(added_new_labels)
    print(type(added_new_labels))
    # added_new_labels.reset_index(inplace=True, drop=True)
    return added_new_labels

# Function to get active API
def get_api(data):
    taskType = data.get('taskType')
    api = get_active_api(taskType)
    return {"active_api": api}
##########################################################
def retival(input_json, output_dict):
    new_json = {}

    # Iterate through the output dictionary
    for k, v in output_dict.items():
        output_keys = k.split(".")  # Split the output key by '.'
        output_keys=output_keys[1:]
        current_dict = new_json
        
        # Iterate through the split keys
        for i in range(len(output_keys)):
            key = output_keys[i]
            
            # If it's the last key, update the value in new_json
            if i == len(output_keys) - 1:
                current_dict[key] = v
            else:
                # Otherwise, traverse deeper into the nested dictionaries
                if key in current_dict:
                    current_dict = current_dict[key]
                else:
                    current_dict[key] = {}
                    current_dict = current_dict[key]
    return new_json
##########################################################################################################
# print(new_json)
def create_Json(u_in, dataframe, file, file_n):
    
    df2 = dataframe
    final_dict = {}
    l1 = []
    string1=""
    label_tagged_dict={}
    label_tagged_dict.update(parse_dict(file_n, string1, file))
    temp_dict = {}
    for k, v in label_tagged_dict.items():
        

        
        try:
            
            if k in df2["languagekey"].values:
                
                if len(df2.loc[df2["languagekey"] == k, f"{u_in}_value(curated)"].values[0]) != 0:
                    value_df = df2.loc[df2["languagekey"] == k, f"{u_in}_value(curated)"].values[0]
                elif len(df2.loc[df2["languagekey"] == k, f"{u_in}_value(curated)"].values[0]) == 0:
                    value_df = df2.loc[df2["languagekey"] == k, f"{u_in}_translated"].values[0]                
                            
            elif v == "NA":
                value_df = "NA"
            else:
                l1.append(v)
            # Assuming you want to continue even if no value is found
                continue

            temp_dict[k] = value_df
        except Exception as e:
            print(f"key is {k} and value is {v}")
            print(f"Error occurred: {e}")
            print(f"no value found for {k} : {v}")
        # final_dict[k]=temp_dict 
        
        print("****************************")    
        print(file_n)
        new_j=retival(file, temp_dict)
        try:

            if file_n.startswith("mobile"):
                with open(f"{output_json_path}/{file_n}_translated_output_{u_in}.json", 'w', encoding='utf-8') as json_file:
                    json.dump(new_j["mobileApp"], json_file, indent=2, ensure_ascii=False)
            else:
                with open(f"{output_json_path}/{file_n}_translated_output_{u_in}.json", 'w', encoding='utf-8') as json_file:
                    json.dump(new_j, json_file, indent=2, ensure_ascii=False)

        except:
            with open(f"{output_json_path}/{file_n}_translated_output_{u_in}", 'w', encoding='utf-8') as json_file:
                    json.dump(final_dict, new_j, indent=2, ensure_ascii=False)
    print(f"there are {len(set(l1))} unique labels added from {file_n}") 
    
    return None
##############################################################################################################