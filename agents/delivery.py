import uuid


def create_delivery(order_id):

    tracking_id = "TRK-" + str(uuid.uuid4())[:8].upper()

    return {
        "order_id": order_id,
        "tracking_id": tracking_id,
        "status": "CONFIRMED",
        "eta": "30-45 minutes"
    }


def track_delivery(tracking_id):

    return {
        "tracking_id": tracking_id,
        "status": "OUT_FOR_DELIVERY",
        "eta": "20 minutes"
    }