# spikee/list.py

import os
from pathlib import Path
import importlib
import pkgutil

#
# 1) Seeds: local only
#
def list_seeds(args):
    """
    Lists local seed folders in ./datasets.
    A seed folder is identified if it contains 'base_documents.jsonl'.
    Only shows local seeds, ignoring built-in ones.
    """
    base_path = Path(os.getcwd(), "datasets")
    if not base_path.is_dir():
        print("\n[seeds] No 'datasets/' folder found in the current directory.")
        return

    seed_dirs = []
    for child in base_path.iterdir():
        if child.is_dir():
            # Check if 'base_documents.jsonl' exists in that directory
            if (child / "base_documents.jsonl").is_file():
                seed_dirs.append(child.name)

    if seed_dirs:
        print("\n[seeds] Found the following local seed folders under './datasets/':")
        for d in seed_dirs:
            print(f" - {d}")
    else:
        print("\n[seeds] No seed folders found locally (no 'base_documents.jsonl' detected).")


#
# 2) Datasets: local only
#
def list_datasets(args):
    """
    Lists .jsonl dataset files directly under ./datasets,
    ignoring any subfolders (where seeds typically live).
    Only shows local datasets, ignoring built-in ones.
    """
    datasets_dir = Path(os.getcwd(), "datasets")
    if not datasets_dir.is_dir():
        print("\n[datasets] No 'datasets/' folder found in the current directory.")
        return

    # Only look for *.jsonl files in the top-level of ./datasets
    jsonl_files = list(datasets_dir.glob("*.jsonl"))

    if jsonl_files:
        print("\n[datasets] Found the following JSONL files in './datasets/':")
        for f in jsonl_files:
            print(f" - {f.name}")
    else:
        print("\n[datasets] No JSONL files found at top-level of './datasets/'.")


def list_judges(args):
    """
    Lists all local .py files under ./judges (top-level only),
    then also shows built-in judges from spikee.judges
    (excluding __init__.py).
    """
    # 3a) Local
    targets_dir = Path(os.getcwd(), "judges")
    if targets_dir.is_dir():
        py_files = _py_files_in_dir(targets_dir)
        if py_files:
            print("\n[judges] Local targets in './judges/':")
            for t in py_files:
                print(f" - {t}")
        else:
            print("\n[judges] No local target files found in './judges/'.")
    else:
        print("\n[judges] No local 'judges/' folder found.")

    # 3b) Built-in
    print("\n[judges] Built-in judges in spikee.judges:")
    _print_builtin_modules("spikee.judges")

#
# 3) Targets: local + built-in
#
def list_targets(args):
    """
    Lists all local .py files under ./targets (top-level only),
    then also shows built-in targets from spikee.targets
    (excluding __init__.py).
    """
    # 3a) Local
    targets_dir = Path(os.getcwd(), "targets")
    if targets_dir.is_dir():
        py_files = _py_files_in_dir(targets_dir)
        if py_files:
            print("\n[targets] Local targets in './targets/':")
            for t in py_files:
                print(f" - {t}")
        else:
            print("\n[targets] No local target files found in './targets/'.")
    else:
        print("\n[targets] No local 'targets/' folder found.")

    # 3b) Built-in
    print("\n[targets] Built-in targets in spikee.targets:")
    _print_builtin_modules("spikee.targets")


#
# 4) Plugins: local + built-in
#
def list_plugins(args):
    """
    Lists all local .py files under ./plugins (top-level only),
    then also shows built-in plugins from spikee.plugins
    (excluding __init__.py).
    """
    # 4a) Local
    plugins_dir = Path(os.getcwd(), "plugins")
    if plugins_dir.is_dir():
        py_files = _py_files_in_dir(plugins_dir)
        if py_files:
            print("\n[plugins] Local plugins in './plugins/':")
            for p in py_files:
                print(f" - {p}")
        else:
            print("\n[plugins] No local plugin files found in './plugins/'.")
    else:
        print("\n[plugins] No local 'plugins/' folder found.")

    # 4b) Built-in
    print("\n[plugins] Built-in plugins in spikee.plugins:")
    _print_builtin_modules("spikee.plugins")

def list_attacks(args):
    """
    Lists all local .py files under ./attacks (top-level only),
    then also shows built-in attacks from spikee.attacks
    (excluding __init__.py).
    """
    # 4a) Local
    plugins_dir = Path(os.getcwd(), "attacks")
    if plugins_dir.is_dir():
        py_files = _py_files_in_dir(plugins_dir)
        if py_files:
            print("\n[attacks] Local attack scripts in './attacks/':")
            for p in py_files:
                print(f" - {p}")
        else:
            print("\n[attacks] No local plugin files found in './attacks/'.")
    else:
        print("\n[attacks] No local 'attacks/' folder found.")

    # 4b) Built-in
    print("\n[attacks] Built-in attacks in spikee.attacks:")
    _print_builtin_modules("spikee.attacks")

#
# Internal Helper Functions
#
def _py_files_in_dir(dir_path: Path):
    """
    Return a list of Python modules (excluding __init__.py) in the given dir.
    """
    py_files = []
    for f in dir_path.glob("*.py"):
        if f.name != "__init__.py":
            py_files.append(f.name[:-3])  # strip .py
    return py_files


def _print_builtin_modules(package_name: str):
    """
    Lists all modules in a given package (e.g. spikee.targets or spikee.plugins).
    Skips __init__.py. Only top-level modules are shown.
    """
    import importlib
    import pkgutil
    try:
        pkg = importlib.import_module(package_name)
        for _, mod_name, is_pkg in pkgutil.iter_modules(pkg.__path__):
            if not is_pkg and mod_name != "__init__":
                print(f" - {mod_name}")
    except ModuleNotFoundError:
        print(f"   Built-in package '{package_name}' not found.")
    except Exception as e:
        print(f"   Error listing built-in modules in '{package_name}': {e}")
