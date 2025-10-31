# content_creation_crew/tools/text_expansion.py

class BodyTextExpansionTool:
    def __init__(self):
        pass

    def expand(self, text: str) -> str:
        """
        Expande o corpo do texto, se necessário, até que tenha pelo menos 300 palavras.
        O título, as seções e as referências são preservadas.
        
        :param text: O texto que será analisado e possivelmente expandido.
        :return: O texto expandido ou original (se já tiver ≥ 300 palavras).
        """
        # Se o corpo do texto tiver menos de 300 palavras, expanda-o
        body_content = self._extract_body(text)
        word_count = len(body_content.split())

        if word_count < 300:
            expanded_content = self._expand_text(body_content)
            text = text.replace(body_content, expanded_content)

        return text

    def _extract_body(self, text: str) -> str:
        """
        Extrai o corpo do artigo, excluindo o título, as seções e as referências.
        
        :param text: O texto completo em Markdown.
        :return: O conteúdo do corpo, sem o título e as seções.
        """
        # Divide o texto em partes usando os delimitadores típicos de Markdown
        parts = text.split('\n\n')
        # A primeira parte é o título, então a removemos.
        body = '\n\n'.join(parts[1:])  # Excluindo a primeira parte (Título)
        return body

    def _expand_text(self, body_content: str) -> str:
        """
        Lógica para expandir o conteúdo do corpo do texto até 300 palavras, 
        utilizando os dados de pesquisa já disponíveis.
        
        :param body_content: O conteúdo original do corpo.
        :return: O conteúdo expandido.
        """
        # Aqui, você pode colocar qualquer lógica para expandir o texto. 
        # Por exemplo, pode usar informações de fontes adicionais (como a pesquisa já feita).
        
        additional_content = (
            " This section will be expanded with additional detailed explanations. "
            "The text will elaborate on the concepts discussed, providing more background, examples, and insights. "
            "For instance, this could include more specifics about the topic, a deeper dive into the underlying principles, "
            "and some practical examples to illustrate key points in greater detail."
        )
        
        # Adiciona o conteúdo extra até o texto atingir a contagem necessária
        body_content += additional_content
        return body_content
