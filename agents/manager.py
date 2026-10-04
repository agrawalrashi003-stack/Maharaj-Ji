# =========================================================
# MAHARAJ JI
# Main Agent Manager
# SQLite Connected Version
# =========================================================

from agents.context import get_personal_context
from agents.meal import run_meal_agent
from agents.inventory import check_inventory
from agents.payment import request_payment
from agents.delivery import create_delivery

from database import (
    init_db,
    create_user,
    get_user,
    get_inventory,
    save_message,
    save_meal,
)


# =========================================================
# DATABASE INITIALIZATION
# =========================================================

init_db()


# =========================================================
# CURRENT USER
# =========================================================

DEFAULT_USER_ID = 1


# =========================================================
# TEMPORARY CONVERSATION STATE
# =========================================================

conversation_state = {}


# =========================================================
# ENSURE DEFAULT USER EXISTS
# =========================================================

def ensure_default_user():

    user = get_user(
        DEFAULT_USER_ID
    )

    if user:
        return user

    user_id = create_user(
        name="Rashi",
        diet="vegetarian",
        spice_level="medium",
        typical_budget=250,
        preferred_cooking_time=30,
        cooking_preference="cook_at_home",
        household_size=1
    )

    return get_user(
        user_id
    )


# =========================================================
# ORDER APPROVAL DETECTION
# =========================================================

def is_order_approval(message):

    text = (
        message
        .lower()
        .strip()
    )

    phrases = [
        "yes, order it",
        "yes order it",
        "order it",
        "place the order",
        "place order",
        "go ahead",
        "yes, go ahead",
        "yes go ahead",
        "buy them",
        "buy it",
        "yes, buy it",
        "yes buy it",
        "please order",
        "please place the order"
    ]

    return any(
        phrase in text
        for phrase in phrases
    )


# =========================================================
# COOKING REQUEST DETECTION
# =========================================================

def is_cooking_request(message):

    text = (
        message
        .lower()
        .strip()
    )

    phrases = [
        "i'll cook it",
        "i will cook it",
        "i'll cook this",
        "i will cook this",
        "let me cook",
        "i want to cook it",
        "i want to cook this",
        "i am going to cook it",
        "i am going to cook this",
        "i'm going to cook it",
        "i'm going to cook this"
    ]

    return any(
        phrase in text
        for phrase in phrases
    )


# =========================================================
# MEAL CONFIRMATION DETECTION
# =========================================================

def is_meal_confirmation(message):

    text = (
        message
        .lower()
        .strip()
        .replace(",", "")
        .replace(".", "")
        .replace("!", "")
    )

    confirmation_phrases = [

        # Cook this / it
        "okay i'll cook this",
        "okay i will cook this",
        "ok i'll cook this",
        "ok i will cook this",

        "okay i'll cook it",
        "okay i will cook it",
        "ok i'll cook it",
        "ok i will cook it",

        "i'll cook this",
        "i will cook this",
        "i'll cook it",
        "i will cook it",

        # Make this / it
        "okay i'll make this",
        "okay i will make this",
        "ok i'll make this",
        "ok i will make this",

        "okay i'll make it",
        "okay i will make it",
        "ok i'll make it",
        "ok i will make it",

        "i'll make this",
        "i will make this",
        "i'll make it",
        "i will make it",

        # Yes confirmations
        "yes i'll cook this",
        "yes i will cook this",
        "yes i'll cook it",
        "yes i will cook it",

        "yes i'll make this",
        "yes i will make this",
        "yes i'll make it",
        "yes i will make it",

        # Sounds good
        "sounds good i'll cook this",
        "sounds good i will cook this",
        "sounds good i'll cook it",
        "sounds good i will cook it",

        "sounds good i'll make this",
        "sounds good i will make this",
        "sounds good i'll make it",
        "sounds good i will make it",

        # Selection
        "i'll go with this",
        "i will go with this",
        "i'll go with it",
        "i will go with it",

        "let's cook this",
        "lets cook this",
        "let's cook it",
        "lets cook it",

        "let's make this",
        "lets make this",
        "let's make it",
        "lets make it",

        # Natural confirmations
        "i'll have this",
        "i will have this",
        "i'll have it",
        "i will have it",

        "this works for me",
        "this works",
        "that works for me",
        "that works",

        "this is good",
        "that is good",
        "this sounds good",
        "that sounds good"
    ]

    return any(
        phrase in text
        for phrase in confirmation_phrases
    )


# =========================================================
# SAVE CONFIRMED MEAL
# =========================================================

def save_confirmed_meal(
    user_id,
    meal
):

    if not meal:
        return None

    meal_name = meal.get(
        "name",
        "Unnamed Meal"
    )

    meal_reason = meal.get(
        "reason"
    )

    preparation_time = meal.get(
        "preparation_time"
    )

    estimated_cost = meal.get(
        "estimated_cost"
    )

    meal_id = save_meal(
        user_id=user_id,
        meal_name=meal_name,
        meal_reason=meal_reason,
        preparation_time=preparation_time,
        estimated_cost=estimated_cost,
        status="COOKED"
    )

    print(
        "MEAL SAVED TO HISTORY:",
        meal_name,
        "ID:",
        meal_id
    )

    return meal_id


# =========================================================
# SAFE RECENT MESSAGE LOADER
# =========================================================

def get_recent_messages_safe(user_id):

    from database import get_recent_messages

    return get_recent_messages(
        user_id=user_id,
        limit=20
    )


# =========================================================
# MAIN MANAGER
# =========================================================

def run_manager(
    user_message,
    user_id=DEFAULT_USER_ID,
    live_meal=None
):

    global conversation_state

    print("\n")
    print("=================================================")
    print("MAHARAJ JI MANAGER")
    print("USER MESSAGE:", user_message)
    print("LIVE MEAL:", live_meal)
    print("=================================================")

    # -----------------------------------------------------
    # 1. Make sure user exists
    # -----------------------------------------------------

    user = get_user(
        user_id
    )

    if user is None:

        user = ensure_default_user()

        user_id = user["id"]


    # -----------------------------------------------------
    # 2. Create state for this user
    # -----------------------------------------------------

    if user_id not in conversation_state:

        conversation_state[user_id] = {

            "last_user_message": None,

            "last_status": None,

            "updated_constraints": [],

            "current_meal": None,

            "meal_confirmed": False,

            "inventory_result": None,

            "payment_result": None,

            "delivery_result": None,

            "order_status": None
        }


    user_state = conversation_state[
        user_id
    ]


    # -----------------------------------------------------
    # 3. SAVE USER MESSAGE
    # -----------------------------------------------------

    save_message(
        user_id=user_id,
        role="user",
        message=user_message
    )


    # =====================================================
    # IMPORTANT FIX
    # =====================================================
    #
    # If Gemini Live sends the exact meal it recommended,
    # that meal becomes the current meal.
    #
    # DO NOT call run_meal_agent and overwrite it.
    #
    # =====================================================

    if live_meal:

        print(
            "=============================================="
        )

        print(
            "LIVE GEMINI MEAL RECEIVED"
        )

        print(
            "MEAL:",
            live_meal.get(
                "name",
                "Unnamed Meal"
            )
        )

        print(
            "=============================================="
        )

        user_state[
            "current_meal"
        ] = live_meal

        user_state[
            "meal_confirmed"
        ] = False


    # =====================================================
    # 4. MEAL CONFIRMATION
    # =====================================================

    if (
        is_meal_confirmation(user_message)
        and user_state.get("current_meal")
    ):

        current_meal = user_state[
            "current_meal"
        ]


        # -------------------------------------------------
        # Prevent duplicate saving
        # -------------------------------------------------

        if not user_state.get(
            "meal_confirmed",
            False
        ):

            meal_id = save_confirmed_meal(
                user_id=user_id,
                meal=current_meal
            )

            user_state[
                "meal_confirmed"
            ] = True

            meal_name = current_meal.get(
                "name",
                "your selected meal"
            )

            confirmation_message = (
                f"Perfect! {meal_name} "
                f"is added to your cooking history. "
                f"Enjoy your meal!"
            )

            save_message(
                user_id=user_id,
                role="assistant",
                message=confirmation_message
            )

            user_state[
                "last_user_message"
            ] = user_message

            user_state[
                "last_status"
            ] = "MEAL_CONFIRMED"

            return {

                "status":
                    "MEAL_CONFIRMED",

                "message":
                    confirmation_message,

                "meal":
                    current_meal,

                "meal_history_id":
                    meal_id,

                "missing_information":
                    [],

                "updated_constraints":
                    [],

                "inventory":
                    user_state.get(
                        "inventory_result"
                    )
            }


        # -------------------------------------------------
        # Already confirmed
        # -------------------------------------------------

        meal_name = current_meal.get(
            "name",
            "your selected meal"
        )

        confirmation_message = (
            f"{meal_name} is already saved "
            f"in your cooking history."
        )

        save_message(
            user_id=user_id,
            role="assistant",
            message=confirmation_message
        )

        return {

            "status":
                "MEAL_ALREADY_CONFIRMED",

            "message":
                confirmation_message,

            "meal":
                current_meal,

            "meal_history_id":
                None,

            "missing_information":
                [],

            "updated_constraints":
                [],

            "inventory":
                user_state.get(
                    "inventory_result"
                )
        }


    # =====================================================
    # 5. ORDER APPROVAL
    # =====================================================

    if (
        is_order_approval(user_message)
        and user_state.get(
            "order_status"
        ) == "AWAITING_APPROVAL"
    ):

        inventory_result = user_state.get(
            "inventory_result"
        )

        missing_items = []

        if inventory_result:

            missing_items = inventory_result.get(
                "missing",
                []
            )

        if not missing_items:

            message = (
                "There are no missing ingredients "
                "to order."
            )

            user_state[
                "order_status"
            ] = None

            save_message(
                user_id=user_id,
                role="assistant",
                message=message
            )

            return {

                "status":
                    "NO_ORDER_REQUIRED",

                "message":
                    message,

                "meal":
                    user_state.get(
                        "current_meal"
                    ),

                "inventory":
                    inventory_result
            }


        # -------------------------------------------------
        # Demo pricing
        # -------------------------------------------------

        cost = 50 * len(
            missing_items
        )

        print(
            "========== UC3 PAYMENT =========="
        )

        print(
            "Missing items:",
            missing_items
        )

        print(
            "Demo cart cost:",
            cost
        )


        # -------------------------------------------------
        # Payment
        # -------------------------------------------------

        payment_result = request_payment(
            cost
        )

        print(
            "PINE LABS CALL:",
            payment_result
        )

        user_state[
            "payment_result"
        ] = payment_result


        if not payment_result.get(
            "success",
            False
        ):

            user_state[
                "order_status"
            ] = "PAYMENT_FAILED"

            message = (
                "I couldn't complete the payment. "
                "Your order has not been placed."
            )

            save_message(
                user_id=user_id,
                role="assistant",
                message=message
            )

            return {

                "status":
                    "PAYMENT_FAILED",

                "message":
                    message,

                "payment":
                    payment_result,

                "inventory":
                    inventory_result
            }


        # -------------------------------------------------
        # Delivery
        # -------------------------------------------------

        payment_id = payment_result.get(
            "payment_id"
        )

        delivery_result = create_delivery(
            payment_id
        )

        print(
            "DELHIVERY CALL:",
            delivery_result
        )

        user_state[
            "delivery_result"
        ] = delivery_result

        user_state[
            "order_status"
        ] = "DELIVERY_CREATED"


        message = (
            f"Payment of ₹{cost} was successful. "
            "I've created the delivery for your "
            "missing ingredients."
        )

        save_message(
            user_id=user_id,
            role="assistant",
            message=message
        )

        return {

            "status":
                "DELIVERY_CREATED",

            "message":
                message,

            "meal":
                user_state.get(
                    "current_meal"
                ),

            "inventory":
                inventory_result,

            "payment":
                payment_result,

            "delivery":
                delivery_result
        }


    # =====================================================
    # 6. LOAD PERSONAL CONTEXT
    # =====================================================

    personal_context = get_personal_context(
        user_id
    )


    # =====================================================
    # 7. LOAD RECENT CONVERSATION
    # =====================================================

    recent_messages = get_recent_messages_safe(
        user_id
    )


    # =====================================================
    # 8. LOAD INVENTORY
    # =====================================================

    stored_inventory = get_inventory(
        user_id
    )


    # =====================================================
    # 9. BUILD REQUEST
    # =====================================================

    current_request = {

        "message":
            user_message,

        "user_id":
            user_id,

        "user":
            user,

        "inventory":
            stored_inventory,

        "recent_messages":
            recent_messages
    }


    # =====================================================
    # 10. BUILD CONTEXT
    # =====================================================

    context = {

        "personal_context":
            personal_context,

        "current_request":
            current_request,

        "conversation_state":
            user_state,

        "database_user":
            user,

        "database_inventory":
            stored_inventory,

        "conversation_history":
            recent_messages
    }


    # =====================================================
    # 11. MEAL DECISION
    # =====================================================
    #
    # ONLY use the deterministic backend if Gemini Live
    # did NOT provide a concrete meal.
    #
    # =====================================================

    if live_meal:

        meal_result = {

            "status":
                "MEAL_RECOMMENDED",

            "message":
                "",

            "meal":
                live_meal,

            "missing_information":
                [],

            "updated_constraints":
                []
        }

    else:

        meal_result = run_meal_agent(
            context
        )


    # =====================================================
    # 12. UPDATE STATE
    # =====================================================

    user_state[
        "last_user_message"
    ] = user_message

    user_state[
        "last_status"
    ] = meal_result.get(
        "status"
    )

    user_state[
        "updated_constraints"
    ] = meal_result.get(
        "updated_constraints",
        []
    )


    # =====================================================
    # 13. STORE NEW MEAL
    # =====================================================

    if meal_result.get(
        "meal"
    ):

        # IMPORTANT:
        # live_meal takes priority.

        if live_meal:

            user_state[
                "current_meal"
            ] = live_meal

        else:

            user_state[
                "current_meal"
            ] = meal_result[
                "meal"
            ]

        user_state[
            "meal_confirmed"
        ] = False


    # =====================================================
    # 14. CHECK INVENTORY
    # =====================================================

    inventory_result = None

    if user_state.get(
        "current_meal"
    ):

        ingredients = user_state[
            "current_meal"
        ].get(
            "ingredients",
            []
        )

        if ingredients:

            inventory_result = check_inventory(
                ingredients
            )

            user_state[
                "inventory_result"
            ] = inventory_result


    # =====================================================
    # 15. MISSING INGREDIENTS
    # =====================================================

    if (
        inventory_result
        and inventory_result.get(
            "missing"
        )
    ):

        missing_items = inventory_result.get(
            "missing",
            []
        )

        user_state[
            "order_status"
        ] = "AWAITING_APPROVAL"

        meal_name = user_state[
            "current_meal"
        ].get(
            "name",
            "your meal"
        )

        missing_text = ", ".join(
            str(item)
            for item in missing_items
        )

        message = (
            f"{meal_name} looks good. "
            f"You are missing: {missing_text}. "
            f"Would you like me to order them?"
        )

    else:

        user_state[
            "order_status"
        ] = None

        message = meal_result.get(
            "message"
        )


    # =====================================================
    # 16. FINAL RESULT
    # =====================================================

    result = {

        "status":
            meal_result.get(
                "status"
            ),

        "message":
            message,

        "meal":
            user_state.get(
                "current_meal"
            ),

        "missing_information":
            meal_result.get(
                "missing_information",
                []
            ),

        "updated_constraints":
            meal_result.get(
                "updated_constraints",
                []
            ),

        "inventory":
            inventory_result
    }


    # =====================================================
    # 17. SAVE ASSISTANT RESPONSE
    # =====================================================

    assistant_message = result.get(
        "message"
    )

    if assistant_message:

        save_message(
            user_id=user_id,
            role="assistant",
            message=assistant_message
        )


    # =====================================================
    # 18. RETURN
    # =====================================================

    print(
        "FINAL MANAGER MEAL:",
        result.get("meal")
    )

    print(
        "FINAL STATUS:",
        result.get("status")
    )

    print(
        "=================================================\n"
    )

    return result


# =========================================================
# DIRECT TEST
# =========================================================

if __name__ == "__main__":

    print(
        "========================================"
    )

    print(
        "MAHARAJ JI MANAGER TEST"
    )

    print(
        "========================================"
    )

    user = ensure_default_user()

    print(
        f"User loaded: {user['name']}"
    )

    print(
        f"User ID: {user['id']}"
    )

    test_message = (
        "What should I cook today?"
    )

    print(
        f"\nUser: {test_message}"
    )

    result = run_manager(
        test_message,
        user_id=user["id"]
    )

    print(
        "\nMaharaj Ji:"
    )

    print(
        result
    )