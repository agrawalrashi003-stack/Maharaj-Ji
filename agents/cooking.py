def cooking_option(willingness):

    if not willingness:
        return {
            "option": "self_cook"
        }

    willingness = willingness.lower()

    if "no" in willingness or "low" in willingness:
        return {
            "option": "cook_service",
            "status": "available",
            "message": "A cooking service can be arranged."
        }

    return {
        "option": "self_cook",
        "status": "selected",
        "message": "User can cook the meal themselves."
    }


def get_cooking_guidance(meal_name):

    return {
        "meal": meal_name,
        "message": f"Cooking guidance for {meal_name} is ready."
    }