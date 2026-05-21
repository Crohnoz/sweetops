import requests
import json

URL = "https://api.olaclick.app/ms-products/public/companies/13610cf0-3bed-11ec-ba95-bba0d5df8115/categories"

response = requests.get(URL, timeout=30)
response.raise_for_status()

payload = response.json()
categories = payload.get("data", [])

with open("olaclick_products.json", "w", encoding="utf-8") as file:
    json.dump(payload, file, ensure_ascii=False, indent=2)

print("Archivo guardado: olaclick_products.json")
print("Categorías encontradas:", len(categories))

total_products = 0

for category in categories:
    products = category.get("products", [])
    total_products += len(products)

    print("\nCATEGORÍA:", category.get("name"))
    print("Productos:", len(products))

    for product in products:
        variants = product.get("product_variants", [])
        price = variants[0].get("price") if variants else 0
        stock = variants[0].get("stock") if variants else 0

        print(f"- {product.get('name')} | ${price} | stock API: {stock}")

print("\nTotal productos:", total_products)