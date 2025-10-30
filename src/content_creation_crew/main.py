# crew/main.py
from dotenv import load_dotenv
load_dotenv()

import sys
import re
# ⬇️ ADICIONADO: utilitários para salvar JSON/ler arquivo
from pathlib import Path  # ADICIONADO
import json               # ADICIONADO

from content_creation_crew.crew import ContentCreationCrewCrew

# ===== Regras de contagem de palavras (PT/EN) =====
_WORD_RE = re.compile(r"\b[\wÀ-ÿ'-]+\b", re.UNICODE)
MIN_WORDS = 300

def count_words(text: str) -> int:
    if not isinstance(text, str):
        return 0
    return len(_WORD_RE.findall(text))

# ⬇️ ADICIONADO: prioriza Markdown da execução
def _extract_markdown_result(result) -> str:
    """
    Tenta obter o Markdown final do Crew:
    1) result.raw (CrewOutput moderno)
    2) se result já for str, usa direto
    3) fallback: lê 'report.md' gravado pela task
    4) último recurso: str(result)
    """
    # Caso CrewAI novo: CrewOutput com .raw
    md = getattr(result, "raw", None)
    if isinstance(md, str) and md.strip():
        return md

    # Caso a lib antiga retorne str diretamente
    if isinstance(result, str):
        return result

    # Fallback: arquivo salvo pela Task (output_file="report.md")
    try:
        return Path("report.md").read_text(encoding="utf-8")
    except Exception:
        pass

    # Último recurso
    return str(result)

# ⬇️ ADICIONADO: salva Pydantic/JSON se existir
def _persist_structured_output(result) -> Path | None:
    """
    Se houver 'result.pydantic' (CrewOutput com output_pydantic),
    salva em report.json. Caso contrário, tenta 'to_dict()' como fallback.
    Retorna o Path salvo ou None.
    """
    json_path = Path("report.json")

    try:
        p = getattr(result, "pydantic", None)
        if p is not None:
            # Pydantic v2
            try:
                json_path.write_text(
                    p.model_dump_json(indent=2, ensure_ascii=False),
                    encoding="utf-8",
                )
                return json_path
            except AttributeError:
                # Pydantic v1
                json_path.write_text(
                    p.json(indent=2, ensure_ascii=False),
                    encoding="utf-8",
                )
                return json_path

        # Fallback: alguns CrewOutput têm .to_dict()
        to_dict = getattr(result, "to_dict", None)
        if callable(to_dict):
            json_path.write_text(
                json.dumps(to_dict(), indent=2, ensure_ascii=False),
                encoding="utf-8",
            )
            return json_path

    except Exception:
        # Não falhe a execução só porque o JSON não foi salvo
        return None

    return None

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

        # ⬇️ ADICIONADO: grava saída estruturada (Pydantic/JSON) se disponível
        json_path = _persist_structured_output(result)

        # ===== Validação de mínimo de 300 palavras (baseada no MARKDOWN) =====
        final_markdown = _extract_markdown_result(result)  # ← usa Markdown, não JSON
        wc = count_words(final_markdown)

        print("\n" + "="*50)
        print("FINAL RESULT:")
        print("="*50)
        print(final_markdown)  # ← imprime o Markdown no console

        print("\n" + "-"*50)
        print(f"Word count: {wc} (minimum required: {MIN_WORDS})")
        if wc < MIN_WORDS:
            # Falha explícita para evitar que conteúdos curtos passem despercebidos no CLI
            raise SystemExit(f"❌ The generated article has {wc} words; minimum is {MIN_WORDS}.")

        print("✅ Minimum word count satisfied.")

        # ⬇️ Mensagens úteis sobre arquivos gerados
        if Path("report.md").exists():
            print("📝 Markdown saved to: report.md")
        if json_path is not None and json_path.exists():
            print(f"🧾 Structured JSON saved to: {json_path}")

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
