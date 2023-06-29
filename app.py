import os
import replicate

def run_model_on_image(image_path):
    with open(image_path, "rb") as image_file:
        output = replicate.run(
            "salesforce/blip:2e1dddc8621f72155f24cf2e0adbde548458d3cab9f00c0139eea840d0ac4746",
            input={"image": image_file}
        )
    return output

#Directory where your images are stored (relative to the script)
image_directory = os.path.join(os.path.dirname(__file__), "Images")

# Get a list of all image paths in the directory
image_paths = [os.path.join(image_directory, image) for image in os.listdir(image_directory) if image.endswith(('.png', '.jpg', '.jpeg'))]

outputs = []
for image_path in image_paths:
    output = run_model_on_image(image_path)
    outputs.append(output)
    print(output)
