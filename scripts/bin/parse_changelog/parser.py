import re

from .lines import (
    EmptyLine,
    InvalidLine,
    HeaderFinishedLine,
    HeaderLine,
    ReleaseNoteLine,
    SectionLine,
    UnreleasedVersionLine,
    VersionLine,
)
from .errors import HeaderEndNotFoundLineError

VERSION_LINE_PATTERN = (
    r"## \[(?:(\d{4}-\d{2}-\d{2})|Unreleased)\]"
)
SECTION_LINE_PATTERN = r"^### (Added|Fixed|Changed|Removed)$"
RELEASE_NOTE_LINE_PATTERN = r"^-\s.*"
LINEBREAK_NOTE_LINE_PATTERN = r"^\s\s.*"
HEADER_FINISHED_LINE_PATTERN = "<!-- BEGIN OF CHANGELOG -->"
VER_PATTERN = r"^(\d{4})-(\d{2})-(\d{2})$"

class ReleaseNoteVersion:
    def __init__(self, year, month, day, is_unreleased=False):
        self.year = year
        self.month = month
        self.day = day
        self.is_unreleased = is_unreleased
        self.allowed_sections = ["Added", "Fixed", "Changed", "Removed"]

    @classmethod
    def from_version_string(cls, version_string, is_unreleased=False):
        if version_string is None:
            return cls(None, None, None, is_unreleased=True)

        match = re.fullmatch(VER_PATTERN, version_string)
        if match is None:
            raise ValueError(f"invalid version string: {version_string!r}")

        return cls(
            int(match.group(1)),
            int(match.group(2)),
            int(match.group(3)),
            is_unreleased,
        )

    @property
    def version_string(self):
        return f"{self.year}-{self.month}-{self.day}"

    def check_section(self, section):
        if section not in self.allowed_sections:
            return False
        self.allowed_sections.remove(section)
        return True


class Parser:
    def __init__(self, file_content):
        self.current_line = None
        self.header_finished = False
        self.line_errors = []
        self.file_content = file_content

    def get_line_errors(self):
        for index, line_text in enumerate(self.file_content.splitlines()):
            next_line = self.parse_next_line(index, line_text)
            if not isinstance(next_line, EmptyLine):
                self.current_line = next_line
                self.line_errors.extend(self.current_line.get_errors())
        if not self.header_finished:
            self.line_errors.append(HeaderEndNotFoundLineError(self.current_line))
        return self.line_errors

    def parse_next_line(self, index, line_text):
        stripped_line_text = line_text.rstrip()
        line_number = index + 1

        if not stripped_line_text:
            return EmptyLine(line_number, stripped_line_text, self.current_line)

        if re.match(HEADER_FINISHED_LINE_PATTERN, stripped_line_text):
            self.header_finished = True
            return HeaderFinishedLine(
                line_number, stripped_line_text, self.current_line
            )

        if not self.header_finished:
            return HeaderLine(line_number, stripped_line_text, self.current_line)

        version_match = re.match(VERSION_LINE_PATTERN, stripped_line_text)
        if version_match:
            current_version = ReleaseNoteVersion.from_version_string(
                version_match.group(1),
                version_match.group(1) is None,
            )
            if not current_version.is_unreleased:
                return VersionLine(
                    line_number,
                    stripped_line_text,
                    self.current_line,
                    current_version=current_version,
                )

            return UnreleasedVersionLine(
                line_number,
                stripped_line_text,
                self.current_line,
                current_version=current_version,
            )

        if re.match(SECTION_LINE_PATTERN, stripped_line_text):
            current_section = re.match(SECTION_LINE_PATTERN, stripped_line_text).group(
                1
            )
            return SectionLine(
                line_number,
                stripped_line_text,
                self.current_line,
                current_section=current_section,
            )

        if re.match(RELEASE_NOTE_LINE_PATTERN, stripped_line_text):
            return ReleaseNoteLine(line_number, stripped_line_text, self.current_line)

        if re.match(LINEBREAK_NOTE_LINE_PATTERN, stripped_line_text):
            return ReleaseNoteLine(line_number, stripped_line_text, self.current_line)

        return InvalidLine(line_number, stripped_line_text, self.current_line)
