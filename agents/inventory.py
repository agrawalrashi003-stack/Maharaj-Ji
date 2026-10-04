# =========================================================
# MAHARAJ JI
# SQLite Inventory Module
# =========================================================

from database import (
    get_inventory as db_get_inventory,
    add_inventory_item,
)


# =========================================================
# GET INVENTORY
# =========================================================

def get_inventory(user_id=1):
    """
    Load the user's current household inventory
    from SQLite.
    """

    rows = db_get_inventory(user_id)

    inventory = {}

    for item in rows:

        ingredient = item["ingredient"].lower().strip()

        inventory[ingredient] = {
            "quantity": item["quantity"],
            "unit": item["unit"]
        }

    return inventory


# =========================================================
# CHECK INVENTORY
# =========================================================

def check_inventory(
    required_ingredients,
    user_id=1
):
    """
    Check which required ingredients are currently
    available in the user's SQLite inventory.
    """

    inventory = get_inventory(user_id)

    available = []
    missing = []

    for ingredient in required_ingredients:

        # -------------------------------------------------
        # Support both formats:
        #
        # "paneer"
        #
        # OR
        #
        # {
        #     "ingredient": "paneer",
        #     "quantity": 200,
        #     "unit": "g"
        # }
        # -------------------------------------------------

        if isinstance(ingredient, dict):

            ingredient_name = ingredient.get(
                "ingredient",
                ""
            ).lower().strip()

        else:

            ingredient_name = str(
                ingredient
            ).lower().strip()


        # -------------------------------------------------
        # Check SQLite inventory
        # -------------------------------------------------

        if ingredient_name in inventory:

            item = inventory[
                ingredient_name
            ]

            if item.get(
                "quantity",
                0
            ) > 0:

                available.append({

                    "ingredient":
                        ingredient_name,

                    "quantity":
                        item["quantity"],

                    "unit":
                        item["unit"]

                })

            else:

                missing.append(
                    ingredient_name
                )

        else:

            missing.append(
                ingredient_name
            )


    # -----------------------------------------------------
    # Return inventory comparison
    # -----------------------------------------------------

    return {

        "available": available,

        "missing": missing

    }


# =========================================================
# CONSUME INVENTORY
# =========================================================

def consume_inventory(
    used_ingredients,
    user_id=1
):
    """
    Reduce inventory quantities in SQLite
    after a meal has been prepared.
    """

    current_inventory = get_inventory(
        user_id
    )


    for ingredient in used_ingredients:

        name = ingredient[
            "ingredient"
        ].lower().strip()

        quantity_used = ingredient.get(
            "quantity",
            0
        )


        # -------------------------------------------------
        # Only consume if ingredient exists
        # -------------------------------------------------

        if name not in current_inventory:

            continue


        current_quantity = current_inventory[
            name
        ]["quantity"]


        new_quantity = max(
            0,
            current_quantity - quantity_used
        )


        # -------------------------------------------------
        # Update SQLite
        #
        # add_inventory_item() performs an
        # insert/update automatically.
        # -------------------------------------------------

        add_inventory_item(

            user_id=user_id,

            ingredient=name,

            quantity=new_quantity,

            unit=current_inventory[
                name
            ]["unit"]

        )


        # Keep local state updated as well
        current_inventory[
            name
        ]["quantity"] = new_quantity


    return current_inventory


# =========================================================
# DATABASE INVENTORY SETUP
# =========================================================

def setup_demo_inventory(user_id=1):
    """
    Add the existing demo inventory into SQLite.

    This is a one-time migration helper so that the
    inventory that previously lived in inventory.json
    is available in the SQLite database.
    """

    demo_inventory = {

        "paneer": {
            "quantity": 250,
            "unit": "g"
        },

        "onion": {
            "quantity": 3,
            "unit": "pieces"
        },

        "tomato": {
            "quantity": 4,
            "unit": "pieces"
        },

        "capsicum": {
            "quantity": 2,
            "unit": "pieces"
        },

        "potato": {
            "quantity": 4,
            "unit": "pieces"
        },

        "green_chilli": {
            "quantity": 5,
            "unit": "pieces"
        },

        "ginger": {
            "quantity": 1,
            "unit": "piece"
        },

        "garlic": {
            "quantity": 1,
            "unit": "piece"
        },

        "oil": {
            "quantity": 500,
            "unit": "ml"
        },

        "salt": {
            "quantity": 500,
            "unit": "g"
        },

        "turmeric": {
            "quantity": 100,
            "unit": "g"
        },

        "red_chilli_powder": {
            "quantity": 100,
            "unit": "g"
        },

        "cumin": {
            "quantity": 100,
            "unit": "g"
        },

        "garam_masala": {
            "quantity": 100,
            "unit": "g"
        },

        "rice": {
            "quantity": 1000,
            "unit": "g"
        },

        "atta": {
            "quantity": 1000,
            "unit": "g"
        }

    }


    for ingredient, item in demo_inventory.items():

        add_inventory_item(

            user_id=user_id,

            ingredient=ingredient,

            quantity=item["quantity"],

            unit=item["unit"]

        )


# =========================================================
# TEST
# =========================================================

if __name__ == "__main__":

    print(
        "\nSetting up demo inventory..."
    )

    setup_demo_inventory()


    print(
        "\nSQLite Inventory:"
    )

    print(
        get_inventory()
    )


    print(
        "\nChecking inventory for:"
    )

    test_ingredients = [

        "paneer",
        "onion",
        "rice",
        "chicken"

    ]

    result = check_inventory(
        test_ingredients
    )


    print(
        result
    )