import uuid


def request_payment(amount):

    payment_id = "PAY-" + str(uuid.uuid4())[:8].upper()

    return {
        "payment_id": payment_id,
        "amount": amount,
        "currency": "INR",
        "status": "PENDING",
        "message": "Payment authorization required."
    }


def confirm_payment(payment_id):

    return {
        "payment_id": payment_id,
        "status": "SUCCESS",
        "message": "Payment completed successfully."
    }