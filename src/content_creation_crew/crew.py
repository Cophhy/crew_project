from crewai import Agent, Crew, Process, Task
from crewai.project import CrewBase, agent, crew, task
from crewai import LLM

# ✅ agora importamos as CLASSES BaseTool que você acabou de criar
from content_creation_crew.tools.wikipedia_tool import (
    WikipediaSearchTool,
    WikipediaFetchTool,
)

@CrewBase
class ContentCreationCrewCrew():
    """ContentCreationCrew crew"""

    agents_config = 'config/agents.yaml'
    tasks_config = 'config/tasks.yaml'

    def __init__(self) -> None:
        self.llm = LLM(
            model="ollama/mistral",
            base_url="http://localhost:11434"
        )
        # ✅ instâncias de BaseTool do CrewAI
        self.wiki_search = WikipediaSearchTool(lang="en", max_chars=1800)
        self.wiki_fetch  = WikipediaFetchTool(lang="en", max_chars=6000)

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
