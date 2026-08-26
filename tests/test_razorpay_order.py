from services.razorpay_service import get_razorpay_client


def main():

    client = get_razorpay_client()

    print("\n===== CREATE RAZORPAY TEST ORDER =====")

    order_data = {
        # Razorpay expects amount in paise
        # ₹500 = 50000 paise
        "amount": 50000,
        "currency": "INR",
        "receipt": "recovery_demo_001",
        "notes": {
            "source": "AI Revenue Recovery Agent"
        }
    }

    try:

        # -----------------------------------------
        # CREATE ORDER
        # -----------------------------------------

        order = client.order.create(
            data=order_data
        )

        print("Order created successfully.")
        print("Order ID:", order["id"])

        print(
            "Amount:",
            f'₹{order["amount"] / 100:,.2f}'
        )

        print(
            "Currency:",
            order["currency"]
        )

        print(
            "Status:",
            order["status"]
        )

        # -----------------------------------------
        # FETCH SAME ORDER
        # -----------------------------------------

        fetched_order = client.order.fetch(
            order["id"]
        )

        print("\n===== FETCH RAZORPAY TEST ORDER =====")

        print("Order fetched successfully.")

        print(
            "Order ID:",
            fetched_order["id"]
        )

        print(
            "Amount:",
            f'₹{fetched_order["amount"] / 100:,.2f}'
        )

        print(
            "Currency:",
            fetched_order["currency"]
        )

        print(
            "Status:",
            fetched_order["status"]
        )

    except Exception as e:

        print("Razorpay operation failed:")
        print(e)


if __name__ == "__main__":
    main()