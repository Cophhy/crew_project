from crewai import Agent, Crew, Process, Task, BaseTool  # Importando BaseTool
from crewai.project import CrewBase, agent, crew, task
from crewai import LLM

# ✅ suas tools existentes (Wikipedia)
from content_creation_crew.tools.wikipedia_tool import (
    WikipediaSearchTool,
    WikipediaFetchTool,
)

# 🔹 ADICIONADO: tool de contagem de palavras do corpo
from content_creation_crew.tools.wordcount import BodyWordCountTool  

# 🔹 ADICIONADO: ferramentas criadas
from content_creation_crew.tools.text_expansion import BodyTextExpansionTool  # <— ADICIONADO
from content_creation_crew.tools.references_check import ReferencesCheckTool  # <— ADICIONADO

# 🔹 ADICIONADO: esquema Pydantic para saída estruturada
from content_creation_crew.schemas import ResearchReport  # <— ADICIONADO


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
        self.wiki_search = WikipediaSearchTool(lang="en", max_chars=1800)
        self.wiki_fetch = WikipediaFetchTool(lang="en", max_chars=6000)
        self.body_wc = BodyWordCountTool()
        self.text_expansion = BodyTextExpansionTool()  # A ferramenta de expansão
        self.references_check = ReferencesCheckTool()  # A ferramenta de validação de referências

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
            tools=[],  # mantém sem tools
            allow_delegation=False,
            verbose=True,
        )

    @agent
    def editor(self) -> Agent:
        return Agent(
            config=self.agents_config['editor'],
            llm=self.llm,
            tools=[self.body_wc, self.references_check],  # Agora inclui o ReferencesCheckTool
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
            description=("Use the `body_word_count` tool to compute the BODY word count of the Markdown article below "
                         "(exclude Title, TL;DR, all headings, and the 'References (Wikipedia)' section). "
                         "If the BODY has 300 words or more, return the article EXACTLY as-is. "
                         "If the BODY has fewer than 300 words, expand ONLY the BODY to reach at least 300 words, "
                         "preserving the existing Title, all headings, and keeping the 'References (Wikipedia)' list "
                         "identical (same entries, same URLs). Do NOT add new links or sources; only elaborate using "
                         "the already-present research facts and explanations."),
            agent=self.editor(),
            context=[self.editing_task()],
            expected_output="A Markdown article whose BODY is ≥ 300 words (or unchanged if already ≥ 300).",
            markdown=True,
            output_file="report.md",
            output_pydantic=ResearchReport,
        )

    @crew
    def crew(self) -> Crew:
        return Crew(
            agents=self.agents,
            tasks=self.tasks,        # a enforce_min_words_task vem por último (sequencial)
            process=Process.sequential,
            verbose=True,
        )

# Funções de ferramentas auxiliares

class BodyTextExpansionTool(BaseTool):
    """
    Expande o corpo do artigo se ele tiver menos de 300 palavras,
    mantendo o título, cabeçalhos e referências intactos.
    """
    
    def run(self, markdown: str) -> str:
        # Contar as palavras no corpo do artigo (excluindo título, cabeçalhos e referências)
        body_word_count = self.body_word_count(markdown)
        
        # Se o corpo tiver menos de 300 palavras, adicionar mais conteúdo.
        if body_word_count < 300:
            # Lógica de expansão do corpo, baseado no conteúdo existente
            expanded_body = self.expand_body(markdown)
            return expanded_body
        
        return markdown  # Se já tem mais de 300 palavras, retorna sem mudanças

    def body_word_count(self, markdown: str) -> int:
        # Função que simula a contagem de palavras do corpo
        return len(markdown.split())

    def expand_body(self, markdown: str) -> str:
        # Lógica para expandir o corpo com conteúdo adicional
        body_start = markdown.find("## Introduction") + len("## Introduction")
        body_end = markdown.find("## Conclusion")
        body_content = markdown[body_start:body_end]

        additional_content = "\n\n# Expanding the Theory\nHere are more details on String Theory based on the research."

        expanded_markdown = markdown[:body_end] + additional_content + markdown[body_end:]

        return expanded_markdown


class ReferencesCheckTool(BaseTool):
    """
    Verifica se as referências estão corretas, garantindo que todas sejam da Wikipedia.
    """
    
    def run(self, markdown: str) -> str:
        references_start = markdown.find("## References (Wikipedia)") + len("## References (Wikipedia)")
        references_content = markdown[references_start:]

        valid_references = []
        for line in references_content.split("\n"):
            if "wikipedia.org" in line:
                valid_references.append(line.strip())
        
        corrected_references = "\n".join(valid_references)

        return markdown[:references_start] + corrected_references


class ResearchReport(BaseModel):
    title: str
    tl_dr: str
    introduction: str
    sections: List[str]
    conclusion: str
    references: List[str]
    
    class Config:
        orm_mode = True
