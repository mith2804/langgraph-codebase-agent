from typing import TypedDict, List, Dict, Any


class AgentState(TypedDict):

    question: str

    plan: List[str]
    current_task: str

    route: str

    # Search
    search_query: str

    # Qdrant results
    retrieved_code: List[Dict[str, Any]]

    # Relevance
    relevance_score: float
    relevance_reason: str

    # Retry mechanism
    retry_count: int

    # Analysis
    analysis: str

    # Final answer
    answer: str