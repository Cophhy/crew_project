# src/content_creation_crew/crew.py
from crewai import Agent, Crew, LLM
from typing import Dict

LANG_SYSTEM = {
    "pt": "Detecte o idioma da última mensagem do usuário e responda no mesmo idioma. Se for português, responda em PT-BR claro e natural.",
    "en": "Detect the user's language and reply in the same language. If English, use natural, concise tone."
}

def build_llm(model_id: str) -> LLM:
    # Use Ollama local
    return LLM(
        model=f"ollama/{model_id}",          # p.ex. "ollama/llama3.1:8b-instruct"
        base_url="http://localhost:11434",   # Ollama local
        temperature=0.3
    )

def build_agents(agents_config: Dict, llm: LLM, lang: str):
    # exemplo para dois agentes típicos do template; ajuste nomes conforme seu agents.yaml
    researcher = Agent(
        config=agents_config["researcher"],  # existente no teu YAML
        llm=llm,
        verbose=True,
        system_prompt=LANG_SYSTEM.get(lang, LANG_SYSTEM["en"])
    )
    writer = Agent(
        config=agents_config["writer"],
        llm=llm,
        verbose=True,
        system_prompt=LANG_SYSTEM.get(lang, LANG_SYSTEM["en"])
    )
    return researcher, writer

def build_crew(agents_config: Dict, tasks_config: Dict, llm: LLM, lang: str) -> Crew:
    researcher, writer = build_agents(agents_config, llm, lang)
    # mapeie tasks do teu tasks.yaml
    # ex.: tasks_config["research_topic"], tasks_config["compose_article"]
    crew = Crew(
        agents=[researcher, writer],
        tasks=[  # ligue as tasks conforme seu YAML
            tasks_config["research_topic"].copy(update={"agent": researcher}),
            tasks_config["compose_article"].copy(update={"agent": writer}),
        ],
        verbose=True
    )
    return crew
