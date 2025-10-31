
# Content Creation Crew Project

## Descrição do Projeto

O **Content Creation Crew** é um projeto que utiliza o **CrewAI** para criar e gerenciar agentes responsáveis pela criação de conteúdo. O objetivo do projeto é permitir que um conjunto de agentes (pesquisadores, escritores e editores) trabalhem juntos para gerar artigos e outros tipos de conteúdo, baseados em informações verificáveis do **Wikipedia**.

### Funcionalidades

O sistema oferece as seguintes funcionalidades:

- **Pesquisa no Wikipedia**: Permite obter informações sobre um tópico usando a API oficial do Wikipedia.
- **Criação de Conteúdo**: Gera conteúdo em formato Markdown com base nas informações coletadas.
- **Edição de Conteúdo**: Revisa e edita o conteúdo gerado, garantindo a qualidade e a consistência das informações.

### Agentes

O projeto é composto por três agentes principais:

1. **Pesquisador (Researcher)**: Este agente pesquisa o tópico fornecido no **Wikipedia**, coleta fatos verificáveis e URLs correspondentes.
2. **Escritor (Writer)**: Com base nas informações coletadas pelo pesquisador, o escritor cria um conteúdo claro e coeso, estruturado em Markdown.
3. **Editor**: O editor revisa o conteúdo gerado pelo escritor, garantindo que o artigo esteja coeso, preciso e com referências verificáveis.

O fluxo de execução dos agentes é **sequencial**, com cada agente realizando sua função em ordem.

## Estrutura do Código

### 1. **`api/`**:
Contém a lógica da **API**, que expõe os serviços para interação com o sistema. Isso permite que o conteúdo seja gerado, consultado e modificado.

- **`api.app.main:app`**: Este é o ponto de entrada para o servidor da API, que deve ser executado com o **Uvicorn**.

### 2. **`web/`**:
Contém o **front-end** do projeto, incluindo os arquivos da interface do usuário. A interface permite interagir com os agentes e visualizar os resultados da criação de conteúdo.

### 3. **`crew.py`**:
Define a **Crew** de criação de conteúdo, configurando os agentes e as tarefas. A classe `ContentCreationCrewCrew` orquestra as interações entre os agentes, realizando as etapas de pesquisa, escrita e edição.

### 4. **`tools/`**:
Contém as ferramentas utilizadas pelos agentes, responsáveis por interagir com a API do Wikipedia e realizar tarefas específicas, como pesquisa e extração de conteúdo.

- **`WikipediaSearchTool`**: Ferramenta para realizar buscas no Wikipedia.
- **`WikipediaFetchTool`**: Ferramenta para buscar conteúdo detalhado de uma página ou seção específica do Wikipedia.
- **`BodyWordCountTool`**: Ferramenta para contar palavras no conteúdo gerado.

### 5. **`agents.yaml`** e **`tasks.yaml`**:
Arquivos de configuração que definem as propriedades dos **agentes** e das **tarefas**. O `agents.yaml` especifica os **papéis** e **objetivos** de cada agente, enquanto o `tasks.yaml` descreve as **tarefas** que os agentes executam (como pesquisa, escrita e edição).

### 6. **`models.py`**:
Define os **modelos Pydantic** usados para validar as entradas e saídas dos agentes. Eles garantem que os dados estejam em conformidade com o formato esperado antes de serem processados pelos agentes.

## Como Usar o Projeto

### 1. **Instalação de Dependências (Back-End)**

O projeto utiliza o **`pyproject.toml`** para gerenciar as dependências no back-end. Siga os passos abaixo para instalar as dependências:

1. **Crie um ambiente virtual** para o projeto (recomendado para isolar as dependências):

   ```bash
   python -m venv venv
   ```

2. **Ative o ambiente virtual**:

   - No **Windows**:

     ```bash
     .env\Scriptsctivate
     ```

   - No **Linux/Mac**:

     ```bash
     source venv/bin/activate
     ```

3. **Instale as dependências do back-end**:

   Com o ambiente virtual ativado, instale as dependências do projeto usando o **Poetry**:

   ```bash
   poetry install
   ```

4. **Carregue as variáveis de ambiente**:

   Certifique-se de que o arquivo `.env` contém as variáveis necessárias, como `APP_UA_NAME` e `WIKI_CONTACT`, que são utilizadas para configurar o cabeçalho de User-Agent das requisições.

   Exemplo de um arquivo `.env`:

   ```plaintext
   APP_UA_NAME=ContentCreationCrew/0.1
   WIKI_CONTACT=https://github.com/Cophhy/crew_project
   ```

### 2. **Instalação de Dependências (Front-End)**

O front-end do projeto utiliza o **npm**. Para configurar o front-end, siga os passos abaixo:

1. **Navegue até a pasta `web/`**:

   ```bash
   cd web
   ```

2. **Instale as dependências do front-end com o npm**:

   ```bash
   npm install
   ```

### 3. **Executando o Projeto**

Agora que as dependências estão instaladas, você pode iniciar tanto o **back-end** quanto o **front-end** do projeto.

1. **Inicie o Front-End**:

   Na pasta `web/`, execute o comando:

   ```bash
   npm run dev
   ```

   Isso iniciará o **servidor de desenvolvimento** para o front-end, permitindo que você interaja com a interface do usuário no navegador.

2. **Inicie o Back-End (API)**:

   Para iniciar o back-end, na raiz do projeto, execute o comando:

   ```bash
   uvicorn api.app.main:app --reload --reload-dir api --reload-dir src
   ```

   Isso iniciará o servidor **Uvicorn** para o back-end da API, com **hot reload**.


## Estrutura de Agentes e Tarefas

### **Agentes**:

- **Pesquisador** (`researcher`): Busca dados no **Wikipedia** sobre o tópico.
- **Escritor** (`writer`): Cria o conteúdo em **Markdown** com base nas informações coletadas.
- **Editor** (`editor`): Revisa o conteúdo gerado, garantindo clareza e consistência.

### **Tarefas**:

- **`research_task`**: Tarefa do **pesquisador** que realiza a busca no Wikipedia.
- **`writing_task`**: Tarefa do **escritor** que cria o conteúdo em Markdown.
- **`editing_task`**: Tarefa do **editor** que revisa o conteúdo gerado.

## Futuras Melhorias

O projeto possui várias possibilidades de melhorias, incluindo:

- **Adicionar Pydantic na saída dos agentes**: Para garantir uma maior consistência e validação nas saídas dos agentes.
- **Adicionar um agente especializado para revisão de fatos e veracidade**: Para garantir que as informações fornecidas sejam precisas e verificadas.
- **Melhorar suporte para perguntas em português**: Para tornar o sistema mais acessível e funcional em múltiplos idiomas, especialmente o português.

