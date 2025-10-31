from crewai import Agent, Crew, Process, Task
from crewai.project import CrewBase, agent, crew, task
from crewai import LLM

from content_creation_crew.tools.wikipedia_tool import (
    WikipediaSearchTool,
    WikipediaFetchTool,
)

from content_creation_crew.tools.wordcount import BodyWordCountTool


@CrewBase
class ContentCreationCrewCrew():
    """Classe base para o conteúdo da criação de artigos, representando o time de trabalho do CrewAI."""

    agents_config = 'config/agents.yaml'  
    tasks_config = 'config/tasks.yaml'   
    def __init__(self) -> None:
        """
        Inicializa as ferramentas, o modelo LLM, e as instâncias das ferramentas de pesquisa, 
        recuperação e contagem de palavras.
        """
        self.llm = LLM(
            model="ollama/mistral",  # Nome do modelo de linguagem
            base_url="http://localhost:11434"  # URL do servidor local do modelo
        )
        
        self.wiki_search = WikipediaSearchTool(lang="en", max_chars=1800)
        self.wiki_fetch  = WikipediaFetchTool(lang="en", max_chars=6000)
        
        #contagem de palavras
        self.body_wc = BodyWordCountTool() 

    @agent
    def researcher(self) -> Agent:
        return Agent(
            config=self.agents_config['researcher'],
            llm=self.llm,
            tools=[self.wiki_search, self.wiki_fetch],  # apenas Wikipedia
            allow_delegation=False,
            verbose=True,
            max_searches=3,  
            max_search_duration=70,  
        )


    @agent
    def writer(self) -> Agent:
        """
        Cria o agente de escrita que irá redigir o artigo com base nas informações coletadas.
        Este agente não usa ferramentas, pois deve se concentrar na escrita.
        """
        return Agent(
            config=self.agents_config['writer'], 
            llm=self.llm,  
            tools=[],  
            allow_delegation=False,
            verbose=True,
        )

    @agent
    def editor(self) -> Agent:
        """
        Cria o agente de edição que irá revisar o artigo, focando na contagem de palavras do corpo do texto.
        Esse agente utiliza a ferramenta de contagem de palavras.
        """
        return Agent(
            config=self.agents_config['editor'],  
            llm=self.llm,  
            tools=[self.body_wc],  
            allow_delegation=False,
            verbose=True,
        )

    @task
    def research_task(self) -> Task:
        """
        Tarefa de pesquisa. O agente de pesquisa realiza buscas na Wikipedia.
        Essa tarefa será executada pelo agente 'researcher'.
        """
        return Task(
            config=self.tasks_config['research_task'],  
            agent=self.researcher(),  
        )

    @task
    def writing_task(self) -> Task:
        """
        Tarefa de escrita. O agente 'writer' escreve o artigo com base nas pesquisas realizadas.
        Essa tarefa depende da 'research_task' para ser executada.
        """
        return Task(
            config=self.tasks_config['writing_task'],  
            agent=self.writer(),  
            context=[self.research_task()],  
        )

    @task
    def editing_task(self) -> Task:
        """
        Tarefa de edição. O agente 'editor' revisa o artigo com foco na contagem de palavras.
        Essa tarefa depende da 'writing_task' para ser executada.
        """
        return Task(
            config=self.tasks_config['editing_task'],  
            agent=self.editor(), 
            context=[self.writing_task()], 
        )

    # garantia de ≥ 300 palavras
    @task
    def enforce_min_words_task(self) -> Task:
        """
        Tarefa para garantir que o corpo do artigo tenha pelo menos 300 palavras. 
        Caso o corpo tenha menos, o agente de edição irá expandi-lo sem alterar título, cabeçalhos e referências.
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
            agent=self.editor(),  
            context=[self.editing_task()], 
            expected_output="A Markdown article whose BODY is ≥ 300 words (or unchanged if already ≥ 300).", 
        )

    @crew
    def crew(self) -> Crew:
        """
        Cria o time de trabalho (Crew) com os agentes e tarefas configurados. 
        O processo será sequencial, garantindo que as tarefas sejam executadas uma após a outra.
        """
        return Crew(
            agents=self.agents,  
            tasks=self.tasks, 
            process=Process.sequential,  
            verbose=True, 
        )
