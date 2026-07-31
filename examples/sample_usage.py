from pathlib import Path

from organizer.config_loader import load_config
from organizer.sorter import organize
from organizer.utils import generate_summary

config = load_config("config.json")

results = organize("~/Downloads", config, dry_run=True)
print(generate_summary(results))

results = organize("~/Downloads", config, dry_run=False)
print(generate_summary(results))
