import ast
import os
import json


def check_docstrings(directory):
    missing_docs = {}
    for root, dirs, files in os.walk(directory):
        if (
            "venv" in root
            or ".git" in root
            or "__pycache__" in root
            or "alembic" in root
        ):
            continue
        for file in files:
            if file.endswith(".py"):
                filepath = os.path.join(root, file)
                try:
                    with open(filepath, "r", encoding="utf-8") as f:
                        source = f.read()

                    tree = ast.parse(source)
                    missing = []

                    if not ast.get_docstring(tree):
                        missing.append({"type": "module", "name": file, "lineno": 1})

                    for node in ast.walk(tree):
                        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                            if node.name.startswith("__") and node.name != "__init__":
                                continue
                            if not ast.get_docstring(node):
                                missing.append(
                                    {
                                        "type": "function",
                                        "name": node.name,
                                        "lineno": node.lineno,
                                    }
                                )
                        elif isinstance(node, ast.ClassDef):
                            if not ast.get_docstring(node):
                                missing.append(
                                    {
                                        "type": "class",
                                        "name": node.name,
                                        "lineno": node.lineno,
                                    }
                                )

                    if missing:
                        missing_docs[filepath] = missing
                except Exception as e:
                    print(f"Error parsing {filepath}: {e}")

    with open("missing_docs.json", "w") as f:
        json.dump(missing_docs, f, indent=4)
    print(f"Found missing docs in {len(missing_docs)} files.")


if __name__ == "__main__":
    check_docstrings("app")
