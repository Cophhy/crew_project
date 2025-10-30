# src/content_creation_crew/tools/wordcount.py

import re

# Tenta importar BaseTool do pacote certo (varia por versão)
try:
    from crewai_tools import BaseTool  # pacote "crewai-tools"
except Exception:  # fallback para instalações antigas
    try:
        from crewai.tools import BaseTool  # algumas versões expõem aqui
    except Exception as e:  # último recurso: erro claro
        raise ImportError(
            "Não foi possível importar BaseTool. "
            "Instale 'crewai-tools' (pip install crewai-tools) "
            "ou atualize o CrewAI."
        ) from e


# ---------- Funções utilitárias (extração do CORPO e contagem) ----------
_HEADING_PREFIXES = ("#", "##", "###", "####", "#####", "######")

_WORD_RE = re.compile(r"[A-Za-zÀ-ÖØ-öø-ÿ0-9_]+(?:['\-][A-Za-zÀ-ÖØ-öø-ÿ0-9_]+)?")

def _is_heading(line: str) -> bool:
    s = line.strip()
    return any(s.startswith(p) for p in _HEADING_PREFIXES)

def extract_body(markdown: str) -> str:
    """
    Remove: título, TL;DR (seção completa), TODAS as linhas de heading
    e tudo a partir de '## References' (inclusive).
    """
    lines = markdown.splitlines()
    out = []
    in_tldr = False

    for raw in lines:
        line = raw.rstrip()
        low = line.strip().lower()

        # corta tudo a partir de '## references'
        if low.startswith("## references"):
            break

        # TL;DR começa em '## TL;DR' e termina no próximo heading '## '
        if low.startswith("## tl;dr"):
            in_tldr = True
            continue
        if in_tldr and line.strip().startswith("## "):
            in_tldr = False
            # não inclui o heading; segue para próxima linha
            continue

        # remove todas as linhas de heading do count
        if _is_heading(line):
            continue

        if not in_tldr:
            out.append(line)

    return "\n".join(out).strip()

def count_words(text: str) -> int:
    return len(_WORD_RE.findall(text))

def body_word_count(markdown: str) -> int:
    return count_words(extract_body(markdown))


# ---------- Tool ----------
class BodyWordCountTool(BaseTool):
    """
    Tool chamada 'body_word_count' que recebe o artigo Markdown completo
    e retorna APENAS o número inteiro de palavras do CORPO (como string).
    """
    name: str = "body_word_count"
    description: str = (
        "Compute the BODY word count of a Markdown article. "
        "Exclude Title, TL;DR section, all headings, and the 'References (Wikipedia)' section. "
        "Pass the full Markdown in the 'markdown' argument. "
        "Returns the word count as a stringified integer."
    )

    # O CrewAI mapeia pelo nome do parâmetro; mantemos simples
    def _run(self, markdown: str) -> str:  # type: ignore[override]
        try:
            return str(body_word_count(markdown))
        except Exception as e:
            # Resposta textual ajuda o LLM a entender falhas
            return f"ERROR: {e}"
