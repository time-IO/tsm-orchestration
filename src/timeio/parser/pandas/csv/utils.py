import pandas as pd
import re
from io import StringIO

def filter_lines(rawdata: str, comment_regex: str) -> str:
    lines = []
    for line in rawdata.splitlines():
        if not re.match(comment_regex, line):
            lines.append(line)
    return "\n".join(lines)


def get_header(rawdata: str, header_line: int) -> str:
    for i, line in enumerate(rawdata.splitlines()):
        if i == header_line:
            return line
    raise ValueError(f"header line {header_line} not found")


def pandafy_headerline(header_raw: str, delimiter: str) -> list[str]:
    mock_cvs = StringIO(header_raw + "\n\n")
    df = pd.read_csv(mock_cvs, delimiter=delimiter)
    return df.columns.to_list()