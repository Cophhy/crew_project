# src/content_creation_crew/crew.py
from __future__ import annotations

from pathlib import Path
from time import perf_counter
from datetime import datetime, timezone
from typing import Any, Dict
import re

from crewai import Agent, Crew, Process, Task, LLM
from crewai.project import CrewBase, agent, crew, task

from content_creation_crew.tools.wikipedia_tool import (
    WikipediaSearchTool,
    WikipediaFetchTool,
)

from .schemas import (
    CrewOutput,
    TaskResult,
    ResearchOutput,
    WritingOutput,
    EditOutput,
)

def _now_utc() -> datetime:
    return datetime.now(timezone.utc)

_CODE_FENCE_RE = re.compile(r"```(?:markdown|md)?\s*([\s\S]*?)```", re.IGNORECASE)

def _strip_code_fences(text: str) -> str:
    if not isinstance(text, str):
        return ""
    cleaned = re.sub(r"^\s*(Final Output:|Agent Final Answer:)\s*", "", text, flags=re.IGNORECASE)
    m = _CODE_FENCE_RE.search(cleaned)
    if m:
        return m.group(1).strip()
    return cleaned.strip()

def _choose_final_md(tasks, raw_text: str) -> str:
    for tr in reversed(tasks):
        if tr.pydantic_model == "EditOutput" and tr.pydantic_payload:
            md = tr.pydantic_payload.get("markdown")
            if md:
                return md.strip()
    for tr in reversed(tasks):
        if tr.pydantic_model == "WritingOutput" and tr.pydantic_payload:
            md = tr.pydantic_payload.get("markdown")
            if md:
                return md.strip()
    return _strip_code_fences(raw_text)


@CrewBase
class ContentCreationCrewCrew():
    """ContentCreationCrew crew"""

    agents_config = 'config/agents.yaml'
    tasks_config = 'config/tasks.yaml'

    def __init__(self) -> None:
        self.llm = LLM(
            model="ollama/mistral",
            base_url="http://localhost:11434",
        )
        self.wiki_search = WikipediaSearchTool(lang="en", max_chars=1800)
        self.wiki_fetch = WikipediaFetchTool(lang="en", max_chars=6000)

    @agent
    def researcher(self) -> Agent:
        return Agent(
            config=self.agents_config['researcher'],
            llm=self.llm,
            tools=[self.wiki_search, self.wiki_fetch],
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

    # ======= ALTERADO: sem "config=", passamos description/expected_output =======
    @task
    def research_task(self) -> Task:
        cfg = self.tasks_config['research_task']
        return Task(
            description=cfg['description'],
            expected_output=cfg['expected_output'],
            agent=self.researcher(),
            output_pydantic=ResearchOutput,
        )

    @task
    def writing_task(self) -> Task:
        cfg = self.tasks_config['writing_task']
        return Task(
            description=cfg['description'],
            expected_output=cfg['expected_output'],
            agent=self.writer(),
            context=[self.research_task()],
            output_pydantic=WritingOutput,
        )

    @task
    def editing_task(self) -> Task:
        cfg = self.tasks_config['editing_task']
        return Task(
            description=cfg['description'],
            expected_output=cfg['expected_output'],
            agent=self.editor(),
            context=[self.writing_task()],
            output_pydantic=EditOutput,
        )
    # ===========================================================================

    @crew
    def crew(self) -> Crew:
        return Crew(
            agents=self.agents,
            tasks=self.tasks,
            process=Process.sequential,
            verbose=True,
        )


class ContentCreationCrewRunner:
    def __init__(self) -> None:
        self._crew_holder = ContentCreationCrewCrew()

    def crew(self) -> Crew:
        return self._crew_holder.crew()

    def run(self, **inputs: Dict[str, Any]) -> CrewOutput:
        out = CrewOutput(inputs=inputs)
        t0 = perf_counter()
        out.started_at = _now_utc()

        crew_inst = self.crew()
        task_objs = getattr(crew_inst, "tasks", []) or getattr(self._crew_holder, "tasks", [])

        raw_result = crew_inst.kickoff(inputs=inputs)
        raw_text = str(raw_result) if raw_result is not None else ""

        out.finished_at = _now_utc()
        out.duration_seconds = perf_counter() - t0

        out.tasks = []
        for t in task_objs:
            tr = TaskResult(
                name=(getattr(t, "description", None) or getattr(t, "name", "") or "").strip()[:200],
                status="success",
            )
            to = getattr(t, "output", None)
            try:
                if to is not None:
                    p_model = getattr(to, "pydantic", None)
                    if p_model is not None:
                        tr.pydantic_model = p_model.__class__.__name__
                        tr.pydantic_payload = (
                            p_model.model_dump() if hasattr(p_model, "model_dump") else p_model.dict()
                        )
                    json_dict = getattr(to, "json_dict", None)
                    if isinstance(json_dict, dict):
                        tr.json_dict = json_dict
                    raw = getattr(to, "raw", None)
                    if isinstance(raw, str):
                        tr.raw = raw
                        if raw.lstrip().startswith("#"):
                            tr.output_markdown = _strip_code_fences(raw)
            except Exception as e:
                tr.status = "error"
                tr.error_message = str(e)

            out.tasks.append(tr)

        out.final_markdown = _choose_final_md(out.tasks, raw_text)

        report = Path("report.md")
        if report.exists():
            out.output_file = str(report.resolve())

        return out
