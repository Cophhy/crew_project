# content_creation_crew/tools/references_check.py

import re

class ReferencesCheckTool:
    def __init__(self):
        pass

    def check_references(self, text: str) -> bool:
        """
        Verifica se todas as referências no texto são links válidos para o Wikipedia.
        
        :param text: O texto completo que será verificado.
        :return: True se todas as referências forem do Wikipedia, False caso contrário.
        """
        # Regex para encontrar links no formato Markdown
        links = re.findall(r'\[.*?\]\((.*?)\)', text)

        # Verifica se cada link é do Wikipedia
        for link in links:
            if not link.startswith('https://en.wikipedia.org/wiki/'):
                print(f"Invalid reference found: {link}")
                return False

        # Se todas as referências forem do Wikipedia
        return True
