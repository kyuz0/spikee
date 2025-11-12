import importlib
import inspect
import os

from ..templates.target import Target
from ..templates.judge import Judge


# ==== Loading Modules ====
def load_module_from_path(name, module_type):
    """Loads a module either from a local path or from the spikee package."""
    local_path = os.path.join(os.getcwd(), module_type, f"{name}.py")
    if os.path.isfile(local_path):
        spec = importlib.util.spec_from_file_location(name, local_path)
        if spec and spec.loader:
            mod = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(mod)

            match module_type:
                case "targets":
                    for _, obj in inspect.getmembers(mod):
                        if inspect.isclass(obj) and issubclass(obj, Target) and obj is not Target:
                            return obj()
                case "judges":
                    for _, obj in inspect.getmembers(mod):
                        if inspect.isclass(obj) and issubclass(obj, Judge) and obj is not Judge:
                            return obj()

            return mod
        else:
            raise ImportError(f"Could not load module {name} from {local_path}")
    else:
        try:
            return importlib.import_module(f"spikee.{module_type}.{name}")
        except ModuleNotFoundError:
            raise ValueError(f"Module '{name}' not found locally or in spikee.{module_type}")


def get_default_option(module):
    if module and hasattr(module, "get_available_option_values"):
        available = module.get_available_option_values()
        if available:
            return available[0]

        else:
            return None
