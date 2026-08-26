from services.razorpay_service import get_razorpay_client


def main():

    client = get_razorpay_client()

    print("\n===== RAZORPAY TEST PAYMENTS =====")

    try:

        response = client.payment.all({
            "count": 10
        })

        payments = response.get("items", [])

        if not payments:
            print("No test payments found.")
            return

        for payment in payments:

            print("\n------------------------------")
            print("Payment ID:", payment.get("id"))
            print(
                "Amount:",
                f'₹{payment.get("amount", 0) / 100:,.2f}'
            )
            print("Currency:", payment.get("currency"))
            print("Status:", payment.get("status"))
            print("Method:", payment.get("method"))

            print(
                "Error code:",
                payment.get("error_code")
            )

            print(
                "Error description:",
                payment.get("error_description")
            )

            print(
                "Order ID:",
                payment.get("order_id")
            )

    except Exception as e:

        print("Unable to fetch Razorpay payments:")
        print(e)


if __name__ == "__main__":
    main()