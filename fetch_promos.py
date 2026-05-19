import json
import os
import time
import re
from datetime import datetime
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
        meta_box = item.get("gridbox", {}).get("meta", {})
        price_data = data_box.get("price", {})
        discount = price_data.get("discount") or {}
        percentage = discount.get("percentageDiscount")

        # Check for Lidl Plus promotions
        lidl_plus = data_box.get("lidlPlus")
        if lidl_plus:
            lidl_plus_price = lidl_plus[0].get("price", {})
            current_price = lidl_plus_price.get("price")
            old_price = lidl_plus_price.get("oldPrice")

            # Calculate percentage for Lidl Plus items
            if current_price and old_price and old_price > 0:
                percentage = round((1 - current_price / old_price) * 100)
            else:
                percentage = None

            discount_text = discount.get("discountText") or "Lidl Plus"
        else:
            # Standard promotions
            current_price = price_data.get("price")
            old_price = price_data.get("oldPrice")
            discount_text = discount.get("discountText")

            # Attempt to derive percentage from discount_text (e.g., "-20%" or "20%")
            if percentage is None and discount_text:
                match = re.search(r"^-?(\d+)%", discount_text)
                if match:
                    percentage = int(match.group(1))

        # Only include items with numeric percentage discounts.
        if percentage is None:
            continue

        # Extract dates from stockAvailability
        badge_info = data_box.get("stockAvailability", {}).get("badgeInfoV2", [])
        start_date = None
        end_date = None
        if badge_info:
            first_badge = badge_info[0]
            start_date = first_badge.get("validFrom")
            end_date = first_badge.get("validUntil")

        # Exclude promotions not valid today
        now = time.time()
        if start_date and end_date:
            if not (start_date <= now <= end_date):
                continue

        # Extract category if available. The path is
        # gridbox.meta.wonCategoryBreadcrumbs[0][1].name
        category = None
        try:
            breadcrumbs = meta_box.get("wonCategoryBreadcrumbs", [])
            if breadcrumbs and isinstance(breadcrumbs, list):
                first = breadcrumbs[0]
                if isinstance(first, list) and len(first) > 1:
                    cat_dict = first[1]
                    if isinstance(cat_dict, dict):
                        category = cat_dict.get("name")
        except Exception:
            category = None

        # Exclude unwanted categories
        exclude_categories = {
            "За домашни любимци",
            "Вино и алкохол",
            "Козметика и грижа за тялото",
            "Снаксове и сладки изкушения",
        }
        if category in exclude_categories:
            continue

        promotions.append(
            {
                "name": data_box.get("title", "Unknown"),
                "current_price": current_price,
                "old_price": old_price,
                "discount_text": discount_text,
                "percentage": percentage,
                "url": data_box.get("canonicalUrl"),
                "is_lidl_plus": bool(lidl_plus),
                "start_date": start_date,
                "end_date": end_date,
                "category": category,
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

    all_promotions.sort(key=lambda entry: entry.get("percentage") or 0, reverse=True)

    output_dir = os.path.dirname(output_file)
    if output_dir:
        os.makedirs(output_dir, exist_ok=True)

    with open(output_file, "w", encoding="utf-8") as handle:
        json.dump(all_promotions, handle, indent=2, ensure_ascii=False)

    print(f"Successfully saved {len(all_promotions)} promotions to {output_file}")

    print("\n--- Top 25 Promotions ---")
    for item in all_promotions[:25]:
        start = (
            datetime.fromtimestamp(item["start_date"]).strftime("%d/%m")
            if item.get("start_date")
            else "??/??"
        )
        end = (
            datetime.fromtimestamp(item["end_date"]).strftime("%d/%m")
            if item.get("end_date")
            else "??/??"
        )

        # Ensure full URL
        full_url = (
            f"https://www.lidl.bg{item['url']}"
            if item["url"] and not item["url"].startswith("http")
            else item["url"]
        )

        print(
            f"[{item['name']}]({full_url}): {item['current_price']}€ ({item['percentage']}% off) - {start}-{end}"
        )

    return all_promotions


if __name__ == "__main__":
    fetch_promos()
