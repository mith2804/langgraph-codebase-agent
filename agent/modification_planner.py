from typing import Dict, Any
import re


def create_modification_plan(state) -> Dict[str, Any]:

    question = state.get("question", "").strip()

    retrieved_code = state.get(
        "retrieved_code",
        []
    )

    code_analysis = state.get(
        "code_analysis",
        {}
    )

    print("\n[MODIFICATION PLANNER]")

    print("User request:")
    print(question)

    question_lower = question.lower()

    # =====================================================
    # TARGET FILES
    # =====================================================

    target_files = []

    analysis_files = code_analysis.get(
        "files",
        []
    )

    for file_name in analysis_files:
        if file_name not in target_files:
            target_files.append(file_name)

    # Detect file path directly from user question
    path_pattern = (
        r"(?:[\w.-]+[\\/])+[\w.-]+\."
        r"(?:py|js|jsx|ts|tsx|java|cpp|c|h|hpp|cs|go|rs|php|rb|swift|kt|kts|"
        r"html|css|scss|json|yaml|yml|md|txt)\b"
    )

    detected_paths = re.findall(
        path_pattern,
        question,
        flags=re.IGNORECASE
    )

    # Preserve complete relative path
    for file_path in detected_paths:

        file_path = file_path.replace("\\", "/")

        if file_path not in target_files:
            target_files.append(file_path)

    # If no path was detected, detect filename only
    if not detected_paths:

        filename_pattern = (
            r"\b[\w.-]+\."
            r"(?:py|js|jsx|ts|tsx|java|cpp|c|h|hpp|cs|go|rs|php|rb|swift|kt|kts|"
            r"html|css|scss|json|yaml|yml|md|txt)\b"
        )

        detected_files = re.findall(
            filename_pattern,
            question,
            flags=re.IGNORECASE
        )

        for file_name in detected_files:

            if file_name not in target_files:
                target_files.append(file_name)

    # Detect file from retrieved Qdrant results
    for item in retrieved_code:

        file_name = item.get(
            "file_name",
            ""
        )

        if file_name and file_name not in target_files:
            target_files.append(file_name)

    # =====================================================
    # TARGET FUNCTIONS
    # =====================================================

    target_functions = []

    analysis_functions = code_analysis.get(
        "functions",
        []
    )

    # Existing functions mentioned in question
    for function_name in analysis_functions:

        if function_name.lower() in question_lower:

            if function_name not in target_functions:
                target_functions.append(function_name)

    # -----------------------------------------------------
    # Detect newly requested function
    # -----------------------------------------------------

    function_patterns = [
        r"(?:add|create|implement|define)\s+"
        r"(?:a\s+)?function\s+"
        r"(?:called|named)\s+"
        r"([A-Za-z_][A-Za-z0-9_]*)",

        r"(?:add|create|implement|define)\s+"
        r"(?:a\s+)?function\s+"
        r"([A-Za-z_][A-Za-z0-9_]*)",
    ]

    for pattern in function_patterns:

        match = re.search(
            pattern,
            question,
            flags=re.IGNORECASE
        )

        if match:

            new_function = match.group(1)

            if new_function not in target_functions:
                target_functions.append(new_function)

            break

    # =====================================================
    # DETECT MODIFICATION KEYWORDS
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

    detected_keywords = [
        keyword
        for keyword in modification_keywords
        if keyword in question_lower
    ]

    # =====================================================
    # BUILD PLAN
    # =====================================================

    plan = {

        "user_request": question,

        "target_files": target_files,

        "target_functions": target_functions,

        "changes": [
            question
        ] if question else [],

        "detected_keywords": detected_keywords,

        "reason": (
            "Modify only the relevant project files "
            "according to the user's request."
        ),

        "validation": (
            "Run tests after modification and verify "
            "the requested behavior."
        ),

        "retrieved_chunks": len(
            retrieved_code
        ),
    }

    # =====================================================
    # PRINT PLAN
    # =====================================================

    print(
        "\nTarget files:",
        plan["target_files"]
    )

    print(
        "Target functions:",
        plan["target_functions"]
    )

    print(
        "Detected modification keywords:",
        plan["detected_keywords"]
    )

    print(
        "Changes:",
        plan["changes"]
    )

    print(
        "Reason:",
        plan["reason"]
    )

    print(
        "Validation:",
        plan["validation"]
    )

    return {
        "modification_plan": plan,
        "current_task": "Select engineering tool",
    }