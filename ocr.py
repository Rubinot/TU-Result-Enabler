# ocr_lightweight.py
import requests
import json

def online_ocr(image_path, api_key='K88919177488957'):
    """Pure Python OCR without PIL dependency"""
    url = "https://api.ocr.space/parse/image"
    
    with open(image_path, 'rb') as f:
        response = requests.post(
            url,
            files={"image": f},
            data={
                "apikey": api_key,
                "language": "eng",
                "isTable": "true",
                "OCREngine": "2"
            }
        )
    
    if response.status_code == 200:
        return response.json()["ParsedResults"][0]["ParsedText"]
    raise Exception(f"OCR failed: {response.text}")

print(online_ocr("final_result.png"))
