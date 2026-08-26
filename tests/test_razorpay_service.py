from services.razorpay_service import get_razorpay_client


def main():

    client = get_razorpay_client()

    print("\n===== RAZORPAY TEST CONNECTION =====")

    try:

        payments = client.payment.all({
            "count": 1
        })

        print("Connection successful.")
        print(
            "Payments returned:",
            len(payments.get("items", []))
        )

    except Exception as e:

        print("Connection failed:")
        print(e)


if __name__ == "__main__":
    main()