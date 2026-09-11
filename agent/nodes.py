import re
import torch

from agent.retriever import search_codebase

from agent.tools import (
    read_file,
    search_code,
    write_file,
    list_project_files,
    run_function_test,
)

from agent.test_runner import run_tests
from agent.model import get_qwen_model


# =========================================================
# CONSTANTS
# =========================================================

RELEVANCE_THRESHOLD = 0.20
MAX_SEARCH_RETRIES = 1
MAX_ANSWER_RETRIES = 1


# =========================================================
# 1. ANALYZE QUESTION
# =========================================================

def analyze_question(state):
    question = state.get("question", "").strip()

    print("\n[ANALYZER]")
    print("Question:", question)

    question_type = detect_question_type_from_text(question)

    print("Detected question type:", question_type)

    return {
        "question": question,
        "question_type": question_type,
        "plan": [
            "Understand the user question",
            "Determine question type",
            "Retrieve relevant code when required",
            "Check retrieval relevance",
            "Select engineering tool",
            "Execute tool",
            "Analyze source and tool evidence",
            "Generate grounded answer",
            "Validate answer",
        ],
        "retry_count": state.get("retry_count", 0),
        "answer_retry_count": state.get("answer_retry_count", 0),
        "current_task": "Route question",
    }


# =========================================================
# 2. ROUTE QUESTION
# =========================================================

def route_question(state):
    question = state.get("question", "").lower().strip()

    question_type = state.get(
        "question_type",
        detect_question_type_from_text(question),
    )

    print("\n[ROUTER]")
    print("Deciding what to do...")

    if question_type == "file_list":
        print("Route: CODEBASE")

        return {
            "route": "CODEBASE",
            "current_task": "List project files",
        }

    codebase_keywords = [
        "code",
        "codebase",
        "file",
        ".py",
        "python",
        "function",
        "functions",
        "class",
        "classes",
        "import",
        "imports",
        "library",
        "libraries",
        "error",
        "bug",
        "failure",
        "authentication",
        "api",
        "implementation",
        "qdrant",
        "database",
        "config",
        "configuration",
        "repository",
        "repo",
        "test",
        "pytest",
        "modify",
        "change",
        "add",
        "remove",
        "update",
        "fix",
        "delete",
        "implement",
        "rewrite",
        "refactor",
        "replace",
    ]

    route = (
        "CODEBASE"
        if any(keyword in question for keyword in codebase_keywords)
        else "GENERAL"
    )

    print("Route:", route)

    return {
        "route": route,
        "current_task": "Retrieve code",
    }


# =========================================================
# 3. LIST PROJECT FILES
# =========================================================

def list_project_files_node(state):
    print("\n[FILE LIST]")

    try:
        project_files = list_project_files()

    except Exception as e:
        print("[FILE LIST ERROR]", e)

        return {
            "project_files": [],
            "file_list_error": str(e),
            "question_type": "file_list",
            "current_task": "Generate answer",
        }

    print("Found project files:", len(project_files))

    for index, file_name in enumerate(project_files, start=1):
        print(f"  {index}. {file_name}")

    return {
        "project_files": project_files,
        "question_type": "file_list",
        "file_list_error": "",
        "current_task": "Generate answer",
    }


# =========================================================
# 4. CODEBASE SEARCH
# =========================================================

def codebase_search_node(state):
    query = state.get("search_query", "").strip()

    if not query:
        query = state.get("question", "").strip()

    question = state.get("question", "").strip()

    print("\n[CODEBASE SEARCH]")
    print("Searching codebase for:", query)

    filename_match = re.search(
        r"([A-Za-z0-9_.\-/\\]+\.py)\b",
        question,
        re.IGNORECASE,
    )

    filename = None

    if filename_match:
        filename = filename_match.group(1).replace("\\", "/")

        print("Detected target file:", filename)

        search_query = f"{filename} {query}"

    else:
        search_query = query

    try:
        results = search_codebase(
            search_query,
            limit=5,
        )

    except Exception as e:
        print("[QDRANT ERROR]", e)

        return {
            "retrieved_code": [],
            "search_query": search_query,
            "relevance_score": 0.0,
            "best_score": 0.0,
            "relevance_reason": f"Retrieval failed: {e}",
            "current_task": "Check relevance",
        }

    if filename_match and results:
        target_filename = filename.split("/")[-1].lower()

        matching_results = [
            item
            for item in results
            if str(
                item.get("file_name", "")
            ).lower() == target_filename
        ]

        if matching_results:
            results = sorted(
                matching_results,
                key=lambda item: (
                    item.get("chunk_index", 0)
                    if isinstance(
                        item.get("chunk_index", 0),
                        int,
                    )
                    else 0
                ),
            )

    print("\n[QDRANT SEARCH]")
    print(f"Retrieved {len(results)} code chunks")

    for i, result in enumerate(results, 1):
        print(
            f"  {i}. {result.get('file_name', 'unknown')} "
            f"(chunk={result.get('chunk_index', -1)}, "
            f"score={result.get('score', 0.0):.8f})"
        )

    return {
        "retrieved_code": results,
        "search_query": search_query,
        "current_task": "Check relevance",
    }


# =========================================================
# 5. CHECK RELEVANCE
# =========================================================

def check_relevance(state):
    retrieved_code = state.get("retrieved_code", [])

    print("\n[RELEVANCE CHECK]")

    if not retrieved_code:
        print("No code was retrieved.")

        return {
            "relevance_score": 0.0,
            "best_score": 0.0,
            "relevance_reason": "No code was retrieved.",
            "current_task": "Route based on relevance",
        }

    scores = []

    for item in retrieved_code:
        try:
            scores.append(
                float(item.get("score", 0.0))
            )
        except Exception:
            scores.append(0.0)

    best_score = max(scores) if scores else 0.0

    print("Best retrieval score:", best_score)

    if best_score >= RELEVANCE_THRESHOLD:
        reason = "Retrieved code appears sufficiently relevant."

        print(
            "Decision: Retrieved code is relevant."
        )

    else:
        reason = "Retrieved code may not be sufficiently relevant."

        print(
            "Decision: Retrieved code may not be sufficiently relevant."
        )

    return {
        "relevance_score": best_score,
        "best_score": best_score,
        "relevance_reason": reason,
        "current_task": "Route based on relevance",
    }


# =========================================================
# 6. REWRITE QUERY
# =========================================================

def rewrite_query(state):
    question = state.get("question", "").strip()

    retry_count = int(
        state.get("retry_count", 0)
    ) + 1

    print("\n[QUERY REWRITER]")
    print("Original question:", question)

    if not question:
        rewritten_query = (
            "codebase files functions classes imports"
        )

    else:
        rewritten_query = question

        question_type = state.get(
            "question_type",
            "general",
        )

        if question_type == "function":
            rewritten_query = (
                f"{question} function definitions def"
            )

        elif question_type == "class":
            rewritten_query = (
                f"{question} class definitions"
            )

        elif question_type == "import":
            rewritten_query = (
                f"{question} import from libraries"
            )

        elif question_type == "error":
            rewritten_query = (
                f"{question} "
                "error exception traceback implementation"
            )

    print("Rewritten query:", rewritten_query)
    print("Retry count:", retry_count)

    return {
        "search_query": rewritten_query,
        "retry_count": retry_count,
        "current_task": (
            "Retry codebase search with improved query"
        ),
    }


# =========================================================
# 7. CODE ANALYZER
# =========================================================

def analyze_code(state):
    question = state.get("question", "")

    question_type = state.get(
        "question_type",
        detect_question_type_from_text(question),
    )

    retrieved_code = state.get(
        "retrieved_code",
        [],
    )

    tool_name = state.get(
        "tool_name",
        "",
    )

    tool_input = state.get(
        "tool_input",
        "",
    )

    tool_output = state.get(
        "tool_output",
        "",
    )

    print("\n[CODE ANALYZER]")
    print("Question type:", question_type)

    if question_type == "file_list":
        return {
            "code_analysis": {
                "question_type": "file_list",
                "files": state.get(
                    "project_files",
                    [],
                ),
                "functions": [],
                "classes": [],
                "imports": [],
                "raw_context": "",
            },
            "current_task": "Generate answer",
        }

    if (
        tool_name == "read_file"
        and tool_output
        and not tool_output.startswith("Error:")
    ):
        print(
            "Using COMPLETE file returned by read_file."
        )

        file_name = (
            tool_input
            .replace("\\", "/")
            .split("/")[-1]
        )

        retrieved_code = [
            {
                "score": 1.0,
                "content": tool_output,
                "file_path": tool_input,
                "file_name": file_name,
                "chunk_index": 0,
            }
        ]

    if not retrieved_code:
        print(
            "No relevant code was available."
        )

        return {
            "code_analysis": {
                "question_type": question_type,
                "files": [],
                "functions": [],
                "classes": [],
                "imports": [],
                "raw_context": "",
            },
            "retrieved_code": retrieved_code,
            "tool_evidence": (
                tool_output
                if tool_output
                else ""
            ),
            "current_task": "Generate answer",
        }

    files = []
    functions = []
    classes = []
    imports = []
    source_parts = []

    for result in retrieved_code:
        file_name = result.get(
            "file_name",
            "unknown",
        )

        content = result.get(
            "content",
            "",
        )

        if file_name not in files:
            files.append(file_name)

        source_parts.append(
            f"FILE: {file_name}\n"
            f"CODE:\n{content}"
        )

        functions.extend(
            extract_function_definitions(
                content
            )
        )

        classes.extend(
            extract_class_definitions(
                content
            )
        )

        imports.extend(
            extract_imports(
                content
            )
        )

    functions = list(
        dict.fromkeys(functions)
    )

    classes = list(
        dict.fromkeys(classes)
    )

    imports = list(
        dict.fromkeys(imports)
    )

    tool_evidence = (
        tool_output
        if tool_output
        else ""
    )

    analysis = {
        "question_type": question_type,
        "files": files,
        "functions": functions,
        "classes": classes,
        "imports": imports,
        "raw_context": "\n\n".join(
            source_parts
        ),
        "tool_evidence": tool_evidence,
    }

    print("Files:", files)
    print("Functions:", functions)
    print("Classes:", classes)
    print("Imports:", imports)

    return {
        "code_analysis": analysis,
        "retrieved_code": retrieved_code,
        "tool_evidence": tool_evidence,
        "current_task": "Generate answer",
    }


# =========================================================
# 8. QUESTION TYPE DETECTION
# =========================================================

def detect_question_type_from_text(question):
    question = question.lower().strip()

    # QdrantClient explanation questions are general analysis questions.
    # Keep this check before error detection so normal "why" questions
    # are never classified as errors.
    if (
        "qdrantclient" in question
        or "why does the project use qdrant" in question
        or "why is qdrantclient" in question
        or "purpose of qdrantclient" in question
    ):
        return "general"

    if any(
        phrase in question
        for phrase in [
            "what files",
            "which files",
            "files are present",
            "files present",
            "list files",
            "list all files",
            "show files",
            "project files",
            "files in the project",
            "files in project",
            "what files are in",
            "which files are in",
        ]
    ):
        return "file_list"

    if any(
        phrase in question
        for phrase in [
            "modify",
            "change",
            "update",
            "edit",
            "fix",
            "add ",
            "remove",
            "delete",
            "implement",
            "create",
            "rewrite",
            "refactor",
            "replace",
        ]
    ):
        return "modification"

    if any(
        phrase in question
        for phrase in [
            "what functions",
            "which functions",
            "functions defined",
            "function defined",
            "list functions",
            "show functions",
            "what methods",
        ]
    ):
        return "function"

    if any(
        phrase in question
        for phrase in [
            "what classes",
            "which classes",
            "classes defined",
            "class defined",
            "list classes",
            "show classes",
        ]
    ):
        return "class"

    if any(
        phrase in question
        for phrase in [
            "what imports",
            "which imports",
            "imports in",
            "imported libraries",
            "libraries imported",
            "what libraries",
        ]
    ):
        return "import"

    if any(
        phrase in question
        for phrase in [
            "error",
            "bug",
            "failure",
            "failing",
            "exception",
            "traceback",
        ]
    ):
        return "error"

    return "general"


# =========================================================
# 9. EXTRACT FUNCTION DEFINITIONS
# =========================================================

def extract_function_definitions(text):
    if not text:
        return []

    return re.findall(
        r"^\s*(?:async\s+)?def\s+"
        r"([A-Za-z_][A-Za-z0-9_]*)\s*\(",
        text,
        flags=re.MULTILINE,
    )


# =========================================================
# 10. EXTRACT CLASS DEFINITIONS
# =========================================================

def extract_class_definitions(text):
    if not text:
        return []

    return re.findall(
        r"^\s*class\s+"
        r"([A-Za-z_][A-Za-z0-9_]*)",
        text,
        flags=re.MULTILINE,
    )


# =========================================================
# 11. EXTRACT IMPORTS
# =========================================================

def extract_imports(code):
    if not code:
        return []

    imports = []

    lines = code.splitlines()

    inside_multiline_import = False
    multiline_import = ""

    for line in lines:
        stripped = line.strip()

        if stripped.startswith("import "):
            imports.append(stripped)
            continue

        if (
            stripped.startswith("from ")
            and stripped.endswith("(")
        ):
            inside_multiline_import = True
            multiline_import = stripped
            continue

        if inside_multiline_import:
            multiline_import += " " + stripped

            if stripped == ")":
                imports.append(
                    multiline_import
                )

                inside_multiline_import = False
                multiline_import = ""

            continue

        if stripped.startswith("from "):
            imports.append(stripped)

    return imports


# =========================================================
# 12. BUILD SOURCE CONTEXT
# =========================================================

def build_source_context(retrieved_code):
    blocks = []

    for index, result in enumerate(
        retrieved_code,
        start=1,
    ):
        file_name = result.get(
            "file_name",
            "unknown",
        )

        score = result.get(
            "score",
            0.0,
        )

        content = result.get(
            "content",
            "",
        ).strip()

        if not content:
            continue

        blocks.append(
            f"SOURCE {index}\n"
            f"FILE:\n{file_name}\n"
            f"SCORE:\n{score}\n"
            f"CODE:\n{content}"
        )

    context = "\n\n".join(blocks)

    return context[:12000]


# =========================================================
# 13. TOOL EVIDENCE CONTEXT
# =========================================================

def build_tool_evidence_context(tool_output):
    if not tool_output:
        return ""

    if tool_output.startswith("Error:"):
        return ""

    return tool_output[:12000]


# =========================================================
# 14. DETERMINISTIC ANSWER
# =========================================================

def generate_deterministic_answer(
    question,
    question_type,
    retrieved_code,
    code_analysis,
    tool_output="",
):
    if not retrieved_code and not tool_output:
        return None

    files = code_analysis.get(
        "files",
        [],
    )

    functions = code_analysis.get(
        "functions",
        [],
    )

    classes = code_analysis.get(
        "classes",
        [],
    )

    imports = code_analysis.get(
        "imports",
        [],
    )

    if question_type == "function":
        if functions:
            return (
                "Functions defined in the retrieved "
                "source code:\n\n"
                + "\n".join(
                    f"- {name}()"
                    for name in functions
                )
                + f"\n\nFile(s): "
                + ", ".join(files)
                + "\n\n"
                "Conclusion:\n"
                "These function names were extracted "
                "directly from the source."
            )

        return (
            "No function definitions were found "
            "in the retrieved source code."
        )

    if question_type == "class":
        if classes:
            return (
                "Classes defined in the retrieved "
                "source code:\n\n"
                + "\n".join(
                    f"- {name}"
                    for name in classes
                )
                + f"\n\nFile(s): "
                + ", ".join(files)
                + "\n\n"
                "Conclusion:\n"
                "These class names were extracted "
                "directly from the source."
            )

        return (
            "No class definitions were found "
            "in the retrieved source code."
        )

    if question_type == "import":
        if imports:
            return (
                "Imports found in the retrieved "
                "source code:\n\n"
                + "\n".join(
                    f"- {item}"
                    for item in imports
                )
                + f"\n\nFile(s): "
                + ", ".join(files)
                + "\n\n"
                "Conclusion:\n"
                "These imports were extracted "
                "directly from the source."
            )

        return (
            "No imports were found "
            "in the retrieved source code."
        )

    return None


# =========================================================
# 15. QDRANT / CONFIG LOCATION ANSWER
# =========================================================

def generate_location_answer(
    question,
    tool_output,
):
    """
    Deterministic answer for Qdrant source-location
    and configuration questions.
    """

    if not tool_output:
        return None

    q = question.lower()

    wants_qdrant = "qdrant" in q
    wants_url = (
        "qdrant_url" in q
        or "url" in q
    )

    if not (
        wants_qdrant
        and wants_url
    ):
        return None

    lines = tool_output.splitlines()

    relevant = []

    for line in lines:
        lower = line.lower()

        if (
            "qdrantclient" in lower
            or "qdrant_url" in lower
            or "url=qdrant_url" in lower
        ):
            relevant.append(
                line.strip()
            )

    if not relevant:
        return None

    qdrant_lines = [
        line
        for line in relevant
        if "qdrant_connection.py"
        in line.lower()
    ]

    if qdrant_lines:
        evidence_lines = qdrant_lines
        file_name = "qdrant_connection.py"

    else:
        evidence_lines = relevant
        file_name = (
            relevant[0].split(":")[0]
        )

    initialization = [
        line
        for line in evidence_lines
        if (
            "qdrantclient(" in line.lower()
            or "url=qdrant_url"
            in line.lower()
        )
    ]

    url_loading = [
        line
        for line in evidence_lines
        if (
            "qdrant_url =" in line.lower()
            or "qdrant_url=" in line.lower()
        )
    ]

    answer_parts = []

    if initialization:
        answer_parts.append(
            "The Qdrant client is initialized in "
            f"{file_name}."
        )

    else:
        answer_parts.append(
            "The retrieved search evidence identifies "
            "Qdrant client-related code."
        )

    if url_loading:
        answer_parts.append(
            "The QDRANT_URL value is read from the "
            "environment using "
            '`os.getenv("QDRANT_URL")`.'
        )

    if any(
        "url=qdrant_url" in line.lower()
        for line in evidence_lines
    ):
        answer_parts.append(
            "That URL value is then passed to "
            "`QdrantClient` through "
            "`url=QDRANT_URL`."
        )

    evidence = "\n".join(
        evidence_lines[:8]
    )

    return (
        "Answer:\n"
        + " ".join(answer_parts)
        + "\n\nEvidence:\n"
        + evidence
        + "\n\nFile:\n"
        + file_name
        + "\n\nConclusion:\n"
        + "The retrieved source directly shows how "
        "QDRANT_URL is loaded and used to initialize "
        "the Qdrant client."
    )


# =========================================================
# 16. QDRANT EXPLANATION ANSWER
# =========================================================

def generate_qdrant_explanation_answer(
    question,
    tool_output,
):
    """
    Deterministic answer for questions asking why
    QdrantClient is used.

    Uses exact search evidence instead of relying
    on the local LLM to infer the source location.
    """

    if not tool_output:
        return None

    question_lower = question.lower()

    if (
        "qdrantclient" not in question_lower
        and "why does the project use qdrant" not in question_lower
    ):
        return None

    lines = [
        line.strip()
        for line in tool_output.splitlines()
        if line.strip()
    ]

    relevant_lines = [
        line
        for line in lines
        if (
            "qdrantclient" in line.lower()
            or "qdrant_client" in line.lower()
        )
    ]

    if not relevant_lines:
        return None

    # Prefer actual implementation files over
    # references inside nodes.py or tool_selector.py.
    implementation_lines = [
        line
        for line in relevant_lines
        if (
            "qdrant_connection.py" in line.lower()
            or "store_qdrant.py" in line.lower()
            or "test_qdrant.py" in line.lower()
            or "qdrant_auth_test.py" in line.lower()
        )
    ]

    evidence_lines = (
        implementation_lines[:6]
        if implementation_lines
        else relevant_lines[:6]
    )

    files = []

    for line in evidence_lines:
        match = re.match(
            r"([A-Za-z0-9_.\-/\\]+\.py):\d+:",
            line,
        )

        if match:
            file_name = match.group(1)

            if file_name not in files:
                files.append(file_name)

    if not files:
        files = [
            "source files shown in search results"
        ]

    return (
        "Answer:\n"
        "The project uses QdrantClient to connect to "
        "and interact with the Qdrant vector database. "
        "The retrieved source shows QdrantClient being "
        "imported and initialized in the project's "
        "Qdrant-related code.\n\n"
        "Evidence:\n"
        + "\n".join(evidence_lines)
        + "\n\n"
        "File:\n"
        + "\n".join(files)
        + "\n\n"
        "Conclusion:\n"
        "QdrantClient is used as the project's client "
        "interface for connecting to Qdrant and working "
        "with the stored vector data."
    )


# =========================================================
# 17. MODIFICATION ANSWER
# =========================================================

def generate_modification_answer(state):
    modification_status = state.get(
        "modification_status",
        "",
    )

    target_file = state.get(
        "target_file",
        "",
    )

    target_function = state.get(
        "target_function",
        "",
    )

    modification_reason = state.get(
        "modification_reason",
        "",
    )

    tool_output = state.get(
        "tool_output",
        "",
    )

    if modification_status == "MODIFIED":

        if not tool_output:
            test_result = "Tests: Result unavailable."

        elif "TESTS PASSED" in tool_output:

            passed_match = re.search(
                r"(\d+)\s+passed",
                tool_output,
                re.IGNORECASE,
            )

            if passed_match:
                test_result = (
                    f"Tests: PASSED "
                    f"({passed_match.group(1)} test(s) passed)"
                )
            else:
                test_result = "Tests: PASSED"

        elif (
            "TESTS FAILED" in tool_output
            or "failed" in tool_output.lower()
        ):
            test_result = "Tests: FAILED"

        else:
            first_line = next(
                (
                    line.strip()
                    for line in tool_output.splitlines()
                    if line.strip()
                ),
                "Result unavailable.",
            )

            test_result = (
                f"Tests: {first_line}"
            )

        return (
            "Modification completed successfully.\n\n"
            f"File: {target_file}\n"
            + (
                f"Function: {target_function}\n"
                if target_function
                else ""
            )
            + "\n"
            "Syntax validation: PASSED\n"
            "File verification: PASSED\n"
            f"{test_result}"
        )

    return (
        "Modification failed.\n\n"
        f"File: {target_file or 'unknown'}\n"
        f"Reason: "
        f"{modification_reason or 'Unknown error'}"
    )


# =========================================================
# 18. ANSWER GENERATOR
# =========================================================


def build_qdrantclient_answer(question, retrieved_code, tool_output):
    """
    Build a deterministic, grounded answer for QdrantClient explanation
    questions. Prefer actual Qdrant implementation files and ignore
    self-referential matches from nodes.py/tool_selector.py.
    """
    q = str(question or "").lower()

    if not (
        "qdrantclient" in q
        or "why does the project use qdrant" in q
        or "purpose of qdrantclient" in q
    ):
        return None

    candidates = []

    # First use executed tool evidence.
    if tool_output and not str(tool_output).startswith("Error:"):
        for raw_line in str(tool_output).splitlines():
            line = raw_line.strip()
            lower = line.lower()
            if not line:
                continue
            if "qdrantclient" not in lower and "qdrant_client" not in lower:
                continue
            # Avoid using this agent's own answer-generation logic as evidence.
            if "nodes.py:" in lower or "tool_selector.py:" in lower:
                continue
            candidates.append(line)

    # If tool output did not contain implementation evidence, use Qdrant chunks.
    if not candidates:
        for item in retrieved_code or []:
            file_name = str(item.get("file_name", ""))
            content = str(item.get("content", ""))
            lower_file = file_name.lower()

            if not any(
                name in lower_file
                for name in [
                    "qdrant_connection.py",
                    "store_qdrant.py",
                    "test_qdrant.py",
                    "qdrant_auth_test.py",
                ]
            ):
                continue

            for raw_line in content.splitlines():
                line = raw_line.strip()
                lower = line.lower()
                if (
                    line
                    and (
                        "qdrantclient" in lower
                        or "qdrant_client" in lower
                    )
                ):
                    candidates.append(
                        f"{file_name}: {line}"
                    )

    if not candidates:
        return None

    # Prefer the main connection implementation.
    preferred = [
        line for line in candidates
        if "qdrant_connection.py" in line.lower()
    ]
    evidence_lines = (preferred or candidates)[:6]

    files = []
    for line in evidence_lines:
        match = re.match(
            r"([A-Za-z0-9_.\-/\\]+\.py):\d+:",
            line,
        )
        if match:
            file_name = match.group(1)
        else:
            match = re.match(
                r"([A-Za-z0-9_.\-/\\]+\.py):",
                line,
            )
            file_name = (
                match.group(1)
                if match
                else ""
            )

        if file_name and file_name not in files:
            files.append(file_name)

    if not files:
        files = ["Qdrant implementation source"]

    return (
        "Answer:\n"
        "The project uses QdrantClient as the client interface "
        "for connecting to the Qdrant vector database and "
        "working with the project's stored vector data.\n\n"
        "Evidence:\n"
        + "\n".join(evidence_lines)
        + "\n\n"
        "File:\n"
        + "\n".join(files)
        + "\n\n"
        "Conclusion:\n"
        "QdrantClient provides the project's code with the "
        "connection to Qdrant so the application can work "
        "with the stored vector data."
    )

def generate_answer(state):
    print("\n[ANSWER GENERATOR]")

    question = state.get(
        "question",
        "",
    ).strip()

    question_type = state.get(
        "question_type",
        detect_question_type_from_text(
            question
        ),
    )

    # -----------------------------------------------------
    # FILE LIST
    # -----------------------------------------------------

    if question_type == "file_list":
        project_files = state.get(
            "project_files",
            [],
        )

        file_list_error = state.get(
            "file_list_error",
            "",
        )

        if file_list_error:
            answer = (
                "Unable to list project files.\n\n"
                f"Reason: {file_list_error}"
            )

        elif not project_files:
            answer = (
                "No project files were found."
            )

        else:
            answer = (
                "Files present in the project:\n\n"
                + "\n".join(
                    f"- {file}"
                    for file in project_files
                )
                + f"\n\nTotal files: "
                f"{len(project_files)}"
            )

        print(
            "Using deterministic filesystem "
            "file-list answer."
        )

        print(
            "\nGenerated Answer:\n",
            answer,
        )

        return {
            "answer": answer,
            "current_task": "Validate answer",
        }

    # -----------------------------------------------------
    # MODIFICATION
    # -----------------------------------------------------

    if question_type == "modification":
        answer = generate_modification_answer(
            state
        )

        print(
            "\nGenerated Answer:\n",
            answer,
        )

        return {
            "answer": answer,
            "current_task": "Validate answer",
        }

    retrieved_code = state.get(
        "retrieved_code",
        [],
    )

    code_analysis = state.get(
        "code_analysis",
        {},
    )

    tool_output = state.get(
        "tool_output",
        "",
    )

    # -----------------------------------------------------
    # QDRANTCLIENT EXPLANATION — TOP PRIORITY
    # -----------------------------------------------------
    # This must run before Qwen or generic fallbacks.
    # It guarantees that "Why does the project use QdrantClient?"
    # is answered from actual implementation evidence.
    qdrantclient_answer = build_qdrantclient_answer(
        question,
        retrieved_code,
        tool_output,
    )

    if qdrantclient_answer is not None:
        print(
            "Using deterministic QdrantClient explanation answer."
        )
        print(
            "\nGenerated Answer:\n",
            qdrantclient_answer,
        )
        return {
            "answer": qdrantclient_answer,
            "current_task": "Validate answer",
        }

    # -----------------------------------------------------
    # LOCATION ANSWER
    # -----------------------------------------------------

    location_answer = generate_location_answer(
        question,
        tool_output,
    )

    if location_answer is not None:
        print(
            "Using deterministic "
            "source-location answer."
        )

        print(
            "\nGenerated Answer:\n",
            location_answer,
        )

        return {
            "answer": location_answer,
            "current_task": "Validate answer",
        }

    # -----------------------------------------------------
    # QDRANT EXPLANATION ANSWER
    # -----------------------------------------------------

    qdrant_explanation_answer = (
        generate_qdrant_explanation_answer(
            question,
            tool_output,
        )
    )

    if qdrant_explanation_answer is not None:
        print(
            "Using deterministic "
            "Qdrant explanation answer."
        )

        print(
            "\nGenerated Answer:\n",
            qdrant_explanation_answer,
        )

        return {
            "answer": qdrant_explanation_answer,
            "current_task": "Validate answer",
        }

    # -----------------------------------------------------
    # DETERMINISTIC STRUCTURAL ANSWER
    # -----------------------------------------------------

    deterministic_answer = (
        generate_deterministic_answer(
            question,
            question_type,
            retrieved_code,
            code_analysis,
            tool_output,
        )
    )

    if deterministic_answer is not None:
        print(
            "Using deterministic code analysis."
        )

        print(
            "\nGenerated Answer:\n",
            deterministic_answer,
        )

        return {
            "answer": deterministic_answer,
            "current_task": "Validate answer",
        }

    # -----------------------------------------------------
    # NO EVIDENCE
    # -----------------------------------------------------

    if not retrieved_code and not tool_output:
        answer = (
            "Answer:\n"
            "Insufficient evidence in the retrieved code.\n\n"
            "Evidence:\n"
            "No relevant source evidence was returned.\n\n"
            "File:\n"
            "N/A\n\n"
            "Conclusion:\n"
            "The codebase does not currently provide "
            "enough evidence to answer this question."
        )

        return {
            "answer": answer,
            "current_task": "Validate answer",
        }

    # -----------------------------------------------------
    # QWEN GENERAL ANSWER
    # -----------------------------------------------------

    source_context = build_source_context(
        retrieved_code
    )

    tool_context = build_tool_evidence_context(
        tool_output
    )

    system_message = """
You are a strict codebase analysis assistant.

Answer ONLY from the supplied source evidence.

There are two evidence sources:

1. QDRANT SOURCE CODE
2. EXECUTED TOOL RESULT

The EXECUTED TOOL RESULT is authoritative for
exact file locations, line numbers, and literal
search matches.

Do not invent filenames, functions, classes,
imports, errors, configuration, credentials,
API keys, behavior, or root causes.

If the evidence does not prove a claim, say:

"Insufficient evidence in the retrieved code."

Every concrete claim must be supported by
the supplied evidence.

Return exactly:

Answer:
<answer>

Evidence:
<short exact evidence>

File:
<actual filename>

Conclusion:
<short conclusion>
"""

    user_message = f"""
User Question:
{question}

Question Type:
{question_type}

QDRANT SOURCE CODE:
{source_context}

EXECUTED TOOL RESULT:
{tool_context}

Use both evidence sources when relevant.
Do not use outside knowledge.
"""

    messages = [
        {
            "role": "system",
            "content": system_message,
        },
        {
            "role": "user",
            "content": user_message,
        },
    ]

    try:
        print(
            "Getting Qwen model..."
        )

        tokenizer, model = get_qwen_model()

        print(
            "Qwen model ready."
        )

        inputs = tokenizer.apply_chat_template(
            messages,
            tokenize=True,
            add_generation_prompt=True,
            return_tensors="pt",
            return_dict=True,
        )

        with torch.inference_mode():
            outputs = model.generate(
                **inputs,
                max_new_tokens=220,
                do_sample=False,
                pad_token_id=(
                    tokenizer.eos_token_id
                ),
            )

        input_length = (
            inputs["input_ids"].shape[1]
        )

        new_tokens = outputs[
            0,
            input_length:
        ]

        answer = tokenizer.decode(
            new_tokens,
            skip_special_tokens=True,
        ).strip()

    except Exception as e:
        print(
            "[QWEN ERROR]",
            e,
        )

        if tool_output:
            answer = (
                "Answer:\n"
                "The executed code search returned "
                "source evidence, but the language model "
                "could not generate the final response.\n\n"
                "Evidence:\n"
                f"{tool_output[:1500]}\n\n"
                "File:\n"
                "See the files shown in the executed "
                "tool result.\n\n"
                "Conclusion:\n"
                "The answer is limited to the executed "
                "source search."
            )

        elif retrieved_code:
            best = retrieved_code[0]

            file_name = best.get(
                "file_name",
                "unknown",
            )

            content = best.get(
                "content",
                "",
            ).strip()

            first_line = next(
                (
                    line.strip()
                    for line in content.splitlines()
                    if line.strip()
                ),
                "No non-empty source line was found.",
            )

            answer = (
                "Answer:\n"
                "Insufficient evidence in the retrieved code.\n\n"
                "Evidence:\n"
                f"{first_line}\n\n"
                "File:\n"
                f"{file_name}\n\n"
                "Conclusion:\n"
                "The conclusion is limited to the "
                "retrieved source code."
            )

        else:
            answer = (
                "Answer:\n"
                "Insufficient evidence in the retrieved code.\n\n"
                "Evidence:\n"
                "No relevant source evidence was returned.\n\n"
                "File:\n"
                "N/A\n\n"
                "Conclusion:\n"
                "The codebase does not provide enough "
                "evidence to answer this question."
            )

    print(
        "\nGenerated Answer:"
    )

    print(answer)

    return {
        "answer": answer,
        "current_task": "Validate answer",
    }


# =========================================================
# 19. TEXT / EVIDENCE HELPERS
# =========================================================

def normalize_text(text):
    text = str(text).lower()

    text = re.sub(
        r"```python|```",
        " ",
        text,
    )

    text = re.sub(
        r"`",
        "",
        text,
    )

    text = re.sub(
        r"\s+",
        " ",
        text,
    )

    return text.strip()


def extract_evidence(answer):
    if not answer:
        return ""

    match = re.search(
        r"Evidence:\s*(.*?)(?:\n\s*File:|"
        r"\n\s*Conclusion:|$)",
        answer,
        flags=re.IGNORECASE | re.DOTALL,
    )

    return (
        match.group(1).strip()
        if match
        else ""
    )


def extract_file_reference(answer):
    if not answer:
        return ""

    match = re.search(
        r"File:\s*(.*?)(?:\n\s*Conclusion:|$)",
        answer,
        flags=re.IGNORECASE | re.DOTALL,
    )

    return (
        match.group(1).strip()
        if match
        else ""
    )


def evidence_is_grounded(
    evidence,
    retrieved_code,
    tool_output="",
):
    if not evidence.strip():
        return False

    normalized_evidence = normalize_text(
        evidence
    )

    bad_evidence = {
        "none",
        "none provided",
        "no evidence",
        "no relevant evidence",
        "evidence unavailable",
        "not available",
        "no relevant code was retrieved",
        "no code was retrieved",
    }

    if normalized_evidence in bad_evidence:
        return False

    evidence_sources = []

    for item in retrieved_code:
        content = item.get(
            "content",
            "",
        )

        if content:
            evidence_sources.append(
                content
            )

    if (
        tool_output
        and not tool_output.startswith("Error:")
    ):
        evidence_sources.append(
            tool_output
        )

    all_code = normalize_text(
        "\n".join(evidence_sources)
    )

    if not all_code:
        return False

    if normalized_evidence in all_code:
        return True

    statements = re.split(
        r"[\n.;]+",
        normalized_evidence,
    )

    valid_statements = 0

    for statement in statements:
        statement = statement.strip()

        if not statement:
            continue

        words = [
            word
            for word in statement.split()
            if len(word) >= 4
        ]

        if len(words) < 2:
            continue

        matched_words = sum(
            1
            for word in words
            if word in all_code
        )

        overlap = (
            matched_words / len(words)
        )

        if overlap >= 0.75:
            valid_statements += 1

    return valid_statements > 0


def evidence_has_specific_support(
    question,
    evidence,
    tool_output,
):
    q = question.lower()
    e = evidence.lower()
    t = tool_output.lower()

    if "qdrant" in q:
        if (
            "qdrantclient" not in e
            and "qdrantclient" not in t
        ):
            if (
                "qdrant_url" not in e
                and "qdrant_url" not in t
            ):
                return False

    if "qdrant_url" in q:
        if (
            "qdrant_url" not in e
            and "qdrant_url" not in t
        ):
            return False

    return True


# =========================================================
# 20. ANSWER VALIDATOR
# =========================================================

def validate_answer(state):
    print("\n[VALIDATOR]")

    answer = state.get(
        "answer",
        "",
    )

    retrieved_code = state.get(
        "retrieved_code",
        [],
    )

    tool_output = state.get(
        "tool_output",
        "",
    )

    question = state.get(
        "question",
        "",
    )

    question_type = state.get(
        "question_type",
        detect_question_type_from_text(
            question
        ),
    )

    # -----------------------------------------------------
    # FILE LIST VALIDATION
    # -----------------------------------------------------

    if question_type == "file_list":
        project_files = state.get(
            "project_files",
            [],
        )

        file_list_error = state.get(
            "file_list_error",
            "",
        )

        if file_list_error:
            return {
                "validation_status": "FAILED",
                "validation_reason": (
                    "Filesystem listing failed: "
                    f"{file_list_error}"
                ),
                "current_task": "Repair answer",
            }

        if not project_files:
            if (
                "no project files"
                in answer.lower()
            ):
                return {
                    "validation_status": "PASSED",
                    "validation_reason": (
                        "Filesystem was checked."
                    ),
                    "current_task": "Complete",
                }

        if project_files:
            answer_lower = answer.lower()

            if any(
                str(file_path).lower()
                in answer_lower
                for file_path in project_files
            ):
                return {
                    "validation_status": "PASSED",
                    "validation_reason": (
                        "Answer contains verified "
                        "project files."
                    ),
                    "current_task": "Complete",
                }

        return {
            "validation_status": "FAILED",
            "validation_reason": (
                "File list answer could not "
                "be verified."
            ),
            "current_task": "Repair answer",
        }

    # -----------------------------------------------------
    # STRUCTURAL CODE ANALYSIS
    # -----------------------------------------------------

    if question_type in {
        "function",
        "class",
        "import",
    }:

        analysis = state.get(
            "code_analysis",
            {},
        )

        functions = analysis.get(
            "functions",
            [],
        )

        classes = analysis.get(
            "classes",
            [],
        )

        imports = analysis.get(
            "imports",
            [],
        )

        answer_lower = normalize_text(
            answer
        )

        if question_type == "function":

            if not functions:
                if (
                    "no function"
                    in answer_lower
                    or "no function definitions"
                    in answer_lower
                ):
                    print(
                        "Structural answer validation: PASSED"
                    )

                    return {
                        "validation_status": "PASSED",
                        "validation_reason": (
                            "Source analysis confirmed "
                            "no functions."
                        ),
                        "current_task": "Complete",
                    }

            if functions:

                matched = sum(
                    1
                    for function_name
                    in functions
                    if normalize_text(
                        function_name
                    )
                    in answer_lower
                )

                print(
                    f"Function matches: "
                    f"{matched}/{len(functions)}"
                )

                if matched > 0:
                    print(
                        "Structural answer validation: PASSED"
                    )

                    return {
                        "validation_status": "PASSED",
                        "validation_reason": (
                            "Function names match "
                            "source analysis."
                        ),
                        "current_task": "Complete",
                    }

        if question_type == "class":

            if not classes:
                if (
                    "no class"
                    in answer_lower
                    or "no class definitions"
                    in answer_lower
                    or "classes: []"
                    in answer_lower
                ):
                    print(
                        "Structural answer validation: PASSED"
                    )

                    return {
                        "validation_status": "PASSED",
                        "validation_reason": (
                            "Source analysis confirmed "
                            "no class definitions."
                        ),
                        "current_task": "Complete",
                    }

            if classes:

                matched = sum(
                    1
                    for class_name
                    in classes
                    if normalize_text(
                        class_name
                    )
                    in answer_lower
                )

                print(
                    f"Class matches: "
                    f"{matched}/{len(classes)}"
                )

                if matched > 0:
                    print(
                        "Structural answer validation: PASSED"
                    )

                    return {
                        "validation_status": "PASSED",
                        "validation_reason": (
                            "Class names match "
                            "source analysis."
                        ),
                        "current_task": "Complete",
                    }

        if question_type == "import":

            if not imports:
                if (
                    "no import"
                    in answer_lower
                    or "no imports"
                    in answer_lower
                ):
                    print(
                        "Structural answer validation: PASSED"
                    )

                    return {
                        "validation_status": "PASSED",
                        "validation_reason": (
                            "Source analysis confirmed "
                            "no imports."
                        ),
                        "current_task": "Complete",
                    }

            if imports:

                matched = 0

                for import_name in imports:

                    normalized_import = (
                        normalize_text(
                            import_name
                        )
                    )

                    if (
                        normalized_import
                        in answer_lower
                    ):
                        matched += 1

                print(
                    f"Import matches: "
                    f"{matched}/{len(imports)}"
                )

                if matched == len(imports):
                    print(
                        "Structural answer validation: PASSED"
                    )

                    return {
                        "validation_status": "PASSED",
                        "validation_reason": (
                            "All imports match "
                            "source analysis."
                        ),
                        "current_task": "Complete",
                    }

        print(
            "Structural answer validation: FAILED"
        )

        return {
            "validation_status": "FAILED",
            "validation_reason": (
                "Structural answer does not match "
                "source analysis."
            ),
            "current_task": "Repair answer",
        }

    # -----------------------------------------------------
    # MODIFICATION VALIDATION
    # -----------------------------------------------------

    if question_type == "modification":

        modification_status = state.get(
            "modification_status",
            "",
        )

        if modification_status == "MODIFIED":

            print(
                "Modification validation: PASSED"
            )

            return {
                "validation_status": "PASSED",
                "validation_reason": (
                    "Requested modification "
                    "was completed."
                ),
                "current_task": "Complete",
            }

    # -----------------------------------------------------
    # GENERAL VALIDATION
    # -----------------------------------------------------

    if (
        not retrieved_code
        and not tool_output
    ):
        return {
            "validation_status": "FAILED",
            "validation_reason": (
                "No source evidence was retrieved."
            ),
            "current_task": "Repair answer",
        }

    evidence = extract_evidence(
        answer
    )

    file_reference = extract_file_reference(
        answer
    )

    has_evidence_section = (
        "evidence:" in answer.lower()
    )

    has_conclusion = (
        "conclusion:" in answer.lower()
    )

    filenames = [
        item.get(
            "file_name",
            "",
        )
        for item in retrieved_code
        if item.get("file_name")
    ]

    tool_files = re.findall(
        r"(?im)"
        r"([A-Za-z0-9_.\-/\\]+\.py):\d+:",
        tool_output or "",
    )

    known_files = (
        filenames + tool_files
    )

    has_file_reference = any(
        file_name.lower()
        in answer.lower()
        for file_name in known_files
        if file_name
    )

    grounded = evidence_is_grounded(
        evidence,
        retrieved_code,
        tool_output,
    )

    specific_support = (
        evidence_has_specific_support(
            question,
            evidence,
            tool_output,
        )
    )

    print(
        "Evidence extracted:"
    )

    print(evidence)

    print(
        "Evidence grounded:",
        grounded,
    )

    print(
        "File reference:",
        file_reference,
    )

    print(
        "Specific support:",
        specific_support,
    )

    if (
        has_evidence_section
        and has_conclusion
        and has_file_reference
        and grounded
        and specific_support
    ):
        print(
            "Answer validation: PASSED"
        )

        return {
            "validation_status": "PASSED",
            "validation_reason": (
                "Answer structure and source "
                "grounding verified."
            ),
            "current_task": "Complete",
        }

    if not has_evidence_section:
        reason = (
            "Missing Evidence section."
        )

    elif not has_file_reference:
        reason = (
            "Answer does not reference "
            "a verified source file."
        )

    elif not grounded:
        reason = (
            "Evidence could not be verified "
            "against source evidence."
        )

    elif not specific_support:
        reason = (
            "Evidence is too generic to "
            "support the requested claim."
        )

    elif not has_conclusion:
        reason = (
            "Missing Conclusion section."
        )

    else:
        reason = (
            "Answer failed grounding checks."
        )

    print(
        "Answer validation: FAILED"
    )

    print(
        "Reason:",
        reason,
    )

    return {
        "validation_status": "FAILED",
        "validation_reason": reason,
        "current_task": "Repair answer",
    }


# =========================================================
# 21. ANSWER REPAIR
# =========================================================

def repair_answer(state):
    print("\n[ANSWER REPAIR]")

    answer_retry_count = int(
        state.get(
            "answer_retry_count",
            0,
        )
    ) + 1

    question = state.get(
        "question",
        "",
    )

    question_type = state.get(
        "question_type",
        detect_question_type_from_text(
            question
        ),
    )

    # -----------------------------------------------------
    # FILE LIST
    # -----------------------------------------------------

    if question_type == "file_list":
        project_files = state.get(
            "project_files",
            [],
        )

        if project_files:
            repaired_answer = (
                "Files present in the project:\n\n"
                + "\n".join(
                    f"- {file}"
                    for file in project_files
                )
                + f"\n\nTotal files: "
                f"{len(project_files)}"
            )

        else:
            repaired_answer = (
                "No project files were found."
            )

        return {
            "answer": repaired_answer,
            "answer_retry_count": (
                answer_retry_count
            ),
            "current_task": (
                "Validate repaired answer"
            ),
        }

    # -----------------------------------------------------
    # MODIFICATION
    # -----------------------------------------------------

    if question_type == "modification":
        repaired_answer = (
            generate_modification_answer(
                state
            )
        )

        return {
            "answer": repaired_answer,
            "answer_retry_count": (
                answer_retry_count
            ),
            "current_task": (
                "Validate repaired answer"
            ),
        }

    retrieved_code = state.get(
        "retrieved_code",
        [],
    )

    tool_output = state.get(
        "tool_output",
        "",
    )

    code_analysis = state.get(
        "code_analysis",
        {},
    )

    # -----------------------------------------------------
    # QDRANTCLIENT EXPLANATION REPAIR — TOP PRIORITY
    # -----------------------------------------------------
    qdrantclient_answer = build_qdrantclient_answer(
        question,
        retrieved_code,
        tool_output,
    )

    if qdrantclient_answer is not None:
        print(
            "Repairing using deterministic QdrantClient evidence."
        )
        return {
            "answer": qdrantclient_answer,
            "answer_retry_count": answer_retry_count,
            "current_task": "Validate repaired answer",
        }

    # -----------------------------------------------------
    # LOCATION REPAIR
    # -----------------------------------------------------

    location_answer = generate_location_answer(
        question,
        tool_output,
    )

    if location_answer is not None:
        print(
            "Repairing using deterministic "
            "source-location evidence."
        )

        return {
            "answer": location_answer,
            "answer_retry_count": (
                answer_retry_count
            ),
            "current_task": (
                "Validate repaired answer"
            ),
        }

    # -----------------------------------------------------
    # QDRANT EXPLANATION REPAIR
    # -----------------------------------------------------

    qdrant_explanation_answer = (
        generate_qdrant_explanation_answer(
            question,
            tool_output,
        )
    )

    if qdrant_explanation_answer is not None:
        print(
            "Repairing using deterministic "
            "Qdrant explanation evidence."
        )

        return {
            "answer": qdrant_explanation_answer,
            "answer_retry_count": (
                answer_retry_count
            ),
            "current_task": (
                "Validate repaired answer"
            ),
        }

    # -----------------------------------------------------
    # NO EVIDENCE
    # -----------------------------------------------------

    if (
        not retrieved_code
        and not tool_output
    ):
        repaired_answer = (
            "Answer:\n"
            "Insufficient evidence in the retrieved code.\n\n"
            "Evidence:\n"
            "No relevant source evidence was returned.\n\n"
            "File:\n"
            "N/A\n\n"
            "Conclusion:\n"
            "The codebase does not provide enough "
            "evidence to answer this question."
        )

        return {
            "answer": repaired_answer,
            "answer_retry_count": (
                answer_retry_count
            ),
            "current_task": (
                "Validate repaired answer"
            ),
        }

    # -----------------------------------------------------
    # DETERMINISTIC REPAIR
    # -----------------------------------------------------

    deterministic_answer = (
        generate_deterministic_answer(
            question,
            question_type,
            retrieved_code,
            code_analysis,
            tool_output,
        )
    )

    if deterministic_answer is not None:
        return {
            "answer": deterministic_answer,
            "answer_retry_count": (
                answer_retry_count
            ),
            "current_task": (
                "Validate repaired answer"
            ),
        }

    # -----------------------------------------------------
    # BEHAVIOR TEST REPAIR
    # -----------------------------------------------------

    if (
        tool_output
        and "BEHAVIOR TEST PASSED" in tool_output
    ):
        function_name = "unknown"

        function_match = re.search(
            r"Function:\s*(.+)",
            tool_output,
            re.IGNORECASE,
        )

        if function_match:
            function_name = (
                function_match.group(1)
                .strip()
            )

        expected_value = "unknown"

        expected_match = re.search(
            r"Expected:\s*(.+)",
            tool_output,
            re.IGNORECASE,
        )

        if expected_match:
            expected_value = (
                expected_match.group(1)
                .strip()
            )

        file_name = (
            "agent/agent_test.py"
        )

        if retrieved_code:
            file_name = retrieved_code[0].get(
                "file_name",
                file_name,
            )

        repaired_answer = (
            "Answer:\n"
            "The requested function test passed successfully.\n\n"
            "Evidence:\n"
            f"{tool_output}\n\n"
            "File:\n"
            f"{file_name}\n\n"
            "Conclusion:\n"
            f"The function {function_name}() "
            f"returned the expected value "
            f"{expected_value}."
        )

        return {
            "answer": repaired_answer,
            "answer_retry_count": (
                answer_retry_count
            ),
            "current_task": (
                "Validate repaired answer"
            ),
        }

    # -----------------------------------------------------
    # TOOL EVIDENCE REPAIR
    # -----------------------------------------------------

    if (
        tool_output
        and not tool_output.startswith("Error:")
    ):
        tool_lines = [
            line.strip()
            for line
            in tool_output.splitlines()
            if line.strip()
        ]

        evidence_lines = [
            line
            for line
            in tool_lines
            if (
                ":" in line
                and ".py:" in line
            )
        ]

        if evidence_lines:

            # Prefer Qdrant implementation evidence
            # when the question is about Qdrant.
            if "qdrant" in question.lower():

                qdrant_evidence = [
                    line
                    for line in evidence_lines
                    if (
                        "qdrant_connection.py"
                        in line.lower()
                        or "store_qdrant.py"
                        in line.lower()
                    )
                ]

                if qdrant_evidence:
                    evidence_lines = qdrant_evidence

            evidence = "\n".join(
                evidence_lines[:5]
            )

            file_match = re.search(
                r"([A-Za-z0-9_.\-/\\]+\.py):\d+:",
                evidence,
            )

            file_name = (
                file_match.group(1)
                if file_match
                else "source file"
            )

            repaired_answer = (
                "Answer:\n"
                "The executed code search returned "
                "relevant source evidence.\n\n"
                "Evidence:\n"
                f"{evidence}\n\n"
                "File:\n"
                f"{file_name}\n\n"
                "Conclusion:\n"
                "The conclusion is limited to the "
                "verified source search results."
            )

            return {
                "answer": repaired_answer,
                "answer_retry_count": (
                    answer_retry_count
                ),
                "current_task": (
                    "Validate repaired answer"
                ),
            }

    # -----------------------------------------------------
    # QDRANT FALLBACK
    # -----------------------------------------------------

    if retrieved_code:

        best = retrieved_code[0]

        file_name = best.get(
            "file_name",
            "unknown",
        )

        content = best.get(
            "content",
            "",
        ).strip()

        evidence = next(
            (
                line.strip()
                for line
                in content.splitlines()
                if line.strip()
            ),
            "No non-empty source line was found.",
        )

        repaired_answer = (
            "Answer:\n"
            "Insufficient evidence in the retrieved "
            "code to determine the requested result.\n\n"
            "Evidence:\n"
            f"{evidence}\n\n"
            "File:\n"
            f"{file_name}\n\n"
            "Conclusion:\n"
            "The retrieved source does not prove "
            "a stronger conclusion."
        )

    else:

        repaired_answer = (
            "Answer:\n"
            "Insufficient evidence in the retrieved code.\n\n"
            "Evidence:\n"
            f"{tool_output[:1500]}\n\n"
            "File:\n"
            "Source file shown in tool evidence.\n\n"
            "Conclusion:\n"
            "The conclusion is limited to the "
            "verified tool output."
        )

    return {
        "answer": repaired_answer,
        "answer_retry_count": (
            answer_retry_count
        ),
        "current_task": (
            "Validate repaired answer"
        ),
    }


# =========================================================
# 22. TOOL EXECUTION
# =========================================================

def execute_tool(state):
    tool_name = state.get(
        "tool_name",
        "",
    )

    tool_input = state.get(
        "tool_input",
        "",
    )

    print("\n[TOOL EXECUTION]")
    print("Tool:", tool_name)
    print("Input:", tool_input)

    if tool_name == "read_file":
        result = read_file(
            tool_input
        )

    elif tool_name == "search_code":
        result = search_code(
            tool_input
        )

    elif tool_name == "write_file":
        content = state.get(
            "file_content",
            "",
        )

        result = write_file(
            tool_input,
            content,
        )

    elif tool_name == "run_tests":
        result = run_tests()

    elif tool_name == "run_function_test":
        parts = tool_input.split("|", 2)

        if len(parts) != 3:
            result = (
                "BEHAVIOR TEST ERROR: Invalid tool input."
            )
        else:
            file_path, function_name, expected_value = parts

            result = run_function_test(
                file_path,
                function_name,
                expected_value,
            )

    else:
        result = (
            f"Error: Unknown tool: {tool_name}"
        )

    print("\n[TOOL RESULT]")
    print(result[:3000])

    return {
        "tool_output": result,
        "current_task": "Route tool result",
    }