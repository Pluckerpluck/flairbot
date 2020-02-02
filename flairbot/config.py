import yaml

CONFIG_FILE = "flairs.yml"

with open(CONFIG_FILE) as f:
    _config = yaml.load(f)

def get_overrides(flair_name):
    "Return the overrides for the given flair."
    overrides = _config.get("overrides", {})
    return overrides.get(flair_name, {})

def get_combo_flairs():
    """Return all the combo flairs"""
    return _config.get("combos", {})
