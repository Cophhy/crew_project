from crewai import Agent, Crew, Process, Task
from crewai.project import CrewBase, agent, crew, task
from crewai import LLM
from content_creation_crew.tools.wordcount_tool import BodyWordCountTool  
from content_creation_crew.tools.wikipedia_tool import WikipediaSearchTool, WikipediaFetchTool  

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
        self.word_count_tool = BodyWordCountTool()  # Instância do tool de contagem de palavras

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
            tools=[self.word_count_tool],  # Adiciona a ferramenta de contagem de palavras
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

    def ensure_min_word_count(self, markdown: str) -> str:
        """
        Verifica se o número de palavras do corpo do artigo é pelo menos 300.
        Se não for, solicita ao escritor que adicione mais conteúdo.
        """
        # Remove a introdução e qualquer texto inicial irrelevante
        content_body = self.word_count_tool.extract_body(markdown)
        word_count = self.word_count_tool.count_words(content_body)
        
        if word_count < 300:
            return f"O artigo tem apenas {word_count} palavras. Adicione mais conteúdo para atingir pelo menos 300 palavras."
        return f"O artigo tem {word_count} palavras, atendendo ao requisito mínimo de 300 palavras."
