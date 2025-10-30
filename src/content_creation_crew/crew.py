# src/content_creation_crew/crew.py
from __future__ import annotations
from .schemas import CrewOutput


from pathlib import Path
from time import perf_counter
from datetime import datetime, timezone
from typing import Any, Dict, Optional

from crewai import Agent, Crew, Process, Task, LLM
from crewai.project import CrewBase, agent, crew, task

# Ferramentas Wikipedia (BaseTool do CrewAI)
from content_creation_crew.tools.wikipedia_tool import (
    WikipediaSearchTool,
    WikipediaFetchTool,
)

# Schemas Pydantic para o output tipado
from .schemas import CrewOutput


def _now_utc() -> datetime:
    return datetime.now(timezone.utc)


@CrewBase
class ContentCreationCrewCrew():
    """ContentCreationCrew crew"""

    # Caminhos de configuração (o CrewBase carrega e expõe como dict)
    agents_config = 'config/agents.yaml'
    tasks_config = 'config/tasks.yaml'

    def __init__(self) -> None:
        # Ajuste aqui o modelo Ollama que desejar (ex.: "ollama/mistral", "ollama/llama3.1", etc.)
        self.llm = LLM(
            model="ollama/mistral",
            base_url="http://localhost:11434",
        )

        # Instâncias de ferramentas (apenas Wikipedia neste exemplo)
        self.wiki_search = WikipediaSearchTool(lang="en", max_chars=1800)
        self.wiki_fetch = WikipediaFetchTool(lang="en", max_chars=6000)

    @agent
    def researcher(self) -> Agent:
        return Agent(
            config=self.agents_config['researcher'],
            llm=self.llm,
            tools=[self.wiki_search, self.wiki_fetch],  # apenas Wikipedia
            allow_delegation=False,
            verbose=True,
        )

    @agent
    def writer(self) -> Agent:
        return Agent(
            config=self.agents_config['writer'],
            llm=self.llm,
            tools=[],
            allow_delegation=False,
            verbose=True,
        )

    @agent
    def editor(self) -> Agent:
        return Agent(
            config=self.agents_config['editor'],
            llm=self.llm,
            tools=[],
            allow_delegation=False,
            verbose=True,
        )

    @task
    def research_task(self) -> Task:
        return Task(
            config=self.tasks_config['research_task'],
            agent=self.researcher(),
        )

    @task
    def writing_task(self) -> Task:
        return Task(
            config=self.tasks_config['writing_task'],
            agent=self.writer(),
            context=[self.research_task()],
        )

    @task
    def editing_task(self) -> Task:
        return Task(
            config=self.tasks_config['editing_task'],
            agent=self.editor(),
            context=[self.writing_task()],
        )

    @crew
    def crew(self) -> Crew:
        return Crew(
            agents=self.agents,
            tasks=self.tasks,
            process=Process.sequential,
            verbose=True,
        )


class ContentCreationCrewRunner:
    """
    Runner que executa a crew e devolve um CrewOutput (Pydantic).
    Use este runner no CLI e na API (FastAPI) para obter JSON tipado.
    """

    def __init__(self) -> None:
        self._crew_holder = ContentCreationCrewCrew()

    def crew(self) -> Crew:
        return self._crew_holder.crew()

    def run(self, **inputs: Dict[str, Any]) -> CrewOutput:
        out = CrewOutput(inputs=inputs)
        t0 = perf_counter()
        out.started_at = _now_utc()

        # Executa a crew de forma sequencial com os inputs da requisição
        result = self.crew().kickoff(inputs=inputs)

        out.finished_at = _now_utc()
        out.duration_seconds = perf_counter() - t0

        # Resultado final em Markdown (ou texto) vindo do CrewAI
        out.final_markdown = str(result) if result is not None else None

        # Se seu fluxo gerar um arquivo (ex.: "report.md"), exponha o caminho
        report = Path("report.md")
        if report.exists():
            out.output_file = str(report.resolve())

        # Caso você tenha métricas de uso, preencha aqui (opcional):
        # try:
        #     out.usage = self.crew().usage_metrics  # adapte conforme sua implementação
        # except Exception:
        #     pass

        return out
