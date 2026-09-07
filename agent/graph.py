from langgraph.graph import StateGraph, START, END

from agent.state import AgentState

from agent.nodes import (
    analyze_question,
    route_question,
    codebase_search_node,
    check_relevance,
    rewrite_query,
    analyze_code,
    generate_answer,
    validate_answer,
    repair_answer,
)


# ============================================================
# ROUTER DECISION
# ============================================================

def router_decision(state):

    route = state.get(
        "route",
        "CODEBASE"
    )

    print("\n[ROUTER DECISION]")
    print("Route selected:", route)

    if route == "CODEBASE":
        return "codebase_search"

    return "codebase_search"


# ============================================================
# RELEVANCE DECISION
# ============================================================

def relevance_decision(state):

    relevance = state.get(
        "relevance",
        "BAD"
    )

    retry_count = state.get(
        "search_retry_count",
        0
    )

    print("\n[RELEVANCE ROUTER]")

    print(
        "Best score:",
        state.get(
            "best_score",
            0.0
        )
    )

    print(
        "Retry count:",
        retry_count
    )

    if relevance == "GOOD":

        print("Decision: GOOD")

        return "analyze_code"

    if retry_count >= 1:

        print(
            "Decision: Retry limit reached → analyze code"
        )

        return "analyze_code"

    print(
        "Decision: BAD → rewrite query"
    )

    return "rewrite_query"


# ============================================================
# VALIDATION DECISION
# ============================================================

def validation_decision(state):

    validation_status = state.get(
        "validation_status",
        "FAILED"
    )

    retry_count = state.get(
        "answer_retry_count",
        0
    )

    print("\n[VALIDATION ROUTER]")

    print(
        "Validation status:",
        validation_status
    )

    print(
        "Answer retry count:",
        retry_count
    )

    if validation_status == "PASSED":

        print(
            "Decision: PASS → END"
        )

        return "end"

    if retry_count < 1:

        print(
            "Decision: FAIL → REPAIR ANSWER"
        )

        return "repair_answer"

    print(
        "Decision: Retry limit reached → END"
    )

    return "end"


# ============================================================
# BUILD GRAPH
# ============================================================

def build_graph():

    print("\n[GRAPH] Building LangGraph...")

    workflow = StateGraph(
        AgentState
    )

    # ========================================================
    # ADD NODES
    # ========================================================

    workflow.add_node(
        "analyzer",
        analyze_question
    )

    workflow.add_node(
        "router",
        route_question
    )

    workflow.add_node(
        "codebase_search",
        codebase_search_node
    )

    workflow.add_node(
        "relevance",
        check_relevance
    )

    workflow.add_node(
        "rewrite_query",
        rewrite_query
    )

    workflow.add_node(
        "analyze_code",
        analyze_code
    )

    workflow.add_node(
        "generate_answer",
        generate_answer
    )

    workflow.add_node(
        "validate_answer",
        validate_answer
    )

    workflow.add_node(
        "repair_answer",
        repair_answer
    )

    # ========================================================
    # START → ANALYZER
    # ========================================================

    workflow.add_edge(
        START,
        "analyzer"
    )

    # ========================================================
    # ANALYZER → ROUTER
    # ========================================================

    workflow.add_edge(
        "analyzer",
        "router"
    )

    # ========================================================
    # ROUTER → CODEBASE SEARCH
    # ========================================================

    workflow.add_conditional_edges(
        "router",
        router_decision,
        {
            "codebase_search": "codebase_search"
        }
    )

    # ========================================================
    # SEARCH → RELEVANCE
    # ========================================================

    workflow.add_edge(
        "codebase_search",
        "relevance"
    )

    # ========================================================
    # RELEVANCE → ANALYZE / REWRITE
    # ========================================================

    workflow.add_conditional_edges(
        "relevance",
        relevance_decision,
        {
            "analyze_code": "analyze_code",
            "rewrite_query": "rewrite_query"
        }
    )

    # ========================================================
    # REWRITE → SEARCH AGAIN
    # ========================================================

    workflow.add_edge(
        "rewrite_query",
        "codebase_search"
    )

    # ========================================================
    # ANALYZE → GENERATE
    # ========================================================

    workflow.add_edge(
        "analyze_code",
        "generate_answer"
    )

    # ========================================================
    # GENERATE → VALIDATE
    # ========================================================

    workflow.add_edge(
        "generate_answer",
        "validate_answer"
    )

    # ========================================================
    # VALIDATE → REPAIR / END
    # ========================================================

    workflow.add_conditional_edges(
        "validate_answer",
        validation_decision,
        {
            "repair_answer": "repair_answer",
            "end": END
        }
    )

    # ========================================================
    # REPAIR → VALIDATE
    # ========================================================

    workflow.add_edge(
        "repair_answer",
        "validate_answer"
    )

    # ========================================================
    # COMPILE
    # ========================================================

    app = workflow.compile()

    print(
        "[GRAPH] Graph compiled successfully."
    )

    # THIS IS IMPORTANT
    return app