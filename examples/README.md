# Examples

| Example | What it shows |
|---|---|
| `config.custom.json` | Meaning-based categories (Finance, Career, Education, ...) with overlapping extensions |
| `sample_usage.py` | Using FileSage as a Python library (organize with dry-run) |

## Try the custom config

The `smart` command suggests meaning-based folders from file content. The
`sorter` uses `config.json` for extension rules. To organize by meaning-based
categories instead, point the CLI at a custom config by swapping it in:

```bash
cp examples/config.custom.json config.json
file-organizer smart ~/Downloads --dry-run
```

## Programmatic usage

```bash
python examples/sample_usage.py
```
