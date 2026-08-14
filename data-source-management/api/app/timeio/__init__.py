from pathlib import Path

__path__.append(str(Path(__file__).resolve().parents[4] / "src" / "timeio"))

# This file refers to src/timeio directory for local development
# Docker compose setup instead mounts src/timeio directory to this directory instead
# During build process, src/timeio directory is copied here

# Example usage of timeio modules in API:
# from timeio.parser import get_parser
