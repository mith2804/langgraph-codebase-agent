from typing import TypedDict, List, Dict, Any


class AgentState(TypedDict, total=False):

    # =====================================================
    # USER REQUEST
    # =====================================================

    question: str

    # =====================================================
    # PLANNING
    # =====================================================

    plan: List[str]
    current_task: str

    # =====================================================
    # ROUTING
    # =====================================================

    route: str
    question_type: str

    # =====================================================
    # RETRIEVAL
    # =====================================================

    search_query: str
    retrieved_code: List[Dict[str, Any]]
    retrieval_results: List[Dict[str, Any]]

    # =====================================================
    # RELEVANCE
    # =====================================================

    relevance_score: float
    relevance_reason: str
    retry_count: int
    best_score: float

    # =====================================================
    # PROJECT FILE LIST
    # =====================================================
    #
    # Used when the user asks:
    # "What files are present?"
    # "List project files"
    # "Which files are in the project?"
    #
    # This is populated by list_project_files()
    # and consumed by generate_answer().
    # =====================================================

    project_files: List[str]
    file_list_error: str

    # =====================================================
    # CODE ANALYSIS
    # =====================================================

    code_analysis: Dict[str, Any]

    # =====================================================
    # MODIFICATION PLANNING
    # =====================================================

    modification_plan: Dict[str, Any]

    # =====================================================
    # MODIFICATION EXECUTION
    # =====================================================

    target_file: str
    target_function: str

    original_code: str
    modified_code: str

    modification_reason: str
    modification_status: str
    modification_result: str

    # =====================================================
    # TOOL EXECUTION
    # =====================================================

    tool_name: str
    tool_input: str
    tool_output: str

    # =====================================================
    # TESTING
    # =====================================================

    test_output: str
    test_status: str
    test_retry_count: int

    # =====================================================
    # ANSWER
    # =====================================================

    answer: str

    # =====================================================
    # VALIDATION
    # =====================================================

    validation_status: str
    validation_reason: str
    answer_retry_count: int

