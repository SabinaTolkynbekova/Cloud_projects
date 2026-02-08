1. parse_csv returns list[dict]
2. Uses csv.DictReader
3. Returns empty list on FileNotFoundError
4. Handles malformed CSV
5. No eval / exec / os.system / subprocess
6. No hardcoded secrets
