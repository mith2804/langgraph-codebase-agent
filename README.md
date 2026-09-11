# Autonomous AI Codebase Engineering Agent

A LangGraph-based autonomous AI agent that can understand, retrieve, analyze, modify, test, and validate software codebases using natural-language instructions.

The system combines Agentic AI, Retrieval-Augmented Generation (RAG), Vector Search, Code Analysis, Tool Execution, Testing, and Validation Loops to move beyond a traditional RAG chatbot toward an autonomous codebase engineering workflow.

---

## Overview

Traditional RAG systems mainly follow:

User Question
    ↓
Retrieve
    ↓
Generate Answer

This project extends that approach into an agentic workflow:

User Request
    ↓
Question Analysis
    ↓
Route Decision
    ↓
Codebase Retrieval
    ↓
Relevance Check
    ↓
Query Rewrite if required
    ↓
Code Analysis
    ↓
Tool Selection
    ↓
Answer / Modification
    ↓
Testing
    ↓
Validation
    ↓
Repair if required
    ↓
Final Result

The agent is designed to improve reliability when working with real software repositories by grounding responses in actual source code and validating generated results.

---

## Key Features

- Natural-language interaction with a software codebase
- Automated source-code ingestion
- Intelligent code chunking
- Semantic code retrieval using vector embeddings
- Qdrant vector database integration
- LangGraph-based agent orchestration
- Question analysis and routing
- Retrieval relevance checking
- Automatic query rewriting
- Code-specific analysis
- Tool selection based on task requirements
- File and source-code inspection
- Code modification planning
- Automated code modification execution
- Automated test execution
- Source-grounded answer generation
- Answer validation
- Modification validation
- Retry and repair loops
- Deterministic extraction for functions, classes, and imports
- Streamlit-based user interface

---

## Architecture

```text
                         User
                          |
                          v
                 Question Analyzer
                          |
                          v
                   Route Decision
                          |
                          v
                  Codebase Search
                          |
                          v
                  Qdrant Retrieval
                          |
                          v
                  Relevance Check
                    /         \
                  No           Yes
                  |             |
                  v             v
             Query Rewrite   Code Analysis
                  |             |
                  v             v
            Codebase Search  Tool Selector
                  |             |
                  |             v
                  |           Tools
                  |             |
                  |             +-- Search Code
                  |             +-- Read File
                  |             +-- Run Tests
                  |             +-- Code Operations
                  |             |
                  +-------------+
                                |
                                v
                       Answer / Modification
                                |
                                v
                           Validator
                          /         \
                        No           Yes
                        |             |
                        v             v
                      Repair     Final Result
                        |
                        +------> Validator
                        RAG Pipeline

The retrieval system indexes source code into Qdrant using vector embeddings.

Source Code
    |
    v
File Discovery
    |
    v
Code Chunking
    |
    v
Sentence Transformer
    |
    v
384-Dimensional Embeddings
    |
    v
Qdrant Collection
    |
    v
Semantic Search
    |
    v
Relevant Code Context
    |
    v
Code Analysis

The project uses:

Embedding Model:
sentence-transformers/all-MiniLM-L6-v2

Vector Dimension:
384

Vector Database:
QdrantAgent Workflow
1. Question Analysis

The agent first analyzes the user's request and determines what type of task is required.

Examples include:

General questions
Code search
Function and class inspection
Import analysis
Error analysis
Modification requests
Testing requests
2. Routing

The analyzed request is routed to the appropriate workflow.

Codebase-related requests are sent to the retrieval and engineering pipeline.

3. Codebase Search

The system converts the question into an embedding and searches the Qdrant vector database for relevant code chunks.

The agent can also detect target filenames when appropriate to improve source-code retrieval.

4. Relevance Check

Retrieved results are evaluated to determine whether the available code context is relevant and sufficient.

If the retrieved information is insufficient, the agent can continue through a recovery path.

5. Query Rewriting

When retrieval quality is insufficient, the agent rewrites the query and performs another retrieval attempt.

Initial Query
     |
     v
Retrieve
     |
     v
Relevant?
   /   \
 No    Yes
 |      |
 v      v
Rewrite Continue
 |
 v
Retrieve Again
6. Code Analysis

Relevant source-code context is analyzed to determine the information or action required.

For code-specific questions, deterministic extraction can be used to identify:

Functions
Classes
Imports
Files
Source-code locations
7. Tool Selection

For tasks requiring additional actions, the agent selects the appropriate tool.

Examples include:

Search code
Read file
Run function tests
Execute code-related operations

This allows the agent to move beyond retrieval-only behavior.

8. Answer Generation

For information requests, the agent generates an answer using retrieved source code and tool results as evidence.

The goal is to keep responses grounded in the actual repository instead of relying only on the language model's internal knowledge.

9. Code Modification

For modification requests, the agent can plan and execute changes to source files.

Modification Request
        |
        v
Modification Planning
        |
        v
Source Code Modification
        |
        v
Validation
10. Test Execution

After a modification or test-related request, the system can execute tests to verify the resulting code.

Modification
     |
     v
Run Test
     |
     v
Test Passed?
   /      \
 No       Yes
 |         |
 v         v
Repair   Continue
11. Validation

The agent validates generated answers and code modifications.

For answers, validation checks whether the response is supported by available evidence.

For modifications, validation can include syntax and test verification.

12. Repair Loop

If validation fails, the agent can attempt a repair and send the result through validation again.

Generate
   |
   v
Validate
   |
   v
Failed?
   |
   v
Repair
   |
   v
Validate Again
   |
   v
Final Result
Example
Codebase Question
What functions are defined in agent/agent_test.py?

The agent identifies the target file and inspects the source code.

Example result:

hello()
greet()
test_greet()

The result is based on the actual source code rather than a generic model response.

Testing Request
Run a test to verify that greet() in agent/agent_test.py
returns 'Hello from Agent'

The agent identifies the testing requirement, selects the appropriate test tool, executes the test, and validates the result.

Modification Request
Add a comment at the top of ingest_codebase.py
saying "Codebase ingestion module"

The modification workflow performs:

Understand Request
       |
       v
Create Modification Plan
       |
       v
Modify File
       |
       v
Run Validation
       |
       v
Run Tests
       |
       v
Return Result
Project Structure
langgraph-codebase-agent/
|
+-- agent/
|   +-- __init__.py
|   +-- graph.py
|   +-- nodes.py
|   +-- state.py
|   +-- retriever.py
|   +-- qdrant_connection.py
|   +-- tools.py
|   +-- tool_selector.py
|   +-- model.py
|   +-- modification_planner.py
|   +-- modification_executor.py
|   +-- test_runner.py
|   +-- agent_test.py
|
+-- ingest_codebase.py
+-- main.py
+-- requirements.txt
+-- .env.example
+-- .gitignore
+-- README.md
Tech Stack
Python
LangGraph
Qdrant
Sentence Transformers
Hugging Face Transformers
Qwen2.5-0.5B-Instruct
PyTorch
Streamlit
REST APIs
Retrieval-Augmented Generation (RAG)
Vector Embeddings
Setup
1. Clone the Repository
git clone https://github.com/mith2804/langgraph-codebase-agent.git
cd langgraph-codebase-agent
2. Create a Virtual Environment
python -m venv .venv
3. Activate the Environment

Windows PowerShell:

.\.venv\Scripts\Activate.ps1
4. Install Dependencies
pip install -r requirements.txt
5. Configure Environment Variables

Create a .env file using .env.example.

Example:

QDRANT_URL=your_qdrant_url
QDRANT_API_KEY=your_qdrant_api_key
COLLECTION_NAME=codebase_chunks_v2

Do not commit API keys or other secrets to GitHub.

Ingest a Codebase

Run:

python ingest_codebase.py

The ingestion process:

Discover Source Files
       |
       v
Read Source Code
       |
       v
Create Chunks
       |
       v
Generate Embeddings
       |
       v
Create / Connect Qdrant Collection
       |
       v
Upload Vectors

The indexed code can then be searched by the agent.

Run the Agent

The project includes a Streamlit interface.

Run:

streamlit run main.py

The application opens a local Streamlit interface where users can enter natural-language requests about the codebase.

Design Goal

The main goal of this project is to move beyond a simple RAG chatbot toward an autonomous AI codebase engineering agent.

A traditional RAG application mainly performs:

Retrieve
   |
   v
Generate

This project introduces additional reasoning and engineering stages:

Analyze
   |
   v
Route
   |
   v
Retrieve
   |
   v
Evaluate
   |
   v
Rewrite
   |
   v
Analyze Code
   |
   v
Select Tool
   |
   v
Execute
   |
   v
Test
   |
   v
Validate
   |
   v
Repair
   |
   v
Return Result

This architecture enables the system to handle both code understanding and code engineering tasks.

Reliability Approach
Retrieval Grounding

Answers are based on retrieved repository content.

Relevance Checking

Retrieved context is evaluated before relying on it.

Query Rewriting

Poor retrieval can trigger another search attempt.

Deterministic Code Extraction

Structured code information such as functions and imports can be extracted directly from source files.

Validation

Generated responses and modifications are checked before being returned.

Testing

Code changes can be verified through automated test execution.

Repair

Failed validation can trigger another correction cycle.

Current Capabilities

The current implementation supports:

✓ Codebase ingestion
✓ Vector-based code retrieval
✓ Natural-language codebase questions
✓ Function / class / import analysis
✓ Query rewriting
✓ Tool selection
✓ File inspection
✓ Code modification planning
✓ Code modification execution
✓ Automated testing
✓ Answer validation
✓ Modification validation
✓ Repair loops
✓ Streamlit interface
Future Improvements

Potential future improvements include:

Multi-file dependency analysis
More advanced code understanding models
Git-aware code analysis
More sophisticated patch generation
Pull-request generation
Automated repository-level refactoring
Long-term project memory
Multi-agent collaboration
Improved test generation
More advanced development-tool integration
Author

Mithra 

AI & Data Science | Aspiring AI Engineer

GitHub: https://github.com/mith2804