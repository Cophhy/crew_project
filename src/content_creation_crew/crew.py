from crewai import Agent, Crew, Process, Task
from crewai.project import CrewBase, agent, crew, task
from crewai import LLM
from content_creation_crew.tools.wordcount_tool import BodyWordCountTool  
from content_creation_crew.tools.wikipedia_tool import WikipediaSearchTool, WikipediaFetchTool  

@CrewBase
class ContentCreationCrewCrew():
    """ContentCreationCrew crew XD crewcrew"""

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
            allow_delegation=False, #nao permite delegar para outro agente
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

    @task
    def enforce_min_words_task(self) -> Task:
        """
        Esta task usa a tool `body_word_count` para medir o corpo do artigo
        (exclui Title, TL;DR, headings e a seção "References (Wikipedia)").
        Se < 300, expande SOMENTE o corpo até ≥ 300 palavras, mantendo título,
        headings e a lista de referências/URLs exatamente como estão.
        """
        return Task(
            description=(
                "Use the `body_word_count` tool to compute the BODY word count of the Markdown article below "
                "(exclude Title, TL;DR, all headings, and the 'References (Wikipedia)' section). "
                "If the BODY has 300 words or more, return the article EXACTLY as-is. "
                "If the BODY has fewer than 300 words, expand ONLY the BODY to reach at least 300 words, "
                "preserving the existing Title, all headings, and keeping the 'References (Wikipedia)' list "
                "identical (same entries, same URLs). Do NOT add new links or sources; only elaborate using "
                "the already-present research facts and explanations."
            ),
            agent=self.editor(),                 # o editor já tem a tool
            context=[self.editing_task()],       # pega o artigo já editado
            expected_output="A Markdown article whose BODY is ≥ 300 words (or unchanged if already ≥ 300).",
        )

    @crew
    def crew(self) -> Crew:
        return Crew(
            agents=self.agents,
            tasks=self.tasks,        # a enforce_min_words_task vem por último (sequencial)
            process=Process.sequential,
            verbose=True,
        )
