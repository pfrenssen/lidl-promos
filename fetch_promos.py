import json
import requests
import time
import os

def fetch_promotions(output_file='promotions.json'):
    base_url = "https://www.lidl.bg/q/api/search"
    params = {
        "offset": 0,
        "fetchsize": 100,
        "locale": "bg_BG",
        "assortment": "BG",
        "version": "2.1.0",
        "category.id": "10068374"
    }

    all_promotions = []
    offset = 0

    print("Fetching promotions from Lidl...")
    while True:
        params['offset'] = offset
        try:
            response = requests.get(base_url, params=params, timeout=10)
            if response.status_code != 200:
                print(f"Failed to fetch data at offset {offset}. Status code: {response.status_code}")
                break
            
            data = response.json()
            items = data.get('items', [])
            
            if not items:
                break
                
            for item in items:
                gridbox = item.get('gridbox', {})
                data_box = gridbox.get('data', {})
                name = data_box.get('title', 'Unknown')
                price_data = data_box.get('price', {})
                discount = price_data.get('discount')
                
                # Extract price information
                current_price = price_data.get('price')
                old_price = price_data.get('oldPrice')
                
                # Only include items that have discount info
                if discount:
                    all_promotions.append({
                        'name': name,
                        'current_price': current_price,
                        'old_price': old_price,
                        'discount_text': discount.get('discountText'),
                        'percentage': discount.get('percentageDiscount')
                    })
            
            if len(items) < 100:
                break
                
            offset += 100
            time.sleep(0.5) 
            
        except Exception as e:
            print(f"Error: {e}")
            break

    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(all_promotions, f, indent=2, ensure_ascii=False)
    
    print(f"Successfully saved {len(all_promotions)} promotions to {output_file}")

if __name__ == '__main__':
    fetch_promotions()
