# crew/main.py
from dotenv import load_dotenv
load_dotenv()

import sys
import re
from content_creation_crew.crew import ContentCreationCrewCrew

# ===== Regras de contagem de palavras (PT/EN) =====
_WORD_RE = re.compile(r"\b[\wÀ-ÿ'-]+\b", re.UNICODE)
MIN_WORDS = 300

def count_words(text: str) -> int:
    if not isinstance(text, str):
        return 0
    return len(_WORD_RE.findall(text))

def run():
    """
    Run the crew with a specific topic.
    """
    print("Welcome to the Content Creation Crew!")
    print("This crew will help you create comprehensive blog posts on any topic.")
    print()
    
    topic = input("Enter the topic you want to create content about: ")
    
    if not topic.strip():
        print("Please provide a valid topic.")
        return
    
    print(f"\nCreating content about: {topic}")
    print("This may take a few minutes as the agents collaborate...")
    print("-" * 50)
    
    inputs = {
        'topic': topic
    }
    
    try:
        result = ContentCreationCrewCrew().crew().kickoff(inputs=inputs)

        # ===== Validação de mínimo de 300 palavras =====
        wc = count_words(result if isinstance(result, str) else str(result))
        print("\n" + "="*50)
        print("FINAL RESULT:")
        print("="*50)
        print(result)

        print("\n" + "-"*50)
        print(f"Word count: {wc} (minimum required: {MIN_WORDS})")
        if wc < MIN_WORDS:
            # Falha explícita para evitar que conteúdos curtos passem despercebidos no CLI
            raise SystemExit(f"❌ The generated article has {wc} words; minimum is {MIN_WORDS}.")

        print("✅ Minimum word count satisfied.")

    except SystemExit as e:
        # Repassa o SystemExit (usado para sinalizar a validação)
        raise
    except Exception as e:
        print(f"An error occurred: {e}")
        print("Make sure Ollama is running and the mistral model is available.")
        print("Try running: ollama list")
        print("If mistral is not listed, run: ollama pull mistral")

def train():
    """
    Train the crew for a given number of iterations.
    """
    topic = input("Enter the topic for training: ")
    
    inputs = {
        'topic': topic
    }
    try:
        ContentCreationCrewCrew().crew().train(n_iterations=int(sys.argv[1]), inputs=inputs)
    except Exception as e:
        raise Exception(f"An error occurred while training the crew: {e}")

if __name__ == "__main__":
    run()
