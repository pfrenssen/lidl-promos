import json
import os
import time
from typing import Any, Dict, List

import requests

BASE_URL = "https://www.lidl.bg/q/api/search"
DEFAULT_PARAMS = {
    "offset": 0,
    "fetchsize": 100,
    "locale": "bg_BG",
    "assortment": "BG",
    "version": "2.1.0",
    "category.id": "10068374",
}


def _extract_promotions(items: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    promotions: List[Dict[str, Any]] = []
    for item in items:
        data_box = item.get("gridbox", {}).get("data", {})
        price_data = data_box.get("price", {})
        discount = price_data.get("discount") or {}
        percentage = discount.get("percentageDiscount")

        # Only include items with numeric percentage discounts.
        if percentage is None:
            continue

        promotions.append(
            {
                "name": data_box.get("title", "Unknown"),
                "current_price": price_data.get("price"),
                "old_price": price_data.get("oldPrice"),
                "discount_text": discount.get("discountText"),
                "percentage": percentage,
            }
        )
    return promotions


def fetch_promos(output_file: str = "promotions.json") -> List[Dict[str, Any]]:
    params = dict(DEFAULT_PARAMS)
    all_promotions: List[Dict[str, Any]] = []
    offset = 0

    print("Fetching promotions from Lidl...")
    with requests.Session() as session:
        while True:
            params["offset"] = offset
            try:
                response = session.get(BASE_URL, params=params, timeout=15)
                response.raise_for_status()
                data = response.json()
            except requests.RequestException as exc:
                print(f"Request failed at offset {offset}: {exc}")
                break
            except ValueError as exc:
                print(f"Invalid JSON at offset {offset}: {exc}")
                break

            items = data.get("items", [])
            if not items:
                break

            all_promotions.extend(_extract_promotions(items))

            if len(items) < params["fetchsize"]:
                break

            offset += params["fetchsize"]
            time.sleep(0.5)

    all_promotions.sort(
        key=lambda entry: entry.get("percentage") or 0, reverse=True
    )

    output_dir = os.path.dirname(output_file)
    if output_dir:
        os.makedirs(output_dir, exist_ok=True)

    with open(output_file, "w", encoding="utf-8") as handle:
        json.dump(all_promotions, handle, indent=2, ensure_ascii=False)

    print(f"Successfully saved {len(all_promotions)} promotions to {output_file}")

    print("\n--- Top 15 Promotions ---")
    for item in all_promotions[:15]:
        print(f"{item['name']}: {item['percentage']}%")

    return all_promotions


if __name__ == "__main__":
    fetch_promos()
