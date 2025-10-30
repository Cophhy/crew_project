# src/content_creation_crew/main.py
from dotenv import load_dotenv
load_dotenv()

import sys
from content_creation_crew.crew import ContentCreationCrewCrew, ContentCreationCrewRunner
from content_creation_crew.schemas import model_to_json


def run():
    """
    Executa a crew para um tópico específico e imprime o resultado em JSON (Pydantic).
    """
    print("Welcome to the Content Creation Crew!")
    print("This crew will help you create comprehensive blog posts on any topic.")
    print()

    topic = input("Enter the topic you want to create content about: ").strip()

    if not topic:
        print("Please provide a valid topic.")
        return

    print(f"\nCreating content about: {topic}")
    print("This may take a few minutes as the agents collaborate...")
    print("-" * 50)

    inputs = {"topic": topic}

    try:
        runner = ContentCreationCrewRunner()
        output = runner.run(**inputs)

        print("\n" + "=" * 50)
        print("FINAL RESULT (Pydantic JSON):")
        print("=" * 50)
        print(model_to_json(output, indent=2))

    except Exception as e:
        print(f"An error occurred: {e}")
        print("Make sure Ollama is running and the chosen model is available.")
        print("Try running: ollama list")
        print("If mistral is not listed, run: ollama pull mistral")


def train():
    """
    Treina a crew pelo número de iterações informado em sys.argv[1].
    Mantém o fluxo original de treino.
    """
    topic = input("Enter the topic for training: ").strip()
    inputs = {"topic": topic}

    try:
        # Treinamento continua usando a própria Crew base (sem Pydantic no retorno)
        ContentCreationCrewCrew().crew().train(n_iterations=int(sys.argv[1]), inputs=inputs)
    except Exception as e:
        raise Exception(f"An error occurred while training the crew: {e}")


if __name__ == "__main__":
    run()
