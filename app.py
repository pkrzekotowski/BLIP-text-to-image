import os
import json
import replicate
import requests
from replicate.exceptions import ModelError


def run_model_on_image(image_path, retries=3):
    for _ in range(retries):
        try:
            with open(image_path, "rb") as image_file:
                output = replicate.run(
                    "salesforce/blip:2e1dddc8621f72155f24cf2e0adbde548458d3cab9f00c0139eea840d0ac4746",
                    input={"image": image_file}
                )
            return output
        except ModelError as e:
            print(f"ModelError occurred for {image_path}. Retrying...")

    print(f"Failed to process {image_path} after {retries} retries.")
    return None


def send_to_airtable(data):
    airtable_api_url = "https://api.airtable.com/v0/appqLmpIBtfifD9Ob/table" #Use your own airtable API URL
    api_key = os.environ.get('AIRTABLE_API_KEY')  # Store your API key as an environment variable
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    # Format your data as required by Airtable
    payload = {
        "fields": {
            "Notes": json.dumps(data)
        }
    }
    response = requests.post(airtable_api_url, json=payload, headers=headers)

    # Print status code and response content for troubleshooting
    print("Status Code:", response.status_code)
    print("Response Content:", response.content)


# Directory where your images are stored (relative to the script)
image_directory = os.path.join(os.path.dirname(__file__), "Images") # Remember to set your own path

# Get a list of all image paths in the directory
image_paths = [os.path.join(image_directory, image) for image in os.listdir(image_directory) if image.endswith(('.png', '.jpg', '.jpeg'))]

print("Image paths:", image_paths)  # Let's print out the image paths to make sure they are being read

outputs = []
for image_path in image_paths:
    print("Processing image:", image_path)  # Print which image is currently being processed
    output = run_model_on_image(image_path)
    outputs.append(output)
    print("Model output:", output)  # Print the output from the model
    print("Sending data to Airtable")
    send_to_airtable(output)
