from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
import requests
import os
from dotenv import load_dotenv

load_dotenv()

app = FastAPI()
templates = Jinja2Templates(directory="templates")

API_KEY = os.getenv("BESTBUY_API_KEY")  # Add this in Render Dashboard

@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.get("/check")
def check_bestbuy(sku: str, zip_code: str = None, radius: int = 50):
    if not API_KEY:
        return {"error": "Best Buy API key not configured"}
    
    if not sku:
        return {"error": "Provide SKU"}
    
    # Best Buy Stores + Products combined query for in-store availability
    url = "https://api.bestbuy.com/v1/stores"
    
    params = {
        "format": "json",
        "apiKey": API_KEY,
        "pageSize": 25,
        "show": "storeId,storeType,city,region,name,postalCode,products.name,products.sku,products.inStoreAvailability,products.inStorePickup"
    }
    
    if zip_code:
        params["area"] = f"{zip_code},{radius}mi"  # or use lat/long if you prefer
    
    # Filter to specific SKU
    url += f"(area({zip_code},{radius}mi))+products(sku={sku})"
    
    try:
        resp = requests.get(url, params=params, timeout=15)
        data = resp.json()
        
        stores_with_stock = []
        if "stores" in data:
            for store in data["stores"]:
                for product in store.get("products", []):
                    if str(product.get("sku")) == sku:
                        stores_with_stock.append({
                            "store": store.get("name"),
                            "city": store.get("city"),
                            "stock": product.get("inStoreAvailability", False),
                            "pickup": product.get("inStorePickup", False)
                        })
        
        return {
            "sku": sku,
            "zip": zip_code,
            "stores_found": len(stores_with_stock),
            "results": stores_with_stock
        }
    except Exception as e:
        return {"error": str(e)}