import json
import re
from pathlib import Path


# =====================================================
# MAHARAJ JI
# UC1 — DAILY MEAL DECISION
#
# IMPORTANT:
# This file does NOT call Gemini.
#
# It uses:
# - persistent user profile
# - current inventory
# - conversation state
# - current user message
# - recipe data
#
# Therefore it does NOT consume Gemini API quota.
# =====================================================


RECIPES_FILE = Path("data/recipes.json")


# =====================================================
# LOAD RECIPES
# =====================================================

def load_recipes():

    if not RECIPES_FILE.exists():
        return []

    try:

        with open(
            RECIPES_FILE,
            "r",
            encoding="utf-8"
        ) as file:

            return json.load(file)

    except Exception as error:

        print(
            "RECIPE LOAD ERROR:",
            error
        )

        return []


# =====================================================
# NORMALIZE TEXT
# =====================================================

def normalize_text(text):

    if not text:
        return ""

    text = text.lower()

    text = re.sub(
        r"[^a-z0-9\s]",
        " ",
        text
    )

    text = re.sub(
        r"\s+",
        " ",
        text
    )

    return text.strip()


# =====================================================
# KEYWORD HELPER
# =====================================================

def contains_any(text, keywords):

    return any(
        keyword in text
        for keyword in keywords
    )


# =====================================================
# DETECT MEAL TYPE
# =====================================================

def detect_meal_type(text):

    if contains_any(
        text,
        [
            "breakfast",
            "morning",
            "nashta",
            "nasta"
        ]
    ):
        return "breakfast"

    if contains_any(
        text,
        [
            "lunch",
            "dopahar"
        ]
    ):
        return "lunch"

    if contains_any(
        text,
        [
            "dinner",
            "raat",
            "night"
        ]
    ):
        return "dinner"

    return None


# =====================================================
# DETECT MOOD
# =====================================================

def detect_mood(text):

    if contains_any(
        text,
        [
            "tired",
            "thak",
            "exhausted",
            "lazy",
            "thak gaya",
            "thak gayi"
        ]
    ):
        return "tired"

    if contains_any(
        text,
        [
            "busy",
            "jaldi",
            "quick",
            "fast",
            "hurry",
            "time nahi"
        ]
    ):
        return "busy"

    if contains_any(
        text,
        [
            "special",
            "fancy",
            "something special"
        ]
    ):
        return "special"

    return None


# =====================================================
# DETECT CRAVINGS
# =====================================================

def detect_cravings(text):

    cravings = []

    if contains_any(
        text,
        [
            "spicy",
            "teekha",
            "masaledar"
        ]
    ):
        cravings.append("spicy")

    if contains_any(
        text,
        [
            "light",
            "halka"
        ]
    ):
        cravings.append("light")

    if contains_any(
        text,
        [
            "rice",
            "chawal"
        ]
    ):
        cravings.append("rice")

    if "paneer" in text:
        cravings.append("paneer")

    if "comfort food" in text:
        cravings.append("comfort")

    return cravings


# =====================================================
# DETECT COOKING PREFERENCE
# =====================================================

def detect_cooking_preference(text):

    if contains_any(
        text,
        [
            "dont want to cook",
            "do not want to cook",
            "don't want to cook",
            "not cook",
            "can't cook",
            "cannot cook",
            "cook nahi karna",
            "banana nahi hai"
        ]
    ):
        return "do_not_want_to_cook"

    if contains_any(
        text,
        [
            "want to cook",
            "i will cook",
            "i can cook",
            "khud banaungi",
            "khud banaunga"
        ]
    ):
        return "cook_at_home"

    return None


# =====================================================
# DETECT INGREDIENTS MENTIONED BY USER
# =====================================================

def detect_ingredients(
    text,
    inventory
):

    detected = []

    for ingredient in inventory.keys():

        normalized_ingredient = normalize_text(
            ingredient
        )

        if normalized_ingredient in text:

            detected.append(
                ingredient
            )

    return detected


# =====================================================
# DETECT REJECTION / CHANGE
# =====================================================

def detect_rejected_items(
    text,
    current_meal
):

    if not current_meal:
        return []

    rejected = []

    meal_name = normalize_text(
        current_meal.get(
            "name",
            ""
        )
    )

    rejection_phrases = [
        "dont want",
        "do not want",
        "don't want",
        "nahi chahiye",
        "nahi banana",
        "not this",
        "something else",
        "another",
        "change it"
    ]

    if contains_any(
        text,
        rejection_phrases
    ):

        if meal_name:
            rejected.append(
                meal_name
            )

    for ingredient in current_meal.get(
        "ingredients",
        []
    ):

        ingredient_text = normalize_text(
            ingredient
        )

        if (
            ingredient_text in text
            and
            contains_any(
                text,
                [
                    "dont want",
                    "do not want",
                    "don't want",
                    "nahi",
                    "avoid"
                ]
            )
        ):

            rejected.append(
                ingredient_text
            )

    return rejected


# =====================================================
# CHECK RECIPE AVAILABILITY
# =====================================================

def recipe_available(
    recipe,
    inventory
):

    missing = []

    for ingredient in recipe.get(
        "ingredients",
        []
    ):

        if ingredient not in inventory:

            missing.append(
                ingredient
            )

            continue

        quantity = inventory[
            ingredient
        ].get(
            "quantity",
            0
        )

        if quantity <= 0:

            missing.append(
                ingredient
            )

    return missing


# =====================================================
# SCORE RECIPE
# =====================================================

def score_recipe(
    recipe,
    profile,
    inventory,
    user_text,
    rejected_items
):

    score = 0

    text = normalize_text(
        user_text
    )

    recipe_name = normalize_text(
        recipe.get(
            "name",
            ""
        )
    )


    # -------------------------------------------------
    # REJECTED MEAL
    # -------------------------------------------------

    if recipe_name in rejected_items:

        return -999


    # -------------------------------------------------
    # PROFILE
    # -------------------------------------------------

    food_preferences = profile.get(
        "food_preferences",
        {}
    )

    likes = food_preferences.get(
        "likes",
        []
    )

    dislikes = food_preferences.get(
        "dislikes",
        []
    )


    # -------------------------------------------------
    # LIKES
    # -------------------------------------------------

    for like in likes:

        like_text = normalize_text(
            like
        )

        if (
            like_text in recipe_name
            or
            any(
                like_text in normalize_text(
                    ingredient
                )
                for ingredient in recipe.get(
                    "ingredients",
                    []
                )
            )
        ):

            score += 5


    # -------------------------------------------------
    # DISLIKES
    # -------------------------------------------------

    for dislike in dislikes:

        dislike_text = normalize_text(
            dislike
        )

        if (
            dislike_text in recipe_name
            or
            any(
                dislike_text in normalize_text(
                    ingredient
                )
                for ingredient in recipe.get(
                    "ingredients",
                    []
                )
            )
        ):

            score -= 20


    # -------------------------------------------------
    # AVAILABLE INGREDIENTS
    # -------------------------------------------------

    for ingredient in recipe.get(
        "ingredients",
        []
    ):

        if ingredient in inventory:

            quantity = inventory[
                ingredient
            ].get(
                "quantity",
                0
            )

            if quantity > 0:

                score += 3


    # -------------------------------------------------
    # CRAVINGS
    # -------------------------------------------------

    cravings = detect_cravings(
        text
    )


    if (
        "paneer" in cravings
        and
        "paneer" in recipe.get(
            "ingredients",
            []
        )
    ):

        score += 10


    if (
        "rice" in cravings
        and
        "rice" in recipe.get(
            "ingredients",
            []
        )
    ):

        score += 10


    if "spicy" in cravings:

        score += 3


    # -------------------------------------------------
    # MOOD
    # -------------------------------------------------

    mood = detect_mood(
        text
    )

    preparation_time = recipe.get(
        "time",
        999
    )


    if mood in [
        "tired",
        "busy"
    ]:

        if preparation_time <= 30:

            score += 8

        if preparation_time <= 20:

            score += 4


    # -------------------------------------------------
    # LIGHT FOOD
    # -------------------------------------------------

    if (
        "light" in cravings
        and
        preparation_time <= 30
    ):

        score += 5


    # -------------------------------------------------
    # ALL INGREDIENTS AVAILABLE
    # -------------------------------------------------

    missing = recipe_available(
        recipe,
        inventory
    )


    if not missing:

        score += 12


    # -------------------------------------------------
    # PENALIZE MISSING INGREDIENTS
    # -------------------------------------------------

    score -= (
        len(missing) * 2
    )


    return score


# =====================================================
# CHOOSE BEST RECIPE
# =====================================================

def choose_recipe(
    profile,
    inventory,
    user_text,
    rejected_items
):

    recipes = load_recipes()

    if not recipes:
        return None


    scored_recipes = []


    for recipe in recipes:

        score = score_recipe(
            recipe,
            profile,
            inventory,
            user_text,
            rejected_items
        )

        scored_recipes.append(
            (
                score,
                recipe
            )
        )


    scored_recipes.sort(
        key=lambda item: item[0],
        reverse=True
    )


    best_score, best_recipe = (
        scored_recipes[0]
    )


    if best_score <= -900:

        return None


    return best_recipe


# =====================================================
# BUILD MEAL RESULT
# =====================================================

def build_meal_result(
    recipe,
    profile,
    inventory,
    user_text,
    status="MEAL_PROPOSED"
):

    ingredients = recipe.get(
        "ingredients",
        []
    )


    missing = recipe_available(
        recipe,
        inventory
    )


    preparation_time = recipe.get(
        "time",
        30
    )


    servings = profile.get(
        "household",
        {}
    ).get(
        "number_of_people",
        1
    )


    text = normalize_text(
        user_text
    )


    mood = detect_mood(
        text
    )


    cravings = detect_cravings(
        text
    )


    # -------------------------------------------------
    # REASON
    # -------------------------------------------------

    if mood == "tired":

        reason = (
            "You're feeling tired, so I picked "
            "something simple and manageable."
        )

    elif mood == "busy":

        reason = (
            "You're short on time, so I picked "
            "a quick option."
        )

    elif "spicy" in cravings:

        reason = (
            "You wanted something spicy, "
            "so this fits that craving."
        )

    elif "light" in cravings:

        reason = (
            "You wanted something light, "
            "so I picked a lighter option."
        )

    elif not missing:

        reason = (
            "You already have the ingredients needed, "
            "so this is an easy option to make at home."
        )

    else:

        reason = (
            "This fits your preferences and can be made "
            "with most of what you already have."
        )


    return {

        "status": status,

        "message":
            f"How about {recipe.get('name', 'this meal')}?",

        "meal": {

            "name":
                recipe.get(
                    "name",
                    ""
                ),

            "reason":
                reason,

            "preparation_time":
                preparation_time,

            "servings":
                servings,

            "ingredients":
                ingredients,

            "difficulty":
                recipe.get(
                    "difficulty",
                    "easy"
                ),

            "mood_fit":
                mood or "regular"
        },

        "missing_information": [],

        "updated_constraints": []
    }


# =====================================================
# MAIN UC1 AGENT
# =====================================================

def run_meal_agent(context):

    personal_context = context.get(
        "personal_context",
        {}
    )


    profile = personal_context.get(
        "user_profile",
        {}
    )


    inventory = personal_context.get(
        "inventory",
        {}
    )


    conversation_state = context.get(
        "conversation_state",
        {}
    )


    user_message = context.get(
        "current_request",
        {}
    ).get(
        "message",
        ""
    )


    text = normalize_text(
        user_message
    )


    current_meal = conversation_state.get(
        "current_meal"
    )


    # =================================================
    # DETECT CURRENT REQUEST
    # =================================================

    detected_ingredients = detect_ingredients(
        text,
        inventory
    )


    cooking_preference = detect_cooking_preference(
        text
    )


    meal_type = detect_meal_type(
        text
    )


    mood = detect_mood(
        text
    )


    cravings = detect_cravings(
        text
    )


    rejected_items = detect_rejected_items(
        text,
        current_meal
    )


    # =================================================
    # REPLAN?
    # =================================================

    is_replan = bool(

        rejected_items

        or

        contains_any(
            text,
            [
                "actually",
                "instead",
                "change",
                "something else",
                "another option",
                "dont want",
                "do not want",
                "don't want",
                "nahi chahiye",
                "nahi banana"
            ]
        )
    )


    # =================================================
    # USER DOES NOT WANT TO COOK
    # =================================================

    if (
        cooking_preference ==
        "do_not_want_to_cook"
    ):

        return {

            "status":
                "NEEDS_INFO",

            "message":
                "No problem. Do you want me to help arrange cooking assistance or would you rather order something?",

            "meal":
                None,

            "missing_information":
                [
                    "cooking_service_or_order"
                ],

            "updated_constraints":
                [
                    "user_does_not_want_to_cook"
                ]
        }


    # =================================================
    # OBVIOUS CONFLICT
    # =================================================

    very_short_time = contains_any(
        text,
        [
            "5 min",
            "5 minute",
            "5 minutes",
            "2 min",
            "2 minute",
            "2 minutes"
        ]
    )


    if (
        very_short_time
        and
        contains_any(
            text,
            [
                "biryani",
                "elaborate",
                "authentic"
            ]
        )
    ):

        return {

            "status":
                "CONFLICT",

            "message":
                "Those requirements conflict: an authentic biryani would normally take longer than the time you've given. Which matters more — the very short cooking time or the biryani?",

            "meal":
                None,

            "missing_information":
                [
                    "which_constraint_to_relax"
                ],

            "updated_constraints":
                []
        }


    # =================================================
    # CHOOSE RECIPE
    # =================================================

    recipe = choose_recipe(
        profile,
        inventory,
        text,
        rejected_items
    )


    # =================================================
    # NO SUITABLE RECIPE
    # =================================================

    if not recipe:

        return {

            "status":
                "NEEDS_INFO",

            "message":
                "Tell me a little more about what you're craving, and I'll narrow it down.",

            "meal":
                None,

            "missing_information":
                [
                    "food_preference"
                ],

            "updated_constraints":
                []
        }


    # =================================================
    # UPDATED CONSTRAINTS
    # =================================================

    updated_constraints = []


    if meal_type:

        updated_constraints.append(
            f"meal_type:{meal_type}"
        )


    if mood:

        updated_constraints.append(
            f"mood:{mood}"
        )


    for craving in cravings:

        updated_constraints.append(
            f"craving:{craving}"
        )


    if detected_ingredients:

        updated_constraints.append(
            "available_ingredients:" +
            ",".join(
                detected_ingredients
            )
        )


    if cooking_preference:

        updated_constraints.append(
            f"cooking_preference:{cooking_preference}"
        )


    # =================================================
    # FINAL RESULT
    # =================================================

    result = build_meal_result(
        recipe,
        profile,
        inventory,
        user_message,
        status=(
            "REPLAN"
            if is_replan
            else "MEAL_PROPOSED"
        )
    )


    result[
        "updated_constraints"
    ] = updated_constraints


    return result