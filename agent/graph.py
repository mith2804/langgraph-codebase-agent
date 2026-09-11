from pathlib import Path

from langgraph.graph import StateGraph, START, END

from agent.state import AgentState

from agent.nodes import (
    analyze_question,
    route_question,
    codebase_search_node,
    check_relevance,
    rewrite_query,
    analyze_code,
    execute_tool,
    generate_answer,
    validate_answer,
    repair_answer,
)

from agent.tool_selector import select_tool
from agent.modification_planner import create_modification_plan
from agent.modification_executor import execute_modification


# =========================================================
# CONSTANTS
# =========================================================

MAX_SEARCH_RETRIES = 1
MAX_ANSWER_RETRIES = 1

RELEVANCE_THRESHOLD = 0.20


# =========================================================
# ROUTER DECISION
# =========================================================

def router_decision(state):

    question_type = state.get(
        "question_type",
        "general",
    )

    route = state.get(
        "route",
        "CODEBASE",
    )

    print("\n[ROUTER DECISION]")

    print(
        "Route selected:",
        route,
    )

    # -----------------------------------------------------
    # FILE LIST
    # -----------------------------------------------------

    if question_type == "file_list":

        print(
            "Decision: FILE LIST "
            "-> list_project_files"
        )

        return "list_project_files"

    # -----------------------------------------------------
    # NORMAL CODEBASE FLOW
    # -----------------------------------------------------

    print(
        "Decision: CODEBASE "
        "-> codebase_search"
    )

    return "codebase_search"


# =========================================================
# RELEVANCE DECISION
# =========================================================

def relevance_decision(state):

    relevance_score = float(
        state.get(
            "relevance_score",
            0.0,
        )
    )

    retry_count = int(
        state.get(
            "retry_count",
            0,
        )
    )

    print("\n[RELEVANCE ROUTER]")

    print(
        "Best score:",
        relevance_score,
    )

    print(
        "Retry count:",
        retry_count,
    )

    # -----------------------------------------------------
    # GOOD RELEVANCE
    # -----------------------------------------------------

    if relevance_score >= RELEVANCE_THRESHOLD:

        print(
            "Decision: GOOD -> question type routing"
        )

        return "question_type_router"

    # -----------------------------------------------------
    # RETRY LIMIT
    # -----------------------------------------------------

    if retry_count >= MAX_SEARCH_RETRIES:

        print(
            "Decision: Retry limit reached "
            "-> question type routing"
        )

        return "question_type_router"

    # -----------------------------------------------------
    # BAD RELEVANCE
    # -----------------------------------------------------

    print(
        "Decision: BAD -> rewrite query"
    )

    return "rewrite_query"


# =========================================================
# QUESTION TYPE DECISION
# =========================================================

def question_type_decision(state):

    question_type = state.get(
        "question_type",
        "general",
    )

    question = state.get(
        "question",
        "",
    ).lower()

    print("\n[QUESTION TYPE ROUTER]")

    print(
        "Question type:",
        question_type,
    )

    # =====================================================
    # FILE LIST
    # =====================================================

    if question_type == "file_list":

        print(
            "Decision: FILE LIST "
            "-> list_project_files"
        )

        return "list_project_files"

    # =====================================================
    # MODIFICATION
    # =====================================================

    modification_keywords = [
        "modify",
        "change",
        "update",
        "edit",
        "fix",
        "add",
        "remove",
        "delete",
        "implement",
        "create",
        "rewrite",
        "refactor",
        "replace",
    ]

    is_modification = any(
        keyword in question
        for keyword in modification_keywords
    )

    if (
        question_type == "modification"
        or is_modification
    ):

        print(
            "Decision: MODIFICATION "
            "-> modification planner"
        )

        return "modification_planner"

    # =====================================================
    # NORMAL CODE QUESTION
    # =====================================================

    print(
        "Decision: READ / ANALYSIS "
        "-> select tool"
    )

    return "select_tool"


# =========================================================
# MODIFICATION EXECUTOR DECISION
# =========================================================

def modification_executor_decision(state):

    status = state.get(
        "modification_status",
        "FAILED",
    )

    print("\n[MODIFICATION ROUTER]")

    print(
        "Modification status:",
        status,
    )

    # -----------------------------------------------------
    # SUCCESS
    # -----------------------------------------------------

    if status == "MODIFIED":

        print(
            "Decision: MODIFIED -> select tool"
        )

        return "select_tool"

    # -----------------------------------------------------
    # FAILURE
    # -----------------------------------------------------

    print(
        "Decision: MODIFICATION FAILED "
        "-> generate answer"
    )

    return "generate_answer"


# =========================================================
# TOOL DECISION
# =========================================================

def tool_decision(state):

    tool_name = state.get(
        "tool_name",
        "",
    )

    print("\n[TOOL ROUTER]")

    print(
        "Selected tool:",
        tool_name,
    )

    executable_tools = {
        "read_file",
        "search_code",
        "run_tests",
        "run_function_test",
        "write_file",
    }

    if tool_name in executable_tools:

        print(
            "Decision: Valid tool -> execute_tool"
        )

        return "execute_tool"

    print(
        "Decision: Invalid tool "
        "-> analyze_code"
    )

    return "analyze_code"


# =========================================================
# TOOL RESULT DECISION
# =========================================================

def tool_result_decision(state):

    tool_name = state.get(
        "tool_name",
        "",
    )

    print("\n[TOOL RESULT ROUTER]")

    print(
        "Tool executed:",
        tool_name,
    )

    # -----------------------------------------------------
    # READ FILE
    # -----------------------------------------------------

    if tool_name == "read_file":

        print(
            "Decision: READ FILE -> analyze_code"
        )

        return "analyze_code"

    # -----------------------------------------------------
    # SEARCH CODE
    # -----------------------------------------------------

    if tool_name == "search_code":

        print(
            "Decision: SEARCH CODE "
            "-> generate_answer"
        )

        return "generate_answer"

    # -----------------------------------------------------
    # RUN TESTS
    # -----------------------------------------------------

    if tool_name == "run_tests":

        print(
            "Decision: TESTS COMPLETED "
            "-> generate_answer"
        )

        return "generate_answer"

    # -----------------------------------------------------
    # WRITE FILE
    # -----------------------------------------------------

    if tool_name == "write_file":

        print(
            "Decision: FILE WRITTEN "
            "-> generate_answer"
        )

        return "generate_answer"

    # -----------------------------------------------------
    # FALLBACK
    # -----------------------------------------------------

    print(
        "Decision: FALLBACK "
        "-> generate_answer"
    )

    return "generate_answer"


# =========================================================
# LIST PROJECT FILES
# =========================================================

def list_project_files(state):

    print("\n[FILE LIST TOOL]")
    print("Reading actual project directory...")

    # -----------------------------------------------------
    # Project root
    #
    # graph.py is:
    #
    # project/
    #     agent/
    #         graph.py
    #
    # Therefore parent.parent = project root.
    # -----------------------------------------------------

    project_root = (
        Path(__file__)
        .resolve()
        .parent
        .parent
    )

    print(
        "Project root:",
        project_root,
    )

    # -----------------------------------------------------
    # Directories to ignore
    # -----------------------------------------------------

    ignored_dirs = {
        ".git",
        ".venv",
        "venv",
        "__pycache__",
        "node_modules",
        ".pytest_cache",
    }

    # -----------------------------------------------------
    # Sensitive files to ignore
    # -----------------------------------------------------

    ignored_files = {
        ".env",
    }

    files = []

    # -----------------------------------------------------
    # Scan filesystem
    # -----------------------------------------------------

    try:

        for path in project_root.rglob("*"):

            if not path.is_file():
                continue

            relative_path = (
                path.relative_to(
                    project_root
                )
            )

            # -------------------------------------------------
            # Ignore directories
            # -------------------------------------------------

            if any(
                part in ignored_dirs
                for part in relative_path.parts
            ):
                continue

            # -------------------------------------------------
            # Ignore sensitive files
            # -------------------------------------------------

            if path.name in ignored_files:
                continue

            # -------------------------------------------------
            # Add relative path
            # -------------------------------------------------

            files.append(
                str(
                    relative_path
                ).replace(
                    "\\",
                    "/",
                )
            )

    except Exception as e:

        print(
            "[FILE LIST ERROR]",
            e,
        )

        return {
            "project_files": [],
            "file_list_error": str(e),
            "question_type": "file_list",
            "current_task": "Generate answer",
        }

    # -----------------------------------------------------
    # Sort files
    # -----------------------------------------------------

    files.sort()

    # -----------------------------------------------------
    # Print files
    # -----------------------------------------------------

    print(
        f"Found {len(files)} actual project files."
    )

    for file in files:

        print(
            " -",
            file,
        )

    # -----------------------------------------------------
    # Return state
    # -----------------------------------------------------

    return {
        "project_files": files,
        "file_list_error": "",
        "question_type": "file_list",
        "current_task": "Generate answer",
    }


# =========================================================
# VALIDATION DECISION
# =========================================================

def validation_decision(state):

    validation_status = state.get(
        "validation_status",
        "FAILED",
    )

    answer_retry_count = int(
        state.get(
            "answer_retry_count",
            0,
        )
    )

    print("\n[VALIDATION ROUTER]")

    print(
        "Validation status:",
        validation_status,
    )

    print(
        "Answer retry count:",
        answer_retry_count,
    )

    # -----------------------------------------------------
    # SUCCESS
    # -----------------------------------------------------

    if validation_status == "PASSED":

        print(
            "Decision: PASS -> END"
        )

        return "end"

    # -----------------------------------------------------
    # RETRY
    # -----------------------------------------------------

    if answer_retry_count < MAX_ANSWER_RETRIES:

        print(
            "Decision: FAIL "
            "-> repair_answer"
        )

        return "repair_answer"

    # -----------------------------------------------------
    # HARD STOP
    # -----------------------------------------------------

    print(
        "Decision: Retry limit reached "
        "-> END"
    )

    return "end"


# =========================================================
# BUILD GRAPH
# =========================================================

def build_graph():

    print(
        "\n[GRAPH] Building LangGraph..."
    )

    workflow = StateGraph(
        AgentState
    )

    # =====================================================
    # NODES
    # =====================================================

    workflow.add_node(
        "analyzer",
        analyze_question,
    )

    workflow.add_node(
        "router",
        route_question,
    )

    workflow.add_node(
        "codebase_search",
        codebase_search_node,
    )

    workflow.add_node(
        "relevance",
        check_relevance,
    )

    workflow.add_node(
        "rewrite_query",
        rewrite_query,
    )

    workflow.add_node(
        "question_type_router",
        lambda state: state,
    )

    workflow.add_node(
        "list_project_files",
        list_project_files,
    )

    workflow.add_node(
        "modification_planner",
        create_modification_plan,
    )

    workflow.add_node(
        "modification_executor",
        execute_modification,
    )

    workflow.add_node(
        "select_tool",
        select_tool,
    )

    workflow.add_node(
        "execute_tool",
        execute_tool,
    )

    workflow.add_node(
        "analyze_code",
        analyze_code,
    )

    workflow.add_node(
        "generate_answer",
        generate_answer,
    )

    workflow.add_node(
        "validate_answer",
        validate_answer,
    )

    workflow.add_node(
        "repair_answer",
        repair_answer,
    )

    # =====================================================
    # START
    # =====================================================

    workflow.add_edge(
        START,
        "analyzer",
    )

    # =====================================================
    # ANALYZER -> ROUTER
    # =====================================================

    workflow.add_edge(
        "analyzer",
        "router",
    )

    # =====================================================
    # ROUTER
    #
    # FILE LIST:
    #     router -> list_project_files
    #
    # NORMAL:
    #     router -> codebase_search
    # =====================================================

    workflow.add_conditional_edges(
        "router",
        router_decision,
        {
            "codebase_search":
                "codebase_search",

            "list_project_files":
                "list_project_files",
        },
    )

    # =====================================================
    # SEARCH -> RELEVANCE
    # =====================================================

    workflow.add_edge(
        "codebase_search",
        "relevance",
    )

    # =====================================================
    # RELEVANCE
    # =====================================================

    workflow.add_conditional_edges(
        "relevance",
        relevance_decision,
        {
            "question_type_router":
                "question_type_router",

            "rewrite_query":
                "rewrite_query",
        },
    )

    # =====================================================
    # REWRITE -> SEARCH
    # =====================================================

    workflow.add_edge(
        "rewrite_query",
        "codebase_search",
    )

    # =====================================================
    # QUESTION TYPE ROUTER
    # =====================================================

    workflow.add_conditional_edges(
        "question_type_router",
        question_type_decision,
        {
            "select_tool":
                "select_tool",

            "modification_planner":
                "modification_planner",

            "list_project_files":
                "list_project_files",
        },
    )

    # =====================================================
    # FILE LIST -> ANSWER
    # =====================================================

    workflow.add_edge(
        "list_project_files",
        "generate_answer",
    )

    # =====================================================
    # MODIFICATION PLANNER -> EXECUTOR
    # =====================================================

    workflow.add_edge(
        "modification_planner",
        "modification_executor",
    )

    # =====================================================
    # MODIFICATION EXECUTOR
    # =====================================================

    workflow.add_conditional_edges(
        "modification_executor",
        modification_executor_decision,
        {
            "select_tool":
                "select_tool",

            "generate_answer":
                "generate_answer",
        },
    )

    # =====================================================
    # TOOL SELECTOR
    # =====================================================

    workflow.add_conditional_edges(
        "select_tool",
        tool_decision,
        {
            "execute_tool":
                "execute_tool",

            "analyze_code":
                "analyze_code",
        },
    )

    # =====================================================
    # TOOL EXECUTION
    # =====================================================

    workflow.add_conditional_edges(
        "execute_tool",
        tool_result_decision,
        {
            "analyze_code":
                "analyze_code",

            "generate_answer":
                "generate_answer",
        },
    )

    # =====================================================
    # ANALYZE CODE -> ANSWER
    # =====================================================

    workflow.add_edge(
        "analyze_code",
        "generate_answer",
    )

    # =====================================================
    # ANSWER -> VALIDATION
    # =====================================================

    workflow.add_edge(
        "generate_answer",
        "validate_answer",
    )

    # =====================================================
    # VALIDATION
    # =====================================================

    workflow.add_conditional_edges(
        "validate_answer",
        validation_decision,
        {
            "repair_answer":
                "repair_answer",

            "end":
                END,
        },
    )

    # =====================================================
    # REPAIR -> VALIDATION
    # =====================================================

    workflow.add_edge(
        "repair_answer",
        "validate_answer",
    )

    # =====================================================
    # COMPILE
    # =====================================================

    app = workflow.compile()

    print(
        "[GRAPH] Graph compiled successfully."
    )

    return app