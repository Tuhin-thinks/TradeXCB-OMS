import importlib
import re

# keep adding new broker names here
BROKER_MODULES = {
    "angel": None,
    "five_paisa": None,
    "motilal_oswal": None,
    "zerodha": None
}


def to_camel_case(string):
    """
    Function to convert a string to CamelCase so that it can be used to import a broker class from a module
    Args:
        string(str): the name of the module

    Returns:
        camelcase string, with '_' (underscores) removed
    """
    return re.sub("_", '', string.title())


# iterate on each defined broker modules and save their class reference
for broker_module_name, _ in BROKER_MODULES.items():
    importlib.import_module(f"brokers.{broker_module_name}")
    BROKER_MODULES[broker_module_name] = eval(f"{broker_module_name}.{to_camel_case(broker_module_name)}")
