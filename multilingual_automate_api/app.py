# from flask import Flask, request, jsonify
import numpy as np
import time
from functions import *
from config import languages



global refined_df, file

def process_data_route():
    json_files=fetch_github_json_names()
    print(json_files)
    
    for file in json_files: 
        current_json=fetch_github_json(file)
        print("##############")
        print(current_json)
                  
        
        if current_json:
            result_df=create_dataframe_from_json(file, current_json)
            print("##############")
            print(result_df)
            df=read_google_sheet()
            print("@@@@@@@@@@@@@@@@@@@@@@@@")
            print(df.columns)
            print("PPPPPPPPPPPPPPPPPPP")
            print(result_df.columns)
            for i in result_df["languagekey"]:
                if i in df["languagekey"].values and result_df.at[result_df[result_df["languagekey"]==i].index[0], "en_value (current)"].strip() != df[df["languagekey"]==i].iloc[0]["en_value (current)"]:
                    df.drop(df[df["languagekey"]==i].index, inplace=True)
            refined_df = result_df[~result_df["languagekey"].isin(df["languagekey"])]
            print(refined_df)
            # refined_df.to_excel("refined_df.xlsx")
            ##
            
            if not refined_df.empty:       
                print("inside first if statement")              
                for lang in languages:
                    print("inside for loop") 
                    # time.sleep(30)
                    refined_df[f"{lang}_translated"] = parallel_api_calls(refined_df, "translation", f"{lang}", max_workers=128)         ##max_threads
                    time.sleep(2)
                    refined_df[f"{lang}_transliterated"] = parallel_api_calls(refined_df, "transliteration", f"{lang}", max_workers=128)
                    # time.sleep(2) 
                    # refined_df[f"{lang}_curated"]=refined_df.fillna('')       ###np.nan not valid in google spread
                    refined_df[f"{lang}_value(curated)"]=""

                # refined_df.reset_index(inplace=True, drop=True)
                merged_df = merge_labels_for_approval(df, refined_df)
                print(merged_df.columns)
                # merged_df=merged_df.groupby("en_value (current)").first().reset_index()
                merged_df = merged_df.drop_duplicates(subset="languagekey").reset_index(drop=True).drop(columns=["Column1"])
                print("/////////////////////////////////")
                print(merged_df.columns)
                merged_df.to_excel("previously updated_df.xlsx")
                update_google_sheet(merged_df)

            else:
                print("no new data")
            df2=read_google_sheet()
            for language in languages:
                print(file)
                print("****************************")    
                print(file)
                create_Json(language, df2, current_json, file)
            
        else:
            print("Json is not loaded")
        refined_df=[]

    return "Process completed"
process_data_route()
# if __name__ == '__main__':
#     app.run(debug=True, port=9814)
