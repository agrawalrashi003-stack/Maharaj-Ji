# =========================================================
# MAHARAJ JI
# Personal Context Module
# SQLite Connected Version
# =========================================================

from database import (
    get_user,
    get_inventory as db_get_inventory
)


# =========================================================
# GET USER PROFILE
# =========================================================

def get_user_profile(
    user_id=1
):
    """
    Load the user's persistent food profile
    from SQLite.
    """

    user = get_user(
        user_id
    )

    if user is None:

        return {}

    return {

        "name": user.get(
            "name"
        ),

        "diet": user.get(
            "diet"
        ),

        "spice_level": user.get(
            "spice_level"
        ),

        "typical_budget": user.get(
            "typical_budget"
        ),

        "preferred_cooking_time": user.get(
            "preferred_cooking_time"
        ),

        "cooking_preference": user.get(
            "cooking_preference"
        ),

        "household_size": user.get(
            "household_size"
        )

    }


# =========================================================
# GET INVENTORY
# =========================================================

def get_inventory(
    user_id=1
):
    """
    Load the user's current household inventory
    from SQLite.
    """

    rows = db_get_inventory(
        user_id
    )

    inventory = {}

    for item in rows:

        ingredient = item[
            "ingredient"
        ].lower().strip()

        inventory[ingredient] = {

            "quantity":
                item["quantity"],

            "unit":
                item["unit"]

        }

    return inventory


# =========================================================
# GET PERSONAL CONTEXT
# =========================================================

def get_personal_context(
    user_id=1
):
    """
    Load all persistent information Maharaj Ji
    should know about the user.

    The data now comes from SQLite instead
    of JSON files.
    """

    return {

        "user_profile":
            get_user_profile(
                user_id
            ),

        "inventory":
            get_inventory(
                user_id
            )

    }


# =========================================================
# TEST
# =========================================================

if __name__ == "__main__":

    print(
        "\n========================================"
    )

    print(
        "MAHARAJ JI PERSONAL CONTEXT TEST"
    )

    print(
        "========================================"
    )


    print(
        "\nUser Profile:"
    )

    print(
        get_user_profile()
    )


    print(
        "\nInventory:"
    )

    print(
        get_inventory()
    )


    print(
        "\nComplete Personal Context:"
    )

    print(
        get_personal_context()
    )