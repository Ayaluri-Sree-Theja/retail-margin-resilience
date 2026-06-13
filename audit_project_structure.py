from pathlib import Path

IGNORE_DIRS = {
    ".venv",
    ".git",
    "__pycache__",
    ".pytest_cache",
    ".ipynb_checkpoints",
    "target",
    "dbt_packages",
    "logs",
}

SKIP_FILE_EXTENSIONS_IN_DATA = {".csv", ".parquet", ".xlsx"}

root = Path(".").resolve()
lines = [str(root)]

def should_skip(path: Path) -> bool:
    if path.name in IGNORE_DIRS:
        return True

    if path.is_file():
        if any(part in {"raw", "processed"} for part in path.parts):
            if path.suffix.lower() in SKIP_FILE_EXTENSIONS_IN_DATA:
                return True

    return False

def walk(path: Path, prefix: str = "") -> None:
    items = [p for p in sorted(path.iterdir(), key=lambda x: (x.is_file(), x.name.lower())) if not should_skip(p)]

    for index, item in enumerate(items):
        connector = "└── " if index == len(items) - 1 else "├── "
        lines.append(prefix + connector + item.name)

        if item.is_dir():
            extension = "    " if index == len(items) - 1 else "│   "
            walk(item, prefix + extension)

walk(root)

output_path = root / "project_structure_audit.txt"
output_path.write_text("\n".join(lines), encoding="utf-8")

print(f"Saved project structure to: {output_path}")