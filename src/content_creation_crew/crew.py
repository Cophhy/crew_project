# src/content_creation_crew/crew.py
from __future__ import annotations

import os
from crewai import Agent, Crew, Process, Task, LLM
from crewai.project import CrewBase, agent, crew, task

# Tools
from content_creation_crew.tools.wikipedia_tool import (
    WikipediaSearchTool,
    WikipediaFetchTool,
)

# Pydantic schemas used for structured outputs
from content_creation_crew.schemas.article import ArticleDraft
from content_creation_crew.schemas.factcheck import FactCheckReport
# NOTE: Content planner is disabled for now, so OutlineModel is not used.
# from content_creation_crew.schemas.outline import OutlineModel


@CrewBase
class ContentCreationCrewCrew:
    """
    Research -> Write -> Fact-check -> Edit
    - LLM via Ollama (MODEL_ID / OLLAMA_BASE_URL envs)
    - Wikipedia tools only (search/fetch)
    - Logs are written to crew.log for live tailing
    """

    agents_config = "config/agents.yaml"
    tasks_config = "config/tasks.yaml"

    def __init__(self) -> None:
        model_id = os.getenv("MODEL_ID", "ollama/mistral")
        base_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")

        self.llm = LLM(model=model_id, base_url=base_url)

        self.wiki_search = WikipediaSearchTool()
        self.wiki_fetch = WikipediaFetchTool()

    # ---------------- Agents ----------------
    @agent
    def researcher(self) -> Agent:
        return Agent(
            config=self.agents_config["researcher"],
            llm=self.llm,
            tools=[self.wiki_search, self.wiki_fetch],
            allow_delegation=False,
            verbose=True,
        )

    # Content planner disabled for now
    # @agent
    # def content_planner(self) -> Agent:
    #     return Agent(
    #         config=self.agents_config["content_planner"],
    #         llm=self.llm,
    #         tools=[],
    #         allow_delegation=False,
    #         verbose=True,
    #     )

    @agent
    def writer(self) -> Agent:
        return Agent(
            config=self.agents_config["writer"],
            llm=self.llm,
            tools=[],
            allow_delegation=False,
            verbose=True,
        )

    @agent
    def fact_checker(self) -> Agent:
        return Agent(
            config=self.agents_config["fact_checker"],
            llm=self.llm,
            tools=[self.wiki_search, self.wiki_fetch],
            allow_delegation=False,
            verbose=True,
        )

    @agent
    def copy_editor(self) -> Agent:
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
        return Task(
            config=self.tasks_config["research_task"],
            agent=self.researcher(),
        )

    # Content planner disabled for now
    # @task
    # def planning_task(self) -> Task:
    #     return Task(
    #         config=self.tasks_config["planning_task"],
    #         agent=self.content_planner(),
    #         context=[self.research_task()],
    #         output_json=OutlineModel,
    #     )

    @task
    def writing_task(self) -> Task:
        # writer now uses ONLY the research context (planner is disabled)
        return Task(
            config=self.tasks_config["writing_task"],
            agent=self.writer(),
            context=[self.research_task()],
            output_json=ArticleDraft,
        )

    @task
    def fact_check_task(self) -> Task:
        return Task(
            config=self.tasks_config["fact_check_task"],
            agent=self.fact_checker(),
            context=[self.research_task(), self.writing_task()],
            output_json=FactCheckReport,
        )

    @task
    def editing_task(self) -> Task:
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
                # self.content_planner(),  # disabled
                self.writer(),
                self.fact_checker(),
                self.copy_editor(),
            ],
            tasks=[
                self.research_task(),
                # self.planning_task(),  # disabled
                self.writing_task(),
                self.fact_check_task(),
                self.editing_task(),
            ],
            process=Process.sequential,
            verbose=True,
            # <<< important: write live agent/tool logs here >>>
            output_log_file="crew.json",
            # You can also enable tracing dashboards later if you want:
            # tracing=True  # requires proper tracing setup; see docs
        )
