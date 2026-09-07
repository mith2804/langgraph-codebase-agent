import re
import torch

from transformers import AutoTokenizer, AutoModelForCausalLM

from agent.retriever import search_codebase


# ============================================================
# QUESTION ANALYSIS
# ============================================================

def analyze_question(state):

    question = state.get("question", "").strip()

    print("\n[ANALYZER]")
    print("Question:", question)

    state["question"] = question

    return state


# ============================================================
# ROUTER
# ============================================================

def route_question(state):

    question = state.get("question", "").lower()

    print("\n[ROUTER]")
    print("Deciding what to do...")

    code_keywords = [
        "code",
        "file",
        "function",
        "functions",
        "class",
        "classes",
        "variable",
        "import",
        "imports",
        "method",
        "methods",
        "defined",
        "implementation",
        "error",
        "bug",
        "exception",
        "line",
        ".py",
        ".js",
        ".ts",
        ".java",
    ]

    if any(keyword in question for keyword in code_keywords):

        route = "CODEBASE"

    else:

        route = "GENERAL"

    print("Route:", route)

    state["route"] = route

    return state


# ============================================================
# CODEBASE SEARCH
# ============================================================

def codebase_search_node(state):

    question = state.get("question", "")

    print("\n[CODEBASE SEARCH]")
    print("Searching codebase for:", question)

    try:

        # Retrieve more chunks so filename-based questions
        # can inspect the complete file.
        results = search_codebase(
            question,
            limit=20,
        )

    except Exception as e:

        print("\n[CODEBASE SEARCH ERROR]")
        print(e)

        results = []

    state["retrieved_code"] = results

    return state


# ============================================================
# RELEVANCE CHECK
# ============================================================

def check_relevance(state):

    results = state.get(
        "retrieved_code",
        []
    )

    print("\n[RELEVANCE CHECK]")

    if not results:

        print("No retrieval results found.")

        state["relevance"] = "BAD"

        return state

    scores = []

    for result in results:

        score = result.get(
            "score",
            0.0
        )

        scores.append(score)

    best_score = max(scores)

    print(
        f"Best retrieval score: "
        f"{best_score:.8f}"
    )

    # Threshold
    if best_score >= 0.20:

        decision = "GOOD"

        print(
            "Decision: Retrieved code is relevant."
        )

    else:

        decision = "BAD"

        print(
            "Decision: Retrieved code may not be relevant."
        )

    state["relevance"] = decision
    state["best_score"] = best_score

    return state


# ============================================================
# QUERY REWRITE
# ============================================================

def rewrite_query(state):

    question = state.get(
        "question",
        ""
    )

    retry_count = state.get(
        "search_retry_count",
        0
    )

    print("\n[QUERY REWRITE]")

    print(
        "Original question:",
        question
    )

    # IMPORTANT:
    # Do not replace the user's question with
    # an unrelated hardcoded query.
    #
    # We simply make the query slightly more
    # retrieval-friendly on retry.

    rewritten_query = (
        f"{question} "
        f"source code implementation"
    )

    print(
        "Rewritten query:",
        rewritten_query
    )

    state["search_query"] = rewritten_query

    state["search_retry_count"] = (
        retry_count + 1
    )

    return state


# ============================================================
# CODE ANALYSIS
# ============================================================

def analyze_code(state):

    results = state.get(
        "retrieved_code",
        []
    )

    print("\n[CODE ANALYZER]")

    analysis = []

    for result in results:

        file_name = result.get(
            "file_name",
            "unknown"
        )

        score = result.get(
            "score",
            0.0
        )

        content = result.get(
            "content",
            ""
        )

        print(
            f"Analyzing {file_name} "
            f"(chunk={result.get('chunk_index', -1)}, "
            f"score={score:.8f})"
        )

        analysis.append({
            "file_name": file_name,
            "score": score,
            "content": content,
            "chunk_index": result.get(
                "chunk_index",
                -1
            ),
        })

    state["code_analysis"] = analysis

    return state


# ============================================================
# QUESTION TYPE DETECTION
# ============================================================

def detect_question_type(question):

    question_lower = question.lower()

    if (
        "what functions" in question_lower
        or "which functions" in question_lower
        or "functions defined" in question_lower
        or "function defined" in question_lower
        or "list functions" in question_lower
        or "functions in" in question_lower
    ):

        return "functions"

    if (
        "what classes" in question_lower
        or "which classes" in question_lower
        or "classes defined" in question_lower
        or "class defined" in question_lower
        or "list classes" in question_lower
    ):

        return "classes"

    if (
        "what imports" in question_lower
        or "which imports" in question_lower
        or "libraries imported" in question_lower
        or "imports in" in question_lower
    ):

        return "imports"

    return "general"


# ============================================================
# EXTRACT FUNCTION DEFINITIONS
# ============================================================

def extract_function_definitions(retrieved_code):

    functions = {}

    # Sort chunks in source order.
    sorted_results = sorted(
        retrieved_code,
        key=lambda x: x.get(
            "chunk_index",
            0
        )
    )

    pattern = re.compile(
        r"(?m)^[ \t]*(async[ \t]+def|def)"
        r"[ \t]+([A-Za-z_][A-Za-z0-9_]*)"
        r"[ \t]*\("
    )

    for result in sorted_results:

        content = result.get(
            "content",
            ""
        )

        matches = pattern.finditer(
            content
        )

        for match in matches:

            function_type = match.group(1)
            function_name = match.group(2)

            declaration = (
                f"{function_type} "
                f"{function_name}("
            )

            if function_name not in functions:

                functions[function_name] = {
                    "name": function_name,
                    "declaration": declaration,
                }

    return list(
        functions.values()
    )


# ============================================================
# EXTRACT CLASS DEFINITIONS
# ============================================================

def extract_class_definitions(retrieved_code):

    classes = {}

    sorted_results = sorted(
        retrieved_code,
        key=lambda x: x.get(
            "chunk_index",
            0
        )
    )

    pattern = re.compile(
        r"(?m)^[ \t]*class[ \t]+"
        r"([A-Za-z_][A-Za-z0-9_]*)"
    )

    for result in sorted_results:

        content = result.get(
            "content",
            ""
        )

        matches = pattern.finditer(
            content
        )

        for match in matches:

            class_name = match.group(1)

            declaration = (
                f"class {class_name}"
            )

            if class_name not in classes:

                classes[class_name] = {
                    "name": class_name,
                    "declaration": declaration,
                }

    return list(
        classes.values()
    )


# ============================================================
# EXTRACT IMPORTS
# ============================================================

def extract_imports(retrieved_code):

    imports = []

    seen = set()

    sorted_results = sorted(
        retrieved_code,
        key=lambda x: x.get(
            "chunk_index",
            0
        )
    )

    pattern = re.compile(
        r"(?m)^[ \t]*(?:from[ \t]+.+[ \t]+import[ \t]+.+|import[ \t]+.+)$"
    )

    for result in sorted_results:

        content = result.get(
            "content",
            ""
        )

        matches = pattern.findall(
            content
        )

        for line in matches:

            line = line.strip()

            if line not in seen:

                seen.add(line)

                imports.append(line)

    return imports


# ============================================================
# GENERATE ANSWER
# ============================================================

def generate_answer(state):

    question = state.get(
        "question",
        ""
    )

    retrieved_code = state.get(
        "retrieved_code",
        []
    )

    print("\n[ANSWER GENERATOR]")

    question_type = detect_question_type(
        question
    )

    print(
        "Detected question type:",
        question_type
    )

    # ========================================================
    # FUNCTION QUESTION
    # ========================================================

    if question_type == "functions":

        functions = extract_function_definitions(
            retrieved_code
        )

        file_names = []

        for result in retrieved_code:

            file_name = result.get(
                "file_name",
                ""
            )

            if (
                file_name
                and file_name not in file_names
            ):

                file_names.append(
                    file_name
                )

        if functions:

            function_lines = []

            evidence_lines = []

            for function in functions:

                function_name = function["name"]

                function_lines.append(
                    f"- {function_name}()"
                )

                evidence_lines.append(
                    function["declaration"]
                )

            file_name = (
                file_names[0]
                if file_names
                else "retrieved source"
            )

            answer = (
                "Root Cause:\n"
                "Not applicable. "
                "The question asks for functions "
                "defined in the source code.\n\n"

                "Evidence:\n"
                + "\n".join(evidence_lines)
                + "\n\n"

                "Functions:\n"
                + "\n".join(function_lines)
                + "\n\n"

                "File:\n"
                + file_name
                + "\n\n"

                "Conclusion:\n"
                "The functions listed above were "
                "extracted directly from the "
                "retrieved source code."
            )

        else:

            answer = (
                "Root Cause:\n"
                "Not applicable.\n\n"

                "Evidence:\n"
                "No function definitions were found "
                "in the retrieved source chunks.\n\n"

                "File:\n"
                "Unknown\n\n"

                "Conclusion:\n"
                "The retrieved source did not contain "
                "a verifiable function definition."
            )

        print(
            "\nGenerated Answer:"
        )

        print(answer)

        state["answer"] = answer

        return state

    # ========================================================
    # CLASS QUESTION
    # ========================================================

    if question_type == "classes":

        classes = extract_class_definitions(
            retrieved_code
        )

        file_name = (
            retrieved_code[0].get(
                "file_name",
                "Unknown"
            )
            if retrieved_code
            else "Unknown"
        )

        if classes:

            class_lines = []

            evidence_lines = []

            for class_item in classes:

                class_name = class_item["name"]

                class_lines.append(
                    f"- {class_name}"
                )

                evidence_lines.append(
                    class_item["declaration"]
                )

            answer = (
                "Root Cause:\n"
                "Not applicable. "
                "The question asks for classes "
                "defined in the source code.\n\n"

                "Evidence:\n"
                + "\n".join(evidence_lines)
                + "\n\n"

                "Classes:\n"
                + "\n".join(class_lines)
                + "\n\n"

                "File:\n"
                + file_name
                + "\n\n"

                "Conclusion:\n"
                "The classes listed above were "
                "extracted directly from the "
                "retrieved source code."
            )

        else:

            answer = (
                "Root Cause:\n"
                "Not applicable.\n\n"

                "Evidence:\n"
                "No class definitions were found "
                "in the retrieved source chunks.\n\n"

                "File:\n"
                + file_name
                + "\n\n"

                "Conclusion:\n"
                "No verifiable class definition "
                "was found."
            )

        print(
            "\nGenerated Answer:"
        )

        print(answer)

        state["answer"] = answer

        return state

    # ========================================================
    # IMPORT QUESTION
    # ========================================================

    if question_type == "imports":

        imports = extract_imports(
            retrieved_code
        )

        file_name = (
            retrieved_code[0].get(
                "file_name",
                "Unknown"
            )
            if retrieved_code
            else "Unknown"
        )

        if imports:

            answer = (
                "Root Cause:\n"
                "Not applicable. "
                "The question asks about imports "
                "in the source code.\n\n"

                "Evidence:\n"
                + "\n".join(imports)
                + "\n\n"

                "File:\n"
                + file_name
                + "\n\n"

                "Conclusion:\n"
                "The imports listed above were "
                "found directly in the retrieved "
                "source code."
            )

        else:

            answer = (
                "Root Cause:\n"
                "Not applicable.\n\n"

                "Evidence:\n"
                "No import statements were found "
                "in the retrieved source.\n\n"

                "File:\n"
                + file_name
                + "\n\n"

                "Conclusion:\n"
                "No verifiable imports were found."
            )

        print(
            "\nGenerated Answer:"
        )

        print(answer)

        state["answer"] = answer

        return state

    # ========================================================
    # GENERAL QUESTION → QWEN
    # ========================================================

    print(
        "Using Qwen for general code analysis..."
    )

    if not retrieved_code:

        answer = (
            "Root Cause:\n"
            "No relevant code was retrieved.\n\n"

            "Evidence:\n"
            "The codebase search did not return "
            "verifiable source code.\n\n"

            "File:\n"
            "Unknown\n\n"

            "Conclusion:\n"
            "Unable to answer from the available "
            "codebase evidence."
        )

        state["answer"] = answer

        return state

    # --------------------------------------------------------
    # Build source context
    # --------------------------------------------------------

    source_parts = []

    for result in retrieved_code:

        file_name = result.get(
            "file_name",
            "unknown"
        )

        chunk_index = result.get(
            "chunk_index",
            -1
        )

        content = result.get(
            "content",
            ""
        )

        source_parts.append(
            f"FILE: {file_name}\n"
            f"CHUNK: {chunk_index}\n"
            f"{content}"
        )

    source_context = "\n\n".join(
        source_parts
    )

    # Keep prompt size manageable.
    source_context = source_context[
        :12000
    ]

    model_name = (
        "Qwen/Qwen2.5-0.5B-Instruct"
    )

    try:

        tokenizer = AutoTokenizer.from_pretrained(
            model_name
        )

        model = AutoModelForCausalLM.from_pretrained(
            model_name,
            torch_dtype=torch.float32
        )

        prompt = f"""
You are a codebase analysis assistant.

Answer the user's question using ONLY
the retrieved source code.

Do not invent files, functions,
classes, variables, errors, or behavior.

User question:
{question}

Retrieved source code:
{source_context}

Return the answer in exactly this structure:

Root Cause:
<answer or Not applicable>

Evidence:
<specific evidence copied or closely grounded
in the retrieved source code>

File:
<file name>

Conclusion:
<final answer>

Be precise and source-grounded.
"""

        inputs = tokenizer(
            prompt,
            return_tensors="pt"
        )

        with torch.no_grad():

            outputs = model.generate(
                **inputs,
                max_new_tokens=400,
                temperature=0.1,
                do_sample=False,
            )

        generated_text = tokenizer.decode(
            outputs[0],
            skip_special_tokens=True
        )

        # Remove prompt if Qwen repeats it.
        if generated_text.startswith(prompt):

            generated_text = generated_text[
                len(prompt):
            ]

        answer = generated_text.strip()

        if not answer:

            raise ValueError(
                "Qwen returned an empty answer."
            )

    except Exception as e:

        print(
            "\n[QWEN ERROR]"
        )

        print(e)

        # Safe fallback using actual source.
        first_result = retrieved_code[0]

        file_name = first_result.get(
            "file_name",
            "Unknown"
        )

        content = first_result.get(
            "content",
            ""
        ).strip()

        evidence = content[:500]

        answer = (
            "Root Cause:\n"
            "Unable to generate a detailed "
            "LLM answer.\n\n"

            "Evidence:\n"
            + evidence
            + "\n\n"

            "File:\n"
            + file_name
            + "\n\n"

            "Conclusion:\n"
            "The answer could not be fully generated, "
            "but the retrieved source evidence is "
            "shown above."
        )

    print(
        "\nGenerated Answer:"
    )

    print(answer)

    state["answer"] = answer

    return state


# ============================================================
# NORMALIZE TEXT
# ============================================================

def normalize_text(text):

    if not text:

        return ""

    text = text.lower()

    text = re.sub(
        r"\s+",
        " ",
        text
    )

    return text.strip()


# ============================================================
# EXTRACT EVIDENCE SECTION
# ============================================================

def extract_evidence(answer):

    if not answer:

        return ""

    match = re.search(
        r"Evidence:\s*(.*?)(?:\n\s*File:|\n\s*Conclusion:|$)",
        answer,
        flags=re.IGNORECASE | re.DOTALL
    )

    if match:

        return match.group(1).strip()

    return ""


# ============================================================
# EVIDENCE GROUNDING
# ============================================================

def evidence_is_grounded(
    evidence,
    retrieved_code
):

    if not evidence:

        return False

    if not retrieved_code:

        return False

    # --------------------------------------------------------
    # Build complete retrieved source
    # --------------------------------------------------------

    all_code = "\n".join(
        result.get(
            "content",
            ""
        )
        for result in retrieved_code
    )

    normalized_code = normalize_text(
        all_code
    )

    # --------------------------------------------------------
    # Check each evidence line
    # --------------------------------------------------------

    evidence_lines = []

    for line in evidence.splitlines():

        line = line.strip()

        if not line:

            continue

        # Remove markdown bullets.
        line = re.sub(
            r"^[-*]\s*",
            "",
            line
        )

        evidence_lines.append(
            line.strip()
        )

    if not evidence_lines:

        return False

    grounded_count = 0

    for line in evidence_lines:

        normalized_line = normalize_text(
            line
        )

        if not normalized_line:

            continue

        # Exact source match.
        if normalized_line in normalized_code:

            grounded_count += 1

            continue

        # For function names like:
        # analyze_question()
        #
        # source may contain:
        # def analyze_question(state):
        #
        # Therefore compare the function name.
        function_match = re.search(
            r"(?:async\s+)?def\s+"
            r"([A-Za-z_][A-Za-z0-9_]*)",
            line
        )

        if not function_match:

            function_match = re.search(
                r"\b([A-Za-z_][A-Za-z0-9_]*)\s*\(\)",
                line
            )

        if function_match:

            function_name = (
                function_match.group(1)
            )

            function_pattern = re.compile(
                r"\bdef\s+"
                + re.escape(function_name)
                + r"\s*\("
            )

            if function_pattern.search(
                all_code
            ):

                grounded_count += 1

                continue

        # Token overlap fallback.
        tokens = re.findall(
            r"[A-Za-z_][A-Za-z0-9_]+",
            normalized_line
        )

        if tokens:

            matched_tokens = sum(
                1
                for token in tokens
                if token in normalized_code
            )

            overlap = (
                matched_tokens
                / len(tokens)
            )

            if overlap >= 0.50:

                grounded_count += 1

    return (
        grounded_count >= 1
    )


# ============================================================
# VALIDATE ANSWER
# ============================================================

def validate_answer(state):

    answer = state.get(
        "answer",
        ""
    )

    question = state.get(
        "question",
        ""
    )

    retrieved_code = state.get(
        "retrieved_code",
        []
    )

    print("\n[VALIDATOR]")

    evidence = extract_evidence(
        answer
    )

    print(
        "\nEvidence extracted:"
    )

    print(evidence)

    grounded = evidence_is_grounded(
        evidence,
        retrieved_code
    )

    print(
        "\nEvidence grounded:",
        grounded
    )

    question_type = detect_question_type(
        question
    )

    validation_passed = False

    reason = ""

    # ========================================================
    # FUNCTION VALIDATION
    # ========================================================

    if question_type == "functions":

        expected_functions = (
            extract_function_definitions(
                retrieved_code
            )
        )

        expected_names = [
            item["name"]
            for item in expected_functions
        ]

        answer_normalized = normalize_text(
            answer
        )

        missing_functions = []

        for function_name in expected_names:

            if (
                function_name.lower()
                not in answer_normalized
            ):

                missing_functions.append(
                    function_name
                )

        if expected_names and not missing_functions:

            validation_passed = True

            reason = (
                "All function definitions "
                "visible in the retrieved source "
                "were found in the answer and "
                "the evidence is grounded."
            )

        elif not expected_names:

            validation_passed = False

            reason = (
                "No function definitions could "
                "be verified in the retrieved source."
            )

        else:

            validation_passed = False

            reason = (
                "Some retrieved function definitions "
                "were missing from the answer: "
                + ", ".join(
                    missing_functions
                )
            )

    # ========================================================
    # NORMAL VALIDATION
    # ========================================================

    else:

        file_name_ok = True

        retrieved_file_names = []

        for result in retrieved_code:

            file_name = result.get(
                "file_name",
                ""
            )

            if file_name:

                retrieved_file_names.append(
                    file_name.lower()
                )

        if (
            retrieved_file_names
            and "file:" in answer.lower()
        ):

            file_match = re.search(
                r"File:\s*([^\n]+)",
                answer,
                flags=re.IGNORECASE
            )

            if file_match:

                answer_file = (
                    file_match.group(1)
                    .strip()
                    .lower()
                )

                file_name_ok = any(
                    answer_file == file_name
                    or answer_file in file_name
                    or file_name in answer_file
                    for file_name
                    in retrieved_file_names
                )

        if grounded and file_name_ok:

            validation_passed = True

            reason = (
                "Answer contains grounded "
                "evidence from the retrieved "
                "source code."
            )

        elif not grounded:

            validation_passed = False

            reason = (
                "Evidence could not be verified "
                "against the retrieved code."
            )

        else:

            validation_passed = False

            reason = (
                "The answer references a file "
                "that was not present in the "
                "retrieved source."
            )

    if validation_passed:

        status = "PASSED"

    else:

        status = "FAILED"

    print(
        "\nAnswer validation:",
        status
    )

    print(
        "Reason:",
        reason
    )

    state["validation_status"] = status

    state["validation_reason"] = reason

    state["validation_passed"] = (
        validation_passed
    )

    return state


# ============================================================
# REPAIR ANSWER
# ============================================================

def repair_answer(state):

    question = state.get(
        "question",
        ""
    )

    retrieved_code = state.get(
        "retrieved_code",
        []
    )

    print("\n[ANSWER REPAIR]")

    question_type = detect_question_type(
        question
    )

    # ========================================================
    # REPAIR FUNCTION QUESTION
    # ========================================================

    if question_type == "functions":

        functions = extract_function_definitions(
            retrieved_code
        )

        file_name = (
            retrieved_code[0].get(
                "file_name",
                "Unknown"
            )
            if retrieved_code
            else "Unknown"
        )

        if functions:

            evidence_lines = []

            function_lines = []

            for function in functions:

                evidence_lines.append(
                    function["declaration"]
                )

                function_lines.append(
                    f"- {function['name']}()"
                )

            repaired_answer = (
                "Root Cause:\n"
                "Not applicable. "
                "The question asks for functions "
                "defined in the source code.\n\n"

                "Evidence:\n"
                + "\n".join(evidence_lines)
                + "\n\n"

                "Functions:\n"
                + "\n".join(function_lines)
                + "\n\n"

                "File:\n"
                + file_name
                + "\n\n"

                "Conclusion:\n"
                "These function definitions were "
                "extracted directly from the "
                "retrieved source code."
            )

        else:

            repaired_answer = (
                "Root Cause:\n"
                "Not applicable.\n\n"

                "Evidence:\n"
                "No function definitions were found "
                "in the retrieved source.\n\n"

                "File:\n"
                + file_name
                + "\n\n"

                "Conclusion:\n"
                "No function definitions could "
                "be verified."
            )

        print(
            "\nRepaired Answer:"
        )

        print(repaired_answer)

        state["answer"] = repaired_answer

        return state

    # ========================================================
    # GENERIC REPAIR
    # ========================================================

    if retrieved_code:

        result = retrieved_code[0]

        file_name = result.get(
            "file_name",
            "Unknown"
        )

        content = result.get(
            "content",
            ""
        ).strip()

        evidence = content[:700]

        repaired_answer = (
            "Root Cause:\n"
            "The previous answer could not be "
            "verified completely.\n\n"

            "Evidence:\n"
            + evidence
            + "\n\n"

            "File:\n"
            + file_name
            + "\n\n"

            "Conclusion:\n"
            "The answer has been repaired using "
            "the retrieved source evidence."
        )

    else:

        repaired_answer = (
            "Root Cause:\n"
            "No relevant code was retrieved.\n\n"

            "Evidence:\n"
            "No source evidence is available.\n\n"

            "File:\n"
            "Unknown\n\n"

            "Conclusion:\n"
            "Unable to provide a source-grounded "
            "answer."
        )

    print(
        "\nRepaired Answer:"
    )

    print(repaired_answer)

    state["answer"] = repaired_answer

    return state