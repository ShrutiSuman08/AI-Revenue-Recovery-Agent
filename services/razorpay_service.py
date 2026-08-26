import os

import razorpay
from dotenv import load_dotenv


load_dotenv()


RAZORPAY_KEY_ID = os.getenv("RAZORPAY_KEY_ID")
RAZORPAY_KEY_SECRET = os.getenv("RAZORPAY_KEY_SECRET")


def get_razorpay_client():

    if not RAZORPAY_KEY_ID or not RAZORPAY_KEY_SECRET:
        raise ValueError(
            "Razorpay credentials are not configured."
        )

    client = razorpay.Client(
        auth=(
            RAZORPAY_KEY_ID,
            RAZORPAY_KEY_SECRET
        )
    )

    return client


def fetch_order(order_id):

    client = get_razorpay_client()

    return client.order.fetch(order_id)


def fetch_payment(payment_id):

    client = get_razorpay_client()

    return client.payment.fetch(payment_id)