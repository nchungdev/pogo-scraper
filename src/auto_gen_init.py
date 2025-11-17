import ast
import os
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent
SRC_ROOT = PROJECT_ROOT / "src"

print("PROJECT_ROOT =", PROJECT_ROOT)
print("SRC_ROOT =", SRC_ROOT)

if not SRC_ROOT.exists():
    raise RuntimeError(f"❌ Folder 'src/' not found at: {SRC_ROOT}")


def snake_to_camel(name: str) -> str:
    return "".join(w.capitalize() for w in name.split("_"))


def extract_classes(file_path: Path):
    """Return list of class names from a python file."""
    try:
        tree = ast.parse(file_path.read_text(encoding="utf-8"))
        return [
            node.name
            for node in tree.body
            if isinstance(node, ast.ClassDef)
        ]
    except Exception:
        return []


def generate_init(folder: Path):
    """Generate __init__.py for a given folder."""
    py_files = [
        f for f in folder.iterdir()
        if f.suffix == ".py" and not f.name.startswith("_")
    ]

    imports = []
    exports = []

    for f in py_files:
        module_name = f.stem
        camel_name = snake_to_camel(module_name)
        classes = extract_classes(f)

        if camel_name in classes:
            imports.append(f"from .{module_name} import {camel_name}")
            exports.append(f"    '{camel_name}',")
        else:
            imports.append(f"from . import {module_name}")
            exports.append(f"    '{module_name}',")

    content = (
            "# AUTO-GENERATED — DO NOT EDIT\n\n"
            + "\n".join(imports).rstrip()
            + "\n\n__all__ = [\n"
            + "\n".join(exports)
            + "\n]\n"
    )

    init_file = folder / "__init__.py"
    init_file.write_text(content, encoding="utf-8")
    print(f"✓ Generated {init_file}")


def walk_and_generate(root: Path):
    """Walk recursively and create/overwrite __init__.py files."""
    for dirpath, dirnames, filenames in os.walk(root):
        path = Path(dirpath)

        # ignore __pycache__
        if "__pycache__" in path.parts:
            continue

        # ensure package root has __init__.py
        init_file = path / "__init__.py"
        if not init_file.exists():
            init_file.write_text("# AUTO-CREATED\n", encoding="utf-8")
            print(f"✓ Created {init_file}")

        generate_init(path)


if __name__ == "__main__":
    print("🔧 Generating init files recursively...\n")
    walk_and_generate(SRC_ROOT)
    print("\n🎉 Done!")
