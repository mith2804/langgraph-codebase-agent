import subprocess
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parent.parent


def run_tests() -> str:
    """
    Run the project's pytest test suite safely.

    If no pytest tests are discovered, report that clearly
    instead of incorrectly marking the project as failed.
    """

    try:
        result = subprocess.run(
            ["python", "-m", "pytest"],
            cwd=PROJECT_ROOT,
            capture_output=True,
            text=True,
            timeout=120,
        )

        output = result.stdout

        if result.stderr:
            output += "\n" + result.stderr

        # -------------------------------------------------
        # No tests discovered
        # -------------------------------------------------

        if "collected 0 items" in output:
            return (
                "NO TESTS FOUND\n\n"
                "Pytest executed successfully, but no test cases "
                "were discovered in the project.\n\n"
                f"{output}"
            )

        # -------------------------------------------------
        # Tests passed
        # -------------------------------------------------

        if result.returncode == 0:
            return f"TESTS PASSED\n\n{output}"

        # -------------------------------------------------
        # Tests failed
        # -------------------------------------------------

        return f"TESTS FAILED\n\n{output}"

    except subprocess.TimeoutExpired:
        return (
            "TESTS FAILED\n\n"
            "Test execution timed out after 120 seconds."
        )

    except Exception as e:
        return f"TEST EXECUTION ERROR: {e}"