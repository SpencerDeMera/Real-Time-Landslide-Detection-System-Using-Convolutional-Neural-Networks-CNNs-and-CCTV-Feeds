import requests

url = "http://localhost:8000/predict/"
landslide_1_path = "./landslide/brightened_0be1aa38-e8f0-4e7a-89f9-4b5b631dc655.jpg"
normal_1_path = "./standard/00cc970c-a345-4766-bcaf-ead955310cb7.jpg"
normal_2_path = "./standard/00cdcf4d-3d76-400f-8752-09ff7e4a9368.jpg"
normal_3_path = "./standard/00e515e2-0602-4bbb-ab29-fe9d8661043c.jpg"

imagesToTest = [normal_1_path, landslide_1_path, normal_2_path, normal_3_path]

for imagePath in imagesToTest:
    with open(imagePath, "rb") as img:
        files = {"file": img}
        response = requests.post(url, files=files)

    actual = None
    if "/standard/" in imagePath:
        actual = "0"
    elif "/landslide/" in imagePath:
        actual = "1"

    # Predictions:
    # 0 == standard / anomaly-free
    # 1 == has landslide / anomaly
    print(f"Response: {response.json()}, Actual: {actual}")
