\# Autonomous AI Codebase Engineering Agent



A LangGraph-based autonomous AI agent that understands and analyzes software codebases using Retrieval-Augmented Generation (RAG).



The system ingests a codebase, converts source files into searchable chunks, generates vector embeddings, stores them in Qdrant, retrieves relevant code based on natural-language questions, analyzes the retrieved context, generates an answer, and validates the answer against the retrieved source code.



\## Architecture



```text

User Question

&#x20;     ↓

Question Analyzer

&#x20;     ↓

Route Decision

&#x20;     ↓

Codebase Retrieval

&#x20;     ↓

Qdrant Vector Search

&#x20;     ↓

Relevance Check

&#x20;     ↓

&#x20;┌───────────────┐

&#x20;│ Relevant?     │

&#x20;└───────┬───────┘

&#x20;        │

&#x20;   No ──┘ ──→ Query Rewrite

&#x20;                 ↓

&#x20;            Codebase Search

&#x20;                 ↑

&#x20;                 └──── Retry Loop



&#x20;        Yes

&#x20;         ↓

&#x20;    Code Analyzer

&#x20;         ↓

&#x20;   Answer Generator

&#x20;         ↓

&#x20;     Validator

&#x20;         ↓

&#x20;┌──────────────────┐

&#x20;│ Grounded Answer? │

&#x20;└────────┬─────────┘

&#x20;         │

&#x20;    No ──┘ ──→ Answer Repair

&#x20;                   ↓

&#x20;                Validator

&#x20;                   ↑

&#x20;                   └── Retry



&#x20;         Yes

&#x20;          ↓

&#x20;       Final Answer

```



\## Key Features



\* Natural-language interaction with a software codebase

\* Automated codebase ingestion and chunking

\* Semantic code retrieval using vector embeddings

\* Qdrant-based vector storage and search

\* LangGraph workflow orchestration

\* Question routing and relevance checking

\* Automatic query rewriting when retrieval is insufficient

\* Code analysis based on retrieved source

\* Source-grounded answer generation

\* Answer validation against retrieved evidence

\* Retry and repair loops for unreliable answers

\* Deterministic extraction for code-specific questions such as functions, classes, and imports



\## Tech Stack



\* Python

\* LangGraph

\* Qdrant

\* Sentence Transformers

\* Hugging Face Transformers

\* Qwen2.5-0.5B-Instruct

\* REST API

\* Retrieval-Augmented Generation (RAG)

\* Vector Embeddings



\## RAG Pipeline



```text

Source Code

&#x20;   ↓

File Discovery

&#x20;   ↓

Code Chunking

&#x20;   ↓

Sentence Transformer Embeddings

&#x20;   ↓

384-Dimensional Vectors

&#x20;   ↓

Qdrant Collection

&#x20;   ↓

Semantic Retrieval

&#x20;   ↓

Relevant Code Context

```



The project uses `sentence-transformers/all-MiniLM-L6-v2` to generate 384-dimensional embeddings.



\## Agent Workflow



The agent is implemented using LangGraph and consists of multiple stages:



\### 1. Question Analysis



The agent first analyzes the user's question and determines what type of task is required.



\### 2. Routing



The question is routed to the appropriate workflow. Codebase-related questions are sent to the retrieval pipeline.



\### 3. Codebase Search



The system converts the question into an embedding and searches the Qdrant vector database for relevant code chunks.



\### 4. Relevance Check



Retrieved results are evaluated to determine whether the available code context is relevant to the question.



\### 5. Query Rewrite



If the retrieved context is insufficient, the agent rewrites the query and performs another retrieval attempt.



\### 6. Code Analysis



Relevant source-code chunks are analyzed to extract information required to answer the question.



\### 7. Answer Generation



The agent generates an answer using the retrieved source code as evidence.



\### 8. Validation



The generated answer is checked against the retrieved source code to ensure that the response is grounded in actual code.



\### 9. Repair Loop



If validation fails, the answer is repaired and sent through validation again before producing the final response.



\## Example



Question:



```text

What functions are defined in nodes.py?

```



The agent retrieves the relevant `nodes.py` chunks and extracts the function definitions directly from the source code.



Example output:



```text

analyze\_question()

route\_question()

codebase\_search\_node()

check\_relevance()

rewrite\_query()

analyze\_code()

generate\_answer()

normalize\_text()

extract\_evidence()

evidence\_is\_grounded()

validate\_answer()

repair\_answer()

```



The generated answer is then validated against the retrieved source before being returned.



\## Project Structure



```text

langgraph-codebase-agent/

│

├── agent/

│   ├── \_\_init\_\_.py

│   ├── graph.py

│   ├── nodes.py

│   ├── qdrant\_connection.py

│   ├── retriever.py

│   └── state.py

│

├── ingest\_codebase.py

├── main.py

├── .env.example

├── .gitignore

└── README.md

```



\## Setup



Clone the repository and create a Python virtual environment.



```bash

git clone https://github.com/mith2804/langgraph-codebase-agent.git



cd langgraph-codebase-agent



python -m venv .venv

```



Activate the environment on Windows:



```powershell

.venv\\Scripts\\activate

```



Install dependencies:



```powershell

pip install -r requirements.txt

```



Create a `.env` file based on `.env.example`:



```text

QDRANT\_URL=your\_qdrant\_url

QDRANT\_API\_KEY=your\_qdrant\_api\_key

COLLECTION\_NAME=codebase\_chunks\_v2

```



\## Ingest a Codebase



Run:



```powershell

python ingest\_codebase.py

```



This discovers source files, chunks the code, generates embeddings, creates the Qdrant collection, and uploads the vectors.



\## Run the Agent



Run:



```powershell

python main.py

```



Then provide a natural-language question about the codebase.



\## Design Goal



The goal of this project is to move beyond a simple RAG chatbot toward an autonomous codebase engineering workflow.



Instead of simply retrieving documents and generating an answer, the agent can:



```text

Plan

&#x20; ↓

Retrieve

&#x20; ↓

Evaluate

&#x20; ↓

Rewrite

&#x20; ↓

Analyze

&#x20; ↓

Generate

&#x20; ↓

Validate

&#x20; ↓

Repair

&#x20; ↓

Answer

```



This makes the system more reliable for codebase-level reasoning and reduces unsupported or hallucinated answers.



\## Future Improvements



\* Multi-file dependency analysis

\* Code modification and patch generation

\* Automated test execution

\* Git-aware code analysis

\* Tool-based terminal execution

\* Pull-request generation

\* More advanced code understanding models

\* Agent memory and long-term project context



\## Author



&#x20;Mithra Murugesan



AI \& Data Science | Aspiring AI Engineer



GitHub: https://github.com/mith2804



