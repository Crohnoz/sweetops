import requests

URL = "https://isiscakes.ola.click/products"

headers = {
    "User-Agent": "Mozilla/5.0"
}

response = requests.get(URL, headers=headers, timeout=20)

print("Status:", response.status_code)
print("URL final:", response.url)
print("Largo HTML:", len(response.text))

with open("olaclick_raw.html", "w", encoding="utf-8") as file:
    file.write(response.text)

print("HTML guardado en olaclick_raw.html")