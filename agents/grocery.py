def find_missing_items(inventory_result):

    return {
        "missing_items": inventory_result.get("missing", []),
        "status": "identified"
    }


def estimate_grocery_cost(missing_items):

    demo_prices = {
        "roti": 40,
        "curd": 50,
        "lemon": 10,
        "coriander": 20,
        "cheese": 100,
        "bread": 40,
        "milk": 35
    }

    total = 0

    for item in missing_items:
        total += demo_prices.get(item.lower(), 50)

    return {
        "estimated_cost": total,
        "currency": "INR"
    }