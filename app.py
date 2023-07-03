import os
import json
import replicate
import requests
import dropbox
from replicate.exceptions import ModelError
from PIL import Image


dbx = dropbox.Dropbox('sl.Bhdy0j4eMFoGubYvBcQxQgs_Uq_Ki2EVPORStz6CX9AZZQa22jww0I-TOB2craf6qumHgKuFwyUM8Ey8m1_TMk2P1wh7kltnvHIZPoa7lciWQ0k8xzSlSQdOwgQYMV5LsBhNH4Bt')


def get_files_in_folder(folder_path):
    try:
        files = dbx.files_list_folder(folder_path).entries
        return [file.path_lower for file in files if isinstance(file, dropbox.files.FileMetadata)]
    except dropbox.exceptions.ApiError as err:
        print('Dropbox API error:', err)
        return []


def get_direct_link(dbx, file_path):
    try:
        shared_link_metadata = dbx.sharing_create_shared_link_with_settings(file_path)
        url = shared_link_metadata.url
    except dropbox.exceptions.ApiError as err:
        if err.error.is_shared_link_already_exists():
            shared_links = dbx.sharing_list_shared_links(file_path).links
            if shared_links:
                url = shared_links[0].url  # Get the URL of the first shared link
            else:
                print(f"Error: no shared links found for {file_path}")
                return None
        else:
            print('Dropbox API error:', err)
            return None
    # Replace www.dropbox.com with dl.dropboxusercontent.com
    direct_link = url.replace("www.dropbox.com", "dl.dropboxusercontent.com").replace("?dl=0", "?dl=1")
    return direct_link



def run_model_on_image(image_url, retries=3):
    for _ in range(retries):
        try:
            output = replicate.run(
                "salesforce/blip:2e1dddc8621f72155f24cf2e0adbde548458d3cab9f00c0139eea840d0ac4746",
                input={"image": image_url}
            )
            # Assuming the output is a string of the form "Caption: xyz", split on the colon and strip any leading/trailing whitespace
            if output is not None:
                caption = output.split(":", 1)[1].strip()
                return caption
        except ModelError as e:
            print(f"ModelError occurred for {image_url}. Retrying...")

    print(f"Failed to process {image_url} after {retries} retries.")
    return None


def translate_text_deepl(text, target='PL'):  # Set target language to Polish
    deepl_api_url = 'https://api-free.deepl.com/v2/translate'
    api_key = os.environ.get('DEEPL_API_KEY')  # Store your API key as an environment variable

    headers = {
        "Content-Type": "application/x-www-form-urlencoded"
    }
    data = {
        "auth_key": api_key,
        "text": text,
        "target_lang": target,
    }
    response = requests.post(deepl_api_url, data=data, headers=headers)
    response_json = response.json()

    # The translations field contains an array with translations.
    # For a single input text, it should contain a single translation.
    translated_text = response_json['translations'][0]['text']
    return translated_text.lower()  # Convert translated text to lowercase


def send_to_airtable(caption, translated_caption, image_path):
    airtable_api_url = "https://api.airtable.com/v0/appqLmpIBtfifD9Ob/table" #Use your own airtable API URL
    api_key = os.environ.get('AIRTABLE_API_KEY')  # Store your API key as an environment variable
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    # Format your data as required by Airtable
    payload = {
        "fields": {
            "ENG": caption,
            "PL": translated_caption,  # Replace "Translated Notes" with your actual column name
            "Attachments": [
                {
                    "url": image_url
                }
            ]
        }
    }
    response = requests.post(airtable_api_url, json=payload, headers=headers)

    # Print status code and response content for troubleshooting
    print("Status Code:", response.status_code)
    print("Response Content:", response.content)


folder_path = '/Images'  # The path to your Dropbox folder
file_paths = get_files_in_folder(folder_path)

outputs = []
for file_path in file_paths:
    print("Processing file:", file_path)  # Print which image is currently being processed
    image_url = get_direct_link(dbx, file_path)
    if image_url is not None:
        print("Running model on image")
        caption = run_model_on_image(image_url)
        if caption is not None:
            translated_caption = translate_text_deepl(caption, target='PL')
            outputs.append((caption, translated_caption))
            print("Model output:", caption)
            print("Translated output:", translated_caption)
            print("Sending data to Airtable")
            send_to_airtable(caption, translated_caption, image_url)
        else:
            print(f"Could not extract a caption from output for {file_path}")
