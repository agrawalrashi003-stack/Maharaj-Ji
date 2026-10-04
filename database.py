# =========================================================
# MAHARAJ JI
# SQLite Database Layer
# =========================================================

import sqlite3
import os

from contextlib import contextmanager


# =========================================================
# DATABASE LOCATION
# =========================================================

BASE_DIR = os.path.dirname(
    os.path.abspath(__file__)
)

DATA_DIR = os.path.join(
    BASE_DIR,
    "data"
)

os.makedirs(
    DATA_DIR,
    exist_ok=True
)

DATABASE_PATH = os.path.join(
    DATA_DIR,
    "maharaj.db"
)


# =========================================================
# DATABASE CONNECTION
# =========================================================

@contextmanager
def get_db():

    connection = sqlite3.connect(
        DATABASE_PATH
    )

    connection.row_factory = sqlite3.Row

    try:

        yield connection

        connection.commit()

    except Exception:

        connection.rollback()

        raise

    finally:

        connection.close()


# =========================================================
# INITIALIZE DATABASE
# =========================================================

def init_db():

    with get_db() as db:

        # -------------------------------------------------
        # USERS
        # -------------------------------------------------

        db.execute(
            """
            CREATE TABLE IF NOT EXISTS users (

                id INTEGER PRIMARY KEY AUTOINCREMENT,

                name TEXT NOT NULL,

                diet TEXT,

                spice_level TEXT,

                typical_budget REAL,

                preferred_cooking_time INTEGER,

                cooking_preference TEXT,

                household_size INTEGER DEFAULT 1,

                created_at TEXT DEFAULT CURRENT_TIMESTAMP,

                updated_at TEXT DEFAULT CURRENT_TIMESTAMP

            )
            """
        )


        # -------------------------------------------------
        # FOOD PREFERENCES
        # -------------------------------------------------

        db.execute(
            """
            CREATE TABLE IF NOT EXISTS food_preferences (

                id INTEGER PRIMARY KEY AUTOINCREMENT,

                user_id INTEGER NOT NULL,

                preference_type TEXT NOT NULL,

                preference_value TEXT NOT NULL,

                created_at TEXT DEFAULT CURRENT_TIMESTAMP,

                FOREIGN KEY (user_id)
                    REFERENCES users(id)

            )
            """
        )


        # -------------------------------------------------
        # INVENTORY
        # -------------------------------------------------

        db.execute(
            """
            CREATE TABLE IF NOT EXISTS inventory (

                id INTEGER PRIMARY KEY AUTOINCREMENT,

                user_id INTEGER NOT NULL,

                ingredient TEXT NOT NULL,

                quantity REAL NOT NULL DEFAULT 0,

                unit TEXT NOT NULL,

                updated_at TEXT DEFAULT CURRENT_TIMESTAMP,

                FOREIGN KEY (user_id)
                    REFERENCES users(id)

            )
            """
        )


        # -------------------------------------------------
        # MEAL HISTORY
        # -------------------------------------------------

        db.execute(
            """
            CREATE TABLE IF NOT EXISTS meal_history (

                id INTEGER PRIMARY KEY AUTOINCREMENT,

                user_id INTEGER NOT NULL,

                meal_name TEXT NOT NULL,

                meal_reason TEXT,

                preparation_time INTEGER,

                estimated_cost REAL,

                status TEXT,

                rating INTEGER,

                feedback TEXT,

                created_at TEXT DEFAULT CURRENT_TIMESTAMP,

                FOREIGN KEY (user_id)
                    REFERENCES users(id)

            )
            """
        )


        # -------------------------------------------------
        # CONVERSATIONS
        # -------------------------------------------------

        db.execute(
            """
            CREATE TABLE IF NOT EXISTS conversations (

                id INTEGER PRIMARY KEY AUTOINCREMENT,

                user_id INTEGER NOT NULL,

                role TEXT NOT NULL,

                message TEXT NOT NULL,

                created_at TEXT DEFAULT CURRENT_TIMESTAMP,

                FOREIGN KEY (user_id)
                    REFERENCES users(id)

            )
            """
        )


        # -------------------------------------------------
        # ORDERS
        # -------------------------------------------------

        db.execute(
            """
            CREATE TABLE IF NOT EXISTS orders (

                id INTEGER PRIMARY KEY AUTOINCREMENT,

                user_id INTEGER NOT NULL,

                meal_name TEXT,

                status TEXT,

                total_amount REAL,

                provider TEXT,

                created_at TEXT DEFAULT CURRENT_TIMESTAMP,

                updated_at TEXT DEFAULT CURRENT_TIMESTAMP,

                FOREIGN KEY (user_id)
                    REFERENCES users(id)

            )
            """
        )


# =========================================================
# USER FUNCTIONS
# =========================================================

def create_user(
    name,
    diet="vegetarian",
    spice_level="medium",
    typical_budget=250,
    preferred_cooking_time=30,
    cooking_preference="cook_at_home",
    household_size=1
):

    with get_db() as db:

        cursor = db.execute(
            """
            INSERT INTO users (

                name,
                diet,
                spice_level,
                typical_budget,
                preferred_cooking_time,
                cooking_preference,
                household_size

            )

            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                name,
                diet,
                spice_level,
                typical_budget,
                preferred_cooking_time,
                cooking_preference,
                household_size
            )
        )

        return cursor.lastrowid


def get_user(
    user_id=1
):

    with get_db() as db:

        row = db.execute(
            """
            SELECT *

            FROM users

            WHERE id = ?
            """,
            (user_id,)
        ).fetchone()

        if row is None:
            return None

        return dict(row)


# =========================================================
# FOOD PREFERENCE FUNCTIONS
# =========================================================

def add_preference(
    user_id,
    preference_type,
    preference_value
):

    with get_db() as db:

        cursor = db.execute(
            """
            INSERT INTO food_preferences (

                user_id,
                preference_type,
                preference_value

            )

            VALUES (?, ?, ?)
            """,
            (
                user_id,
                preference_type,
                preference_value
            )
        )

        return cursor.lastrowid


def get_preferences(
    user_id=1
):

    with get_db() as db:

        rows = db.execute(
            """
            SELECT *

            FROM food_preferences

            WHERE user_id = ?

            ORDER BY id DESC
            """,
            (user_id,)
        ).fetchall()

        return [
            dict(row)
            for row in rows
        ]


def remove_preference(
    user_id,
    preference_type,
    preference_value=None
):

    with get_db() as db:

        if preference_value is None:

            db.execute(
                """
                DELETE FROM food_preferences

                WHERE user_id = ?

                AND preference_type = ?
                """,
                (
                    user_id,
                    preference_type
                )
            )

        else:

            db.execute(
                """
                DELETE FROM food_preferences

                WHERE user_id = ?

                AND preference_type = ?

                AND preference_value = ?
                """,
                (
                    user_id,
                    preference_type,
                    preference_value
                )
            )


# =========================================================
# INVENTORY FUNCTIONS
# =========================================================

def add_inventory_item(
    user_id,
    ingredient,
    quantity,
    unit
):

    with get_db() as db:

        existing = db.execute(
            """
            SELECT id

            FROM inventory

            WHERE user_id = ?

            AND LOWER(ingredient) = LOWER(?)
            """,
            (
                user_id,
                ingredient
            )
        ).fetchone()


        if existing:

            db.execute(
                """
                UPDATE inventory

                SET
                    quantity = ?,
                    unit = ?,
                    updated_at = CURRENT_TIMESTAMP

                WHERE id = ?
                """,
                (
                    quantity,
                    unit,
                    existing["id"]
                )
            )

        else:

            db.execute(
                """
                INSERT INTO inventory (

                    user_id,
                    ingredient,
                    quantity,
                    unit

                )

                VALUES (?, ?, ?, ?)
                """,
                (
                    user_id,
                    ingredient,
                    quantity,
                    unit
                )
            )


def get_inventory(
    user_id=1
):

    with get_db() as db:

        rows = db.execute(
            """
            SELECT
                ingredient,
                quantity,
                unit

            FROM inventory

            WHERE user_id = ?

            ORDER BY ingredient
            """,
            (user_id,)
        ).fetchall()

        return [
            dict(row)
            for row in rows
        ]


def remove_inventory_item(
    user_id,
    ingredient
):

    with get_db() as db:

        db.execute(
            """
            DELETE FROM inventory

            WHERE user_id = ?

            AND LOWER(ingredient) = LOWER(?)
            """,
            (
                user_id,
                ingredient
            )
        )


# =========================================================
# CONVERSATION FUNCTIONS
# =========================================================

def save_message(
    user_id,
    role,
    message
):

    with get_db() as db:

        db.execute(
            """
            INSERT INTO conversations (

                user_id,
                role,
                message

            )

            VALUES (?, ?, ?)
            """,
            (
                user_id,
                role,
                message
            )
        )


def get_recent_messages(
    user_id=1,
    limit=20
):

    with get_db() as db:

        rows = db.execute(
            """
            SELECT
                role,
                message,
                created_at

            FROM conversations

            WHERE user_id = ?

            ORDER BY id DESC

            LIMIT ?
            """,
            (
                user_id,
                limit
            )
        ).fetchall()


        messages = [
            dict(row)
            for row in rows
        ]


        messages.reverse()

        return messages


# =========================================================
# MEAL HISTORY
# =========================================================

def save_meal(
    user_id,
    meal_name,
    meal_reason=None,
    preparation_time=None,
    estimated_cost=None,
    status="PLANNED"
):

    with get_db() as db:

        cursor = db.execute(
            """
            INSERT INTO meal_history (

                user_id,
                meal_name,
                meal_reason,
                preparation_time,
                estimated_cost,
                status

            )

            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                user_id,
                meal_name,
                meal_reason,
                preparation_time,
                estimated_cost,
                status
            )
        )

        return cursor.lastrowid


# =========================================================
# SAVE CONFIRMED / COOKED MEAL
# =========================================================

def save_confirmed_meal(
    user_id,
    meal
):
    """
    Save the meal selected by the user.

    This is called by the agent manager after the
    user says something such as:

        "I'll cook this"
        "I'll make this"
        "Okay, I'll cook this"

    The meal is stored as COOKED so it appears
    in My Cooking History.
    """

    if not meal:

        return None


    meal_name = meal.get(
        "name",
        "Unknown Meal"
    )


    meal_reason = meal.get(
        "reason",
        meal.get(
            "description",
            "Meal selected by the user."
        )
    )


    preparation_time = meal.get(
        "preparation_time",
        meal.get(
            "time",
            None
        )
    )


    estimated_cost = meal.get(
        "estimated_cost",
        meal.get(
            "cost",
            None
        )
    )


    return save_meal(

        user_id=user_id,

        meal_name=meal_name,

        meal_reason=meal_reason,

        preparation_time=preparation_time,

        estimated_cost=estimated_cost,

        status="COOKED"

    )


def get_meal_history(
    user_id=1,
    limit=20
):
    """
    Return meals actually marked as COOKED
    from the last 7 days.
    """

    with get_db() as db:

        rows = db.execute(
            """
            SELECT *

            FROM meal_history

            WHERE user_id = ?

            AND status = 'COOKED'

            AND date(created_at)
            >= date('now', '-7 days')

            ORDER BY datetime(created_at) DESC

            LIMIT ?
            """,
            (
                user_id,
                limit
            )
        ).fetchall()


        return [
            dict(row)
            for row in rows
        ]


# =========================================================
# DEMO MEAL HISTORY
# =========================================================

def seed_demo_meal_history(
    user_id=1
):
    """
    Add one week of sample cooking history only
    when the user has no meal history.

    This runs only once.

    Once the user starts using Maharaj Ji,
    real meals are added normally.
    """

    with get_db() as db:

        # -------------------------------------------------
        # Check existing history
        # -------------------------------------------------

        existing = db.execute(
            """
            SELECT COUNT(*) AS count

            FROM meal_history

            WHERE user_id = ?
            """,
            (user_id,)
        ).fetchone()


        if existing["count"] > 0:

            return False


        # -------------------------------------------------
        # One week of demo meals
        # -------------------------------------------------

        demo_meals = [

            (
                "Paneer Rice Bowl",

                "A quick and comforting rice meal using paneer and ingredients already available at home.",

                30,

                220,

                "COOKED",

                "-1 day"
            ),

            (
                "Aloo Masala",

                "A simple spicy home-cooked meal that matched the user's craving for something comforting.",

                25,

                120,

                "COOKED",

                "-2 days"
            ),

            (
                "Spicy Paneer Wrap",

                "A quick and spicy option using paneer, capsicum and onion.",

                25,

                180,

                "COOKED",

                "-3 days"
            ),

            (
                "Paneer Rice Bowl",

                "A familiar North Indian style meal that was easy to prepare after a busy day.",

                30,

                220,

                "COOKED",

                "-4 days"
            ),

            (
                "Aloo Masala",

                "An easy vegetarian meal that required minimal preparation.",

                25,

                120,

                "COOKED",

                "-5 days"
            ),

            (
                "Spicy Paneer Wrap",

                "A quick meal chosen when there was limited time available for cooking.",

                25,

                180,

                "COOKED",

                "-6 days"
            ),

            (
                "Paneer Rice Bowl",

                "A filling home-cooked meal using ingredients from the household inventory.",

                30,

                220,

                "COOKED",

                "-7 days"
            )

        ]


        # -------------------------------------------------
        # Insert demo meals
        # -------------------------------------------------

        for meal in demo_meals:

            db.execute(
                """
                INSERT INTO meal_history (

                    user_id,
                    meal_name,
                    meal_reason,
                    preparation_time,
                    estimated_cost,
                    status,
                    created_at

                )

                VALUES (

                    ?,
                    ?,
                    ?,
                    ?,
                    ?,
                    ?,
                    datetime('now', ?)

                )
                """,
                (
                    user_id,
                    meal[0],
                    meal[1],
                    meal[2],
                    meal[3],
                    meal[4],
                    meal[5]
                )
            )


        return True


# =========================================================
# ORDER FUNCTIONS
# =========================================================

def create_order(
    user_id,
    meal_name,
    status="DRAFT",
    total_amount=0,
    provider=None
):

    with get_db() as db:

        cursor = db.execute(
            """
            INSERT INTO orders (

                user_id,
                meal_name,
                status,
                total_amount,
                provider

            )

            VALUES (?, ?, ?, ?, ?)
            """,
            (
                user_id,
                meal_name,
                status,
                total_amount,
                provider
            )
        )

        return cursor.lastrowid


def update_order_status(
    order_id,
    status
):

    with get_db() as db:

        db.execute(
            """
            UPDATE orders

            SET
                status = ?,
                updated_at = CURRENT_TIMESTAMP

            WHERE id = ?
            """,
            (
                status,
                order_id
            )
        )


def get_order(
    order_id
):

    with get_db() as db:

        row = db.execute(
            """
            SELECT *

            FROM orders

            WHERE id = ?
            """,
            (order_id,)
        ).fetchone()


        if row is None:

            return None


        return dict(row)


def get_user_orders(
    user_id=1,
    limit=20
):

    with get_db() as db:

        rows = db.execute(
            """
            SELECT *

            FROM orders

            WHERE user_id = ?

            ORDER BY id DESC

            LIMIT ?
            """,
            (
                user_id,
                limit
            )
        ).fetchall()


        return [
            dict(row)
            for row in rows
        ]


# =========================================================
# START DATABASE
# =========================================================

if __name__ == "__main__":

    init_db()

    print(
        "Maharaj Ji SQLite database initialized."
    )

    print(
        f"Database location: {DATABASE_PATH}"
    )