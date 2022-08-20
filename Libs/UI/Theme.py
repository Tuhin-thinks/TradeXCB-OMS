from typing import Dict
import os

BASE = os.path.realpath(os.path.dirname(__file__))

theme_dir = os.path.join(BASE, "Raw")


def get_available_themes() -> Dict[str, str]:
    """
    function to create a dictionary of available theme from theme directory
    Returns
        Dict[theme_name:theme_path]
    """
    themes = {}
    for theme_files in os.listdir(theme_dir):
        if theme_files.endswith(".xml"):
            theme_name = os.path.splitext(os.path.basename(theme_files))[0]
            themes[theme_name] = os.path.realpath(os.path.join(theme_dir, theme_files))
    return themes
