from agents.recovery_agent import create_llm


def main():

    llm = create_llm()

    response = llm.invoke(
        "Explain in one sentence what a failed payment means."
    )

    print("\n===== GROQ RESPONSE =====")
    print(response.content)


if __name__ == "__main__":
    main()