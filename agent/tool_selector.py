
import re


# ============================================================
# TOOL SELECTOR
# ============================================================

def select_tool(state):
    question = state.get("question", "")
    question_lower = question.lower().strip()

    modification_status = state.get(
        "modification_status",
        "",
    )

    # --------------------------------------------------------
    # Helper: extract Python file path
    # --------------------------------------------------------

    def extract_file_path(text):
        match = re.search(
            r"([A-Za-z0-9_./\\\-]+\.py)\b",
            text,
            re.IGNORECASE,
        )

        if not match:
            return None

        file_path = match.group(1)

        # Known agent files can be referenced without "agent/"
        if (
            "\\" not in file_path
            and "/" not in file_path
        ):
            agent_files = {
                "nodes.py",
                "graph.py",
                "tools.py",
                "retriever.py",
                "state.py",
                "qdrant_connection.py",
                "test_runner.py",
                "tool_selector.py",
                "modification_planner.py",
                "modification_executor.py",
                "model.py",
                "agent_test.py",
            }

            if file_path in agent_files:
                file_path = f"agent/{file_path}"

        return file_path

    # --------------------------------------------------------
    # Helper: detect READ / ANALYSIS request
    # --------------------------------------------------------

    analysis_keywords = [
        "read",
        "show",
        "open",
        "content",
        "functions",
        "function",
        "classes",
        "class",
        "imports",
        "import",
        "defined",
        "definition",
        "what does",
        "explain",
        "contains",
        "list",
    ]

    is_analysis_request = any(
        keyword in question_lower
        for keyword in analysis_keywords
    )

    # --------------------------------------------------------
    # Helper: detect explicit test request
    # --------------------------------------------------------

    explicit_test_keywords = [
        "run test",
        "run tests",
        "run pytest",
        "execute test",
        "execute tests",
        "test the",
        "test whether",
        "test if",
        "verify that",
        "verify whether",
        "check whether",
        "check if",
    ]

    is_explicit_test_request = any(
        keyword in question_lower
        for keyword in explicit_test_keywords
    )

    # ========================================================
    # 1. MODIFICATION COMPLETED
    # ========================================================

    if modification_status == "MODIFIED":

        tool_name = "run_tests"
        tool_input = ""

        print("\n[TOOL SELECTOR]")
        print("Modification completed.")
        print("Next tool: run_tests")

        return {
            "tool_name": tool_name,
            "tool_input": tool_input,
        }

    # ========================================================
    # 2. SPECIFIC FUNCTION BEHAVIOR TEST
    # ========================================================

    is_behavior_test = (
        is_explicit_test_request
        and (
            "returns" in question_lower
            or "return" in question_lower
        )
    )

    if is_behavior_test:

        file_path = extract_file_path(question)

        function_match = re.search(
            r"\b([A-Za-z_][A-Za-z0-9_]*)\s*\(\)",
            question,
        )

        expected_match = re.search(
            r"\breturns?\s+['\"]([^'\"]*)['\"]",
            question,
            re.IGNORECASE,
        )

        if (
            file_path
            and function_match
            and expected_match
        ):

            function_name = function_match.group(1)
            expected_value = expected_match.group(1)

            tool_name = "run_function_test"

            tool_input = (
                f"{file_path}|"
                f"{function_name}|"
                f"{expected_value}"
            )

        else:

            tool_name = "run_tests"
            tool_input = ""

    # ========================================================
    # 3. READ / ANALYSIS REQUEST
    #
    # IMPORTANT:
    # This comes BEFORE generic test detection.
    #
    # Example:
    # "What functions are defined in agent/agent_test.py?"
    #
    # The word "test" exists inside "agent_test.py".
    # We must NOT interpret that as a test request.
    # ========================================================

    elif is_analysis_request:

        file_path = extract_file_path(question)

        if file_path:

            tool_name = "read_file"
            tool_input = file_path

        else:

            tool_name = "search_code"
            tool_input = question

    # ========================================================
    # 4. EXPLICIT GENERAL TEST REQUEST
    # ========================================================

    elif is_explicit_test_request:

        tool_name = "run_tests"
        tool_input = ""

    # ========================================================
    # 5. SEARCH REQUEST
    # ========================================================

    elif any(
        keyword in question_lower
        for keyword in [
            "search",
            "find",
            "where is",
            "which file",
            "locate",
        ]
    ):

        tool_name = "search_code"

        search_terms = []

        if "qdrant" in question_lower:
            search_terms.append("QdrantClient")

        if "qdrant_url" in question_lower:
            search_terms.append("QDRANT_URL")

        if "qdrant_api_key" in question_lower:
            search_terms.append("QDRANT_API_KEY")

        if "embedding" in question_lower:
            search_terms.append("SentenceTransformer")

        if "langgraph" in question_lower:
            search_terms.append("StateGraph")

        if (
            "llm" in question_lower
            or "qwen" in question_lower
        ):
            search_terms.append("Qwen")

        if search_terms:
            tool_input = " ".join(search_terms)
        else:
            tool_input = question

    # ========================================================
    # 6. DEFAULT
    # ========================================================

    else:

        tool_name = "search_code"

        search_terms = []

        if "qdrant" in question_lower:
            search_terms.append("QdrantClient")

        if "qdrant_url" in question_lower:
            search_terms.append("QDRANT_URL")

        if "qdrant_api_key" in question_lower:
            search_terms.append("QDRANT_API_KEY")

        if "embedding" in question_lower:
            search_terms.append("SentenceTransformer")

        if "langgraph" in question_lower:
            search_terms.append("StateGraph")

        if "qwen" in question_lower:
            search_terms.append("Qwen")

        if search_terms:
            tool_input = " ".join(search_terms)
        else:
            tool_input = question

    # ========================================================
    # DEBUG OUTPUT
    # ========================================================

    print("\n[TOOL SELECTOR]")
    print("Tool:", tool_name)
    print("Input:", tool_input)

    return {
        "tool_name": tool_name,
        "tool_input": tool_input,
    }

