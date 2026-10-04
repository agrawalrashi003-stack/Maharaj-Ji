# =========================================================
# MAHARAJ JI
# Flask Application
# SQLite Connected Version
# =========================================================

import datetime

from flask import (
    Flask,
    render_template,
    request,
    jsonify
)

from google import genai

from agents.manager import run_manager

from database import (
    init_db,
    get_inventory,
    seed_demo_meal_history
)

from config import (
    GEMINI_API_KEY,
    LIVE_MODEL
)


app = Flask(__name__)


# ==========================================
# INITIALIZE DATABASE
# ==========================================

init_db()
seed_demo_meal_history(user_id=1)


# ==========================================
# HOME
# ==========================================

@app.route("/")
def home():

    return render_template(
        "index.html"
    )


# ==========================================
# CHAT PAGE
# ==========================================

@app.route("/chat")
def chat():

    return render_template(
        "chat.html"
    )


# ==========================================
# COOKING HISTORY
# ==========================================

@app.route("/history")
def history():

    from database import get_meal_history

    user_id = 1

    meals = get_meal_history(
        user_id=user_id,
        limit=50
    )

    return render_template(
        "history.html",
        meals=meals
    )


# ==========================================
# KITCHEN INVENTORY
# ==========================================

@app.route(
    "/api/inventory",
    methods=["GET"]
)
def inventory_api():

    try:

        # --------------------------------------
        # USER ID
        # --------------------------------------

        user_id = request.args.get(
            "user_id",
            1
        )

        try:

            user_id = int(user_id)

        except (TypeError, ValueError):

            user_id = 1

        # --------------------------------------
        # GET INVENTORY FROM SQLITE
        # --------------------------------------

        inventory = get_inventory(
            user_id=user_id
        )

        return jsonify({

            "success": True,

            "inventory": inventory

        })

    except Exception as e:

        print(
            "\n========== INVENTORY ERROR =========="
        )

        print(
            type(e).__name__
        )

        print(
            str(e)
        )

        print(
            "=====================================\n"
        )

        return jsonify({

            "success": False,

            "error": str(e)

        }), 500


# ==========================================
# TEXT CHAT
# ==========================================

@app.route(
    "/api/chat",
    methods=["POST"]
)
def chat_api():

    try:

        data = request.get_json() or {}

        user_message = (
            data
            .get("message", "")
            .strip()
        )

        if not user_message:

            return jsonify({
                "success": False,
                "error": "Please enter a message."
            }), 400

        # --------------------------------------
        # USER ID
        # --------------------------------------

        user_id = data.get(
            "user_id",
            1
        )

        try:

            user_id = int(user_id)

        except (TypeError, ValueError):

            user_id = 1

        # --------------------------------------
        # LIVE MEAL
        # --------------------------------------
        #
        # When Gemini Live recommends a meal,
        # chat.js can send that exact meal here.
        #
        # This prevents the backend's hardcoded
        # recipes from replacing Gemini's meal.
        #
        # --------------------------------------

        live_meal = data.get(
            "live_meal"
        )

        # --------------------------------------
        # RUN MAHARAJ JI
        # --------------------------------------

        result = run_manager(
            user_message,
            user_id=user_id,
            live_meal=live_meal
        )

        return jsonify({

            "success": True,

            "result": result

        })

    except Exception as e:

        print(
            "\n========== CHAT ERROR =========="
        )

        print(
            type(e).__name__
        )

        print(
            str(e)
        )

        print(
            "================================\n"
        )

        return jsonify({

            "success": False,

            "error": str(e)

        }), 500


# ==========================================
# GEMINI LIVE EPHEMERAL TOKEN
# ==========================================

@app.route(
    "/api/live-token",
    methods=["POST"]
)
def create_live_token():

    try:

        client = genai.Client(
            api_key=GEMINI_API_KEY
        )

        now = datetime.datetime.now(
            datetime.timezone.utc
        )

        token = client.auth_tokens.create(

            config={

                "uses": 1,

                "expire_time":
                    now + datetime.timedelta(
                        minutes=30
                    ),

                "new_session_expire_time":
                    now + datetime.timedelta(
                        minutes=1
                    ),

                "live_connect_constraints": {

                    "model": LIVE_MODEL,

                    "config": {

                        "response_modalities": [
                            "AUDIO"
                        ],

                        "session_resumption": {}

                    }

                }

            }

        )

        print(
            "\n========== MAHARAJ JI LIVE =========="
        )

        print(
            "Live token created successfully."
        )

        print(
            "=====================================\n"
        )

        return jsonify({

            "success": True,

            "token": token.name

        })

    except Exception as e:

        print(
            "\n========== LIVE TOKEN ERROR =========="
        )

        print(
            type(e).__name__
        )

        print(
            str(e)
        )

        print(
            "======================================\n"
        )

        return jsonify({

            "success": False,

            "error": str(e)

        }), 500


# ==========================================
# START SERVER
# ==========================================

if __name__ == "__main__":

    app.run(

        debug=True,

        host="127.0.0.1",

        port=5000

    )