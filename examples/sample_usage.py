from pathlib import Path

from organizer.config_loader import load_config
from organizer.sorter import organize
from organizer.utils import generate_summary

config = load_config("config.json")

downloads = Path.home() / "Downloads"

results = organize(downloads, config, dry_run=True)
print(generate_summary(results))
