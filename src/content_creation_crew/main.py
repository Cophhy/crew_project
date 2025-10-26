# src/content_creation_crew/main.py
from pathlib import Path
import yaml
from .crew import build_crew, build_llm

BASE = Path(__file__).resolve().parent
AGENTS = BASE / "config" / "agents.yaml"
TASKS = BASE / "config" / "tasks.yaml"

def load_yaml(path: Path):
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)

def run_crew(user_query: str, model_id: str, lang: str):
    agents_config = load_yaml(AGENTS)
    tasks_config = load_yaml(TASKS)

    # injeta a entrada do usuário na primeira task de pesquisa (ajuste o nome se for diferente)
    if "research_topic" in tasks_config:
        tasks_config["research_topic"]["input"] = {"topic": user_query}
    else:
        # fallback genérico: injete no primeiro item
        first_key = next(iter(tasks_config))
        tasks_config[first_key]["input"] = {"query": user_query}

    llm = build_llm(model_id)
    crew = build_crew(agents_config, tasks_config, llm, lang)
    result = crew.kickoff()  # retorna o output final do fluxo
    return str(result)
