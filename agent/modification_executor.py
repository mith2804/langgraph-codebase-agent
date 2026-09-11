
from typing import Dict, Any
import re
import torch

from agent.tools import read_file, write_file
from agent.model import get_qwen_model


# ============================================================
# 1. GENERATE MODIFIED CODE
# ============================================================

def generate_modified_code(
    original_code: str,
    target_file: str,
    target_function: str,
    user_request: str,
) -> str:

    request_lower = user_request.lower()

    # --------------------------------------------------------
    # SIMPLE MODIFICATION
    # Add a comment at the top of a Python file
    # --------------------------------------------------------

    if (
        "add a comment at the top" in request_lower
        and target_file.endswith(".py")
    ):
        match = re.search(
            r'saying\s+["\'](.+?)["\']',
            user_request,
            re.IGNORECASE,
        )

        if match:
            comment_text = match.group(1)

            print(
                "[MODIFICATION] Detected simple comment addition."
            )

            modified_code = (
                f"# {comment_text}\n"
                f"{original_code}"
            )

            return modified_code

    # --------------------------------------------------------
    # SIMPLE MODIFICATION
    # Add a function to a Python file
    # --------------------------------------------------------

    function_match = re.search(
        r"(?:add|create|implement|define)\s+"
        r"(?:a\s+)?function\s+"
        r"(?:called|named)\s+"
        r"([A-Za-z_][A-Za-z0-9_]*)"
        r".*?"
        r"returns?\s+['\"](.+?)['\"]",
        user_request,
        re.IGNORECASE,
    )

    if (
        function_match
        and target_file.endswith(".py")
    ):
        function_name = function_match.group(1)
        return_value = function_match.group(2)

        print(
            "[MODIFICATION] Detected simple function addition."
        )

        function_pattern = (
            rf"^\s*def\s+{re.escape(function_name)}\s*\("
        )

        if re.search(
            function_pattern,
            original_code,
            re.MULTILINE,
        ):
            print(
                f"[MODIFICATION] Function '{function_name}' "
                "already exists."
            )

            return original_code

        function_code = (
            f"\n\n"
            f"def {function_name}():\n"
            f"    return '{return_value}'\n"
        )

        modified_code = (
            original_code.rstrip()
            + function_code
        )

        return modified_code

    # --------------------------------------------------------
    # FALLBACK
    # Complex modification -> Qwen
    # --------------------------------------------------------

    print(
        "[MODIFICATION] Complex modification detected."
    )

    tokenizer, model = get_qwen_model()

    prompt = f"""
You are a careful Python code modification agent.

Modify the existing source code according to the user's request.

IMPORTANT RULES:

1. Return ONLY the complete modified source code.
2. Do NOT return markdown.
3. Do NOT use code fences.
4. Do NOT explain the changes.
5. Preserve ALL existing functionality.
6. Make ONLY the requested modification.
7. Do NOT remove existing functions.
8. Do NOT remove existing imports unless explicitly requested.
9. Do NOT invent unrelated code.
10. Do NOT create unrelated functions or files.
11. Preserve the original structure whenever possible.
12. Return a complete source file.

Target file:
{target_file}

Target function:
{target_function}

User request:
{user_request}

Original source code:
{original_code}

Return ONLY the complete modified source code.
"""

    inputs = tokenizer(
        prompt,
        return_tensors="pt",
        truncation=True,
        max_length=4096,
    )

    with torch.no_grad():
        outputs = model.generate(
            **inputs,
            max_new_tokens=3000,
            do_sample=False,
            pad_token_id=tokenizer.eos_token_id,
        )

    generated = tokenizer.decode(
        outputs[0],
        skip_special_tokens=True,
    )

    if generated.startswith(prompt):
        generated = generated[len(prompt):]

    generated = generated.strip()

    if generated.startswith("```python"):
        generated = generated[len("```python"):].strip()

    elif generated.startswith("```"):
        generated = generated[3:].strip()

    if generated.endswith("```"):
        generated = generated[:-3].strip()

    return generated


# ============================================================
# 2. VALIDATE GENERATED CODE
# ============================================================

def validate_generated_code(
    code: str,
    target_function: str = "",
    user_request: str = "",
) -> Dict[str, Any]:

    if not code or not code.strip():
        return {
            "valid": False,
            "reason": "Generated code is empty.",
        }

    try:
        compile(
            code,
            "<generated_code>",
            "exec",
        )

    except SyntaxError as e:
        return {
            "valid": False,
            "reason": (
                f"Generated code has syntax error: "
                f"{e.msg} at line {e.lineno}"
            ),
        }

    except Exception as e:
        return {
            "valid": False,
            "reason": (
                f"Code validation error: {e}"
            ),
        }

    # --------------------------------------------------------
    # Validate requested function
    # --------------------------------------------------------

    if target_function:

        function_pattern = (
            rf"^\s*def\s+"
            rf"{re.escape(target_function)}"
            rf"\s*\("
        )

        function_found = re.search(
            function_pattern,
            code,
            re.MULTILINE,
        )

        if not function_found:

            return {
                "valid": False,
                "reason": (
                    f"Requested function "
                    f"'{target_function}' "
                    f"was not found in generated code."
                ),
            }

    return {
        "valid": True,
        "reason": (
            "Generated code passed Python syntax "
            "and requested-function validation."
        ),
    }


# ============================================================
# 3. EXECUTE MODIFICATION
# ============================================================

def execute_modification(state) -> Dict[str, Any]:

    print("\n" + "=" * 60)
    print("[MODIFICATION EXECUTOR]")
    print("=" * 60)

    modification_plan = state.get(
        "modification_plan",
        {},
    )

    target_files = modification_plan.get(
        "target_files",
        [],
    )

    target_functions = modification_plan.get(
        "target_functions",
        [],
    )

    user_request = modification_plan.get(
        "user_request",
        state.get("question", ""),
    )

    print(
        "User request:",
        user_request,
    )

    print(
        "Target files:",
        target_files,
    )

    print(
        "Target functions:",
        target_functions,
    )

    # --------------------------------------------------------
    # 1. CHECK TARGET FILE
    # --------------------------------------------------------

    if not target_files:
        print(
            "[MODIFICATION] No target file found."
        )

        return {
            "modification_status": "FAILED",
            "modification_reason": (
                "No target file was identified "
                "for modification."
            ),
            "current_task": "Modification failed",
        }

    target_file = target_files[0]

    target_function = (
        target_functions[0]
        if target_functions
        else ""
    )

    print(
        "Target file:",
        target_file,
    )

    print(
        "Target function:",
        target_function,
    )

    # --------------------------------------------------------
    # 2. READ ORIGINAL FILE
    # --------------------------------------------------------

    print(
        "\n[MODIFICATION] Reading original file..."
    )

    original_code = read_file(
        target_file
    )

    if original_code.startswith("Error:"):
        print(
            "[MODIFICATION] Failed to read file."
        )

        return {
            "target_file": target_file,
            "original_code": "",
            "modified_code": "",
            "modification_status": "FAILED",
            "modification_reason": original_code,
            "current_task": "Modification failed",
        }

    print(
        "[MODIFICATION] Original file loaded."
    )

    print(
        "[MODIFICATION] Original code length:",
        len(original_code),
    )

    # --------------------------------------------------------
    # 3. GENERATE / APPLY MODIFICATION
    # --------------------------------------------------------

    print(
        "\n[MODIFICATION] Generating modified code..."
    )

    try:
        modified_code = generate_modified_code(
            original_code=original_code,
            target_file=target_file,
            target_function=target_function,
            user_request=user_request,
        )

    except Exception as e:
        print(
            "[MODIFICATION] Code generation failed:",
            e,
        )

        return {
            "target_file": target_file,
            "original_code": original_code,
            "modified_code": "",
            "modification_status": "FAILED",
            "modification_reason": (
                f"Failed to generate modified code: {e}"
            ),
            "current_task": "Modification failed",
        }

    print(
        "[MODIFICATION] Generated code length:",
        len(modified_code),
    )

    # --------------------------------------------------------
    # 4. VALIDATE SYNTAX + REQUESTED FUNCTION
    # --------------------------------------------------------

    print(
        "\n[MODIFICATION] Validating generated code..."
    )

    validation = validate_generated_code(
        code=modified_code,
        target_function=target_function,
        user_request=user_request,
    )

    print(
        "[MODIFICATION] Validation valid:",
        validation["valid"],
    )

    print(
        "[MODIFICATION] Validation reason:",
        validation["reason"],
    )

    if not validation["valid"]:
        return {
            "target_file": target_file,
            "target_function": target_function,
            "original_code": original_code,
            "modified_code": modified_code,
            "modification_status": "FAILED",
            "modification_reason": validation["reason"],
            "current_task": "Modification failed",
        }

    # --------------------------------------------------------
    # 5. CHECK THAT SOMETHING CHANGED
    # --------------------------------------------------------

    if modified_code == original_code:
        print(
            "[MODIFICATION] No code change generated."
        )

        return {
            "target_file": target_file,
            "target_function": target_function,
            "original_code": original_code,
            "modified_code": modified_code,
            "modification_status": "FAILED",
            "modification_reason": (
                "Generated code is identical "
                "to the original code."
            ),
            "current_task": "Modification failed",
        }

    # --------------------------------------------------------
    # 6. WRITE MODIFIED FILE
    # --------------------------------------------------------

    print(
        "\n[MODIFICATION] Writing modified file..."
    )

    write_result = write_file(
        target_file,
        modified_code,
    )

    print(
        "[MODIFICATION] Write result:"
    )

    print(write_result)

    if write_result.startswith("Error:"):
        return {
            "target_file": target_file,
            "target_function": target_function,
            "original_code": original_code,
            "modified_code": modified_code,
            "modification_status": "FAILED",
            "modification_reason": write_result,
            "current_task": "Modification failed",
        }

    # --------------------------------------------------------
    # 7. VERIFY WRITTEN FILE
    # --------------------------------------------------------

    print(
        "\n[MODIFICATION] Verifying written file..."
    )

    try:
        verification_code = read_file(
            target_file
        )

        if verification_code != modified_code:
            print(
                "[MODIFICATION] Verification failed."
            )

            return {
                "target_file": target_file,
                "target_function": target_function,
                "original_code": original_code,
                "modified_code": modified_code,
                "modification_status": "FAILED",
                "modification_reason": (
                    "File was written but verification "
                    "did not match the generated code."
                ),
                "current_task": "Modification failed",
            }

        print(
            "[MODIFICATION] Verification successful."
        )

    except Exception as e:
        print(
            "[MODIFICATION] Verification error:",
            e,
        )

        return {
            "target_file": target_file,
            "target_function": target_function,
            "original_code": original_code,
            "modified_code": modified_code,
            "modification_status": "FAILED",
            "modification_reason": (
                f"Verification failed: {e}"
            ),
            "current_task": "Modification failed",
        }

    # --------------------------------------------------------
    # 8. SUCCESS
    # --------------------------------------------------------

    print(
        "\n[MODIFICATION] File modified successfully."
    )

    return {
        "target_file": target_file,
        "target_function": target_function,
        "original_code": original_code,
        "modified_code": modified_code,
        "modification_status": "MODIFIED",
        "modification_reason": (
            "Code was modified, syntax validated, "
            "requested function validated, written "
            "successfully, and verified."
        ),
        "current_task": "Run tests after modification",
    }

