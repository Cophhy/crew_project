# src/content_creation_crew/crew.py
from __future__ import annotations

import os
from crewai import Agent, Crew, Process, Task, LLM
from crewai.project import CrewBase, agent, crew, task

# Tools (BaseTool subclasses)
from content_creation_crew.tools.wikipedia_tool import (
    WikipediaSearchTool,
    WikipediaFetchTool,
)

# Pydantic schemas (para output_json)
from content_creation_crew.schemas.outline import OutlineModel
from content_creation_crew.schemas.factcheck import FactCheckReport
from content_creation_crew.schemas.article import ArticleDraft  # backend valida depois em ArticleModel


@CrewBase
class ContentCreationCrewCrew:
    """
    ContentCreationCrew: pipeline de pesquisa -> planejamento -> escrita -> checagem -> edição
    - Usa Ollama via crewai.LLM (model/base_url configuráveis por env)
    - Tools: wikipedia_search / wikipedia_fetch (MediaWiki API)
    - Saídas estruturadas: OutlineModel, ArticleDraft, FactCheckReport
    """

    # mapeamentos para os YAMLs
    agents_config = "config/agents.yaml"
    tasks_config = "config/tasks.yaml"

    def __init__(self) -> None:
        # Config do LLM (padrões seguros se envs não existirem)
        model_id = os.getenv("MODEL_ID", "ollama/mistral")
        base_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")

        self.llm = LLM(
            model=model_id,
            base_url=base_url,
        )

        # Instâncias das ferramentas (sem kwargs extras)
        self.wiki_search = WikipediaSearchTool()
        self.wiki_fetch = WikipediaFetchTool()

    # ---------------- Agents ----------------
    @agent
    def researcher(self) -> Agent:
        # Pesquisa exclusivamente via Wikipedia API
        return Agent(
            config=self.agents_config["researcher"],
            llm=self.llm,
            tools=[self.wiki_search, self.wiki_fetch],
            allow_delegation=False,
            verbose=True,
        )

    @agent
    def content_planner(self) -> Agent:
        # Planeja a estrutura do artigo (outline)
        return Agent(
            config=self.agents_config["content_planner"],
            llm=self.llm,
            tools=[],
            allow_delegation=False,
            verbose=True,
        )

    @agent
    def writer(self) -> Agent:
        # Escreve o rascunho em Markdown, retornando JSON ArticleDraft
        return Agent(
            config=self.agents_config["writer"],
            llm=self.llm,
            tools=[],
            allow_delegation=False,
            verbose=True,
        )

    @agent
    def fact_checker(self) -> Agent:
        # Verifica afirmações usando APENAS as URLs de Wikipedia (mesmas tools do pesquisador)
        return Agent(
            config=self.agents_config["fact_checker"],
            llm=self.llm,
            tools=[self.wiki_search, self.wiki_fetch],
            allow_delegation=False,
            verbose=True,
        )

    @agent
    def copy_editor(self) -> Agent:
        # Edição de clareza, gramática e consistência de estilo
        return Agent(
            config=self.agents_config["copy_editor"],
            llm=self.llm,
            tools=[],
            allow_delegation=False,
            verbose=True,
        )

    # ---------------- Tasks ----------------
    @task
    def research_task(self) -> Task:
        # Pesquisador entrega bullets + referências Wikipedia
        return Task(
            config=self.tasks_config["research_task"],
            agent=self.researcher(),
        )

    @task
    def planning_task(self) -> Task:
        # Planejador produz OutlineModel usando SOMENTE a pesquisa
        return Task(
            config=self.tasks_config["planning_task"],
            agent=self.content_planner(),
            context=[self.research_task()],
            output_json=OutlineModel,
        )

    @task
    def writing_task(self) -> Task:
        # Escritor gera ArticleDraft (≥ 300 palavras), só com fontes do planner/pesquisa
        return Task(
            config=self.tasks_config["writing_task"],
            agent=self.writer(),
            context=[self.research_task(), self.planning_task()],
            output_json=ArticleDraft,
        )

    @task
    def fact_check_task(self) -> Task:
        # Verificador emite FactCheckReport
        return Task(
            config=self.tasks_config["fact_check_task"],
            agent=self.fact_checker(),
            context=[self.research_task(), self.writing_task()],
            output_json=FactCheckReport,
        )

    @task
    def editing_task(self) -> Task:
        # Editor aplica ajustes finais e retorna ArticleDraft final (backend valida >= 300)
        return Task(
            config=self.tasks_config["editing_task"],
            agent=self.copy_editor(),
            context=[self.writing_task(), self.fact_check_task()],
            output_json=ArticleDraft,
        )

    # ---------------- Crew ----------------
    @crew
    def crew(self) -> Crew:
        return Crew(
            agents=[
                self.researcher(),
                self.content_planner(),
                self.writer(),
                self.fact_checker(),
                self.copy_editor(),
            ],
            tasks=[
                self.research_task(),
                self.planning_task(),
                self.writing_task(),
                self.fact_check_task(),
                self.editing_task(),
            ],
            process=Process.sequential,
            verbose=True,
        )
