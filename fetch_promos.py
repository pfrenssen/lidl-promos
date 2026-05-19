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
                
                # Roadmap 1: Only include items that have percentage discount
                if discount and discount.get("percentageDiscount") is not None:
                    all_promotions.append({
                        'name': name,
                        'current_price': price_data.get('price'),
                        'old_price': price_data.get('oldPrice'),
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

    # Roadmap 2: Sort by highest discount first
    all_promotions.sort(key=lambda x: x['percentage'] if x['percentage'] is not None else 0, reverse=True)

    # Save the full sorted list to file
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(all_promotions, f, indent=2, ensure_ascii=False)
    
    print(f"Successfully saved {len(all_promotions)} promotions to {output_file}")
    
    # Roadmap 3: Output top 15
    print("\n--- Top 15 Promotions ---")
    for item in all_promotions[:15]:
        print(f"{item['name']}: {item['percentage']}%")

if __name__ == '__main__':
    fetch_promotions()
