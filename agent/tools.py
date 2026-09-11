from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parent.parent


IGNORED_DIRS = {
    ".git",
    ".venv",
    "venv",
    "__pycache__",
    "node_modules",
    ".pytest_cache",
}


ALLOWED_EXTENSIONS = {
    ".py",
    ".js",
    ".ts",
    ".jsx",
    ".tsx",
    ".java",
    ".cpp",
    ".c",
    ".h",
    ".hpp",
    ".cs",
    ".go",
    ".rs",
    ".php",
    ".rb",
    ".swift",
    ".kt",
    ".kts",
    ".html",
    ".css",
    ".json",
    ".yaml",
    ".yml",
    ".md",
    ".txt",
}


def _safe_project_path(
    file_path: str
) -> tuple[Path | None, str | None]:

    if not file_path or not file_path.strip():
        return None, "Error: File path cannot be empty."

    try:
        target = (
            PROJECT_ROOT / file_path
        ).resolve()

    except Exception as e:
        return None, f"Error: Invalid file path: {e}"

    try:
        target.relative_to(PROJECT_ROOT)

    except ValueError:
        return (
            None,
            "Error: Access outside the project directory is not allowed."
        )

    return target, None


def read_file(file_path: str) -> str:

    target, error = _safe_project_path(file_path)

    if error:
        return error

    if target is None:
        return "Error: Invalid file path."

    if not target.exists():
        return f"Error: File not found: {file_path}"

    if not target.is_file():
        return f"Error: Not a file: {file_path}"

    if target.name == ".env":
        return "Error: Reading .env is not allowed."

    try:
        return target.read_text(
            encoding="utf-8"
        )

    except UnicodeDecodeError:
        return f"Error: Could not decode file: {file_path}"

    except PermissionError:
        return f"Error: Permission denied: {file_path}"

    except Exception as e:
        return f"Error reading file: {e}"


def search_code(query: str) -> str:

    if not query or not query.strip():
        return "Error: Search query cannot be empty."

    query = query.strip()

    terms = [
        term.strip().lower()
        for term in query.split()
        if term.strip()
    ]

    if not terms:
        return "Error: Search query contains no valid terms."

    results = []

    for file_path in PROJECT_ROOT.rglob("*"):

        if not file_path.is_file():
            continue

        if any(
            part in IGNORED_DIRS
            for part in file_path.parts
        ):
            continue

        if (
            file_path.suffix.lower()
            not in ALLOWED_EXTENSIONS
        ):
            continue

        if file_path.name == ".env":
            continue

        try:
            content = file_path.read_text(
                encoding="utf-8",
                errors="ignore"
            )

        except Exception:
            continue

        for line_number, line in enumerate(
            content.splitlines(),
            start=1
        ):

            line_lower = line.lower()

            matched_terms = [
                term
                for term in terms
                if term in line_lower
            ]

            if not matched_terms:
                continue

            relative_path = (
                file_path.relative_to(
                    PROJECT_ROOT
                )
            )

            results.append(
                {
                    "file": str(relative_path),
                    "line": line_number,
                    "content": line.strip(),
                    "matched_terms": matched_terms,
                }
            )

            if len(results) >= 50:
                break

        if len(results) >= 50:
            break

    if not results:
        return f"No matches found for: {query}"

    output = []

    output.append(
        f"Search results for: {query}"
    )

    output.append(
        f"Search terms: {', '.join(terms)}"
    )

    output.append(
        f"Matches found: {len(results)}"
    )

    output.append("")

    for result in results:
        output.append(
            f"{result['file']}:"
            f"{result['line']}: "
            f"{result['content']}"
        )

    return "\n".join(output)


def write_file(
    file_path: str,
    content: str
) -> str:

    target, error = _safe_project_path(file_path)

    if error:
        return error

    if target is None:
        return "Error: Invalid file path."

    if target.name == ".env":
        return "Error: Modifying .env is not allowed."

    if ".git" in target.parts:
        return "Error: Modifying .git files is not allowed."

    try:

        target.parent.mkdir(
            parents=True,
            exist_ok=True
        )

        target.write_text(
            content,
            encoding="utf-8"
        )

        return (
            f"Successfully wrote file: {file_path}"
        )

    except PermissionError:
        return (
            f"Error: Permission denied: {file_path}"
        )

    except Exception as e:
        return (
            f"Error writing file: {e}"
        )


def list_project_files() -> list[str]:

    project_files = []

    for file_path in PROJECT_ROOT.rglob("*"):

        if not file_path.is_file():
            continue

        if any(
            part in IGNORED_DIRS
            for part in file_path.parts
        ):
            continue

        if file_path.name == ".env":
            continue

        try:

            relative_path = (
                file_path.relative_to(
                    PROJECT_ROOT
                )
            )

            project_files.append(
                str(relative_path)
            )

        except ValueError:
            continue

    return sorted(project_files)


def run_function_test(
    file_path: str,
    function_name: str,
    expected_value: str
) -> str:
    """
    Execute a function from a project Python file
    and compare its return value with the expected value.
    """

    try:
        target, error = _safe_project_path(file_path)

        if error:
            return error

        if target is None:
            return "BEHAVIOR TEST FAILED: Invalid file path."

        if target.suffix != ".py":
            return (
                "BEHAVIOR TEST FAILED: "
                "Target file must be a Python file."
            )

        if not target.exists():
            return (
                f"BEHAVIOR TEST FAILED: "
                f"File not found: {file_path}"
            )

        import ast
        import subprocess
        import sys

        source = target.read_text(
            encoding="utf-8"
        )

        tree = ast.parse(source)

        function_exists = any(
            isinstance(
                node,
                (ast.FunctionDef, ast.AsyncFunctionDef)
            )
            and node.name == function_name
            for node in ast.walk(tree)
        )

        if not function_exists:
            return (
                f"BEHAVIOR TEST FAILED: "
                f"Function '{function_name}' "
                f"was not found in {file_path}."
            )

        test_code = f"""
import importlib.util

spec = importlib.util.spec_from_file_location(
    "target_module",
    r"{target}"
)

module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)

result = module.{function_name}()

expected = {expected_value!r}

if result == expected:
    print("BEHAVIOR TEST PASSED")
    print(f"Function: {function_name}")
    print(f"Expected: {{expected!r}}")
    print(f"Actual: {{result!r}}")
else:
    print("BEHAVIOR TEST FAILED")
    print(f"Function: {function_name}")
    print(f"Expected: {{expected!r}}")
    print(f"Actual: {{result!r}}")
"""

        result = subprocess.run(
            [
                sys.executable,
                "-c",
                test_code
            ],
            cwd=PROJECT_ROOT,
            capture_output=True,
            text=True,
            timeout=30,
        )

        output = result.stdout.strip()

        if result.stderr:
            output += (
                f"\n{result.stderr.strip()}"
            )

        return (
            output
            or "BEHAVIOR TEST FAILED: "
               "No test output produced."
        )

    except subprocess.TimeoutExpired:
        return (
            "BEHAVIOR TEST FAILED: "
            "Function execution timed out."
        )

    except Exception as e:
        return f"BEHAVIOR TEST ERROR: {e}"