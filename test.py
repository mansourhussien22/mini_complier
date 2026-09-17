import requests

url = "http://127.0.0.1:8000/compile"
payload = {
    "source_code": """
    int x = 5;
    int y = x + 3;
    print(y);
    """
}

response = requests.post(url, json=payload)
print(response.json())