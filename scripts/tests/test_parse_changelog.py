from scripts.bin.parse_changelog import *


class ValidChangelogTestCase:
    def __init__(self, changelog: str):
        self.changelog = changelog

    def run(self):
        errors = Parser(self.changelog).get_line_errors()
        assert len(errors) == 0


class InvalidChangelogTestCase:
    def __init__(self, changelog: str, expected: LineError):
        self.changelog = changelog
        self.expected = expected

    def error_equals(self, actual: LineError):
        assert issubclass(actual.__class__, LineError)
        assert actual.error_text == self.expected.error_text
        assert actual.error_description == self.expected.error_description
        assert actual.line.line_number == self.expected.line.line_number

    def run(self):
        errors = Parser(self.changelog).get_line_errors()
        assert len(errors) > 0
        error = errors[0]
        self.error_equals(error)


def get_changelog_text_with_header(text):
    return (
        """<!-- ... -->
<!-- BEGIN OF CHANGELOG -->
"""
        + text
    )


# ============================
# Test cases
# ============================


def test_missing_header():
    InvalidChangelogTestCase(
        """No header
""",
        LineError(
            Line(1, "No header", None),
            "Missing end of header.",
            "Header was never ended.",
        ),
    ).run()


def test_missing_unreleased_version():
    InvalidChangelogTestCase(
        get_changelog_text_with_header(
            """
## [2026-01-01]

### Added
- ...
"""
        ),
        LineError(
            Line(4, "## [2026-01-01]", None),
            "Invalid line.",
            "Expected a valid UnreleasedVersionLine, found VersionLine.",
        ),
    ).run()


def test_forbidden_section_key():

    InvalidChangelogTestCase(
        get_changelog_text_with_header(
            """
## [Unreleased]

### ForbiddenKey
- ...
"""
        ),
        LineError(
            Line(6, "ForbiddenKey:", None),
            "Invalid line.",
            "Expected a valid VersionLine or SectionLine, found InvalidLine.",
        ),
    ).run()


def test_missing_section_key():

    InvalidChangelogTestCase(
        get_changelog_text_with_header(
            """
## [Unreleased]

- Missing section key before Release Note.
"""
        ),
        LineError(
            Line(6, "ForbiddenKey:", None),
            "Invalid line.",
            "Expected a valid VersionLine or SectionLine, found ReleaseNoteLine.",
        ),
    ).run()


def test_invalid_release_note_line():
    InvalidChangelogTestCase(
        get_changelog_text_with_header(
            """
## [Unreleased]

### Added
Release note without dash.
"""
        ),
        LineError(
            Line(7, "Release note without dash.", None),
            "Invalid line.",
            "Expected a valid ReleaseNoteLine, found InvalidLine.",
        ),
    ).run()


def test_invalid_version_line():
    InvalidChangelogTestCase(
        get_changelog_text_with_header(
            """
## [Unreleased]

### Added
- Release note with Merge Request ([Merge Request](www.example.com)).

## [01-01-2026]
"""
        ),
        LineError(
            Line(9, "Release note without dash.", None),
            "Invalid line.",
            "Expected a valid VersionLine or SectionLine or ReleaseNoteLine, found InvalidLine.",
        ),
    ).run()


def test_release_note_without_merge_request():
    InvalidChangelogTestCase(
        get_changelog_text_with_header(
            """
## [Unreleased]

### Added
- Release note without Merge Request.
"""
        ),
        LineError(
            Line(7, "- Release note without Merge Request.", None),
            "Missing Merge Request.",
            "Every Release Note of unreleased version requires a valid Merge Request link.",
        ),
    ).run()


def test_release_note_with_invalid_link_title():
    InvalidChangelogTestCase(
        get_changelog_text_with_header(
            """
## [Unreleased]

### Added
- Release note with invalid link tile ([Invalid](www.example.com)).
"""
        ),
        LineError(
            Line(
                7,
                "- Release note with invalid link tile ([Invalid](www.example.com)).",
                None,
            ),
            "Invalid link title.",
            "Allowed titles are: Merge Request, Wiki.",
        ),
    ).run()


def test_version_with_duplicate_section():
    InvalidChangelogTestCase(
        get_changelog_text_with_header(
            """
## [Unreleased]

### Added
- Release note with Merge Request ([Merge Request](www.example.com)).

### Added
"""
        ),
        LineError(
            Line(9, "### Added", None),
            "Duplicate section 'Added'.",
            "Please merge sections.",
        ),
    ).run()


def test_section_without_release_notes():
    InvalidChangelogTestCase(
        get_changelog_text_with_header(
            """
## [Unreleased]

### Added

### Fixed
"""
        ),
        LineError(
            Line(8, "### Added", None),
            "Invalid line.",
            "Expected a valid ReleaseNoteLine, found SectionLine.",
        ),
    ).run()


def test_changelog_with_multiple_unreleased_versions():
    InvalidChangelogTestCase(
        get_changelog_text_with_header(
            """
## [Unreleased]

### Added
- Release note with Merge Request ([Merge Request](www.example.com)).

## [Unreleased]
"""
        ),
        LineError(
            Line(9, "### Added", None),
            "Invalid line.",
            "Expected a valid VersionLine or SectionLine or ReleaseNoteLine, found UnreleasedVersionLine.",
        ),
    ).run()


def test_valid_changelog():
    ValidChangelogTestCase(
        get_changelog_text_with_header(
            """
## [Unreleased]
### Added
- Release note with Merge Request ([Merge Request](www.example.com)).
- Another release note with Merge Request ([Merge Request](www.example.com)) and Wiki ([Wiki](www.example.com)).
- Another release note with two Merge Requests ([Merge Request](www.example.com)) and ([Merge Request](www.example.com)).
- Another release note with two Merge Requests within same parenthesis ([Merge Request](www.example.com), [Merge Request](www.example.com)).

### Fixed
- Release note with Merge Request ([Merge Request](www.example.com)).

### Changed
- Release note with Merge Request ([Merge Request](www.example.com)).

### Removed
- Release note with Merge Request ([Merge Request](www.example.com)).

## [2026-01-01]
### Added
- Release note without Merge Request.

## [2025-01-01]
### Added
- Release note without Merge Request.
"""
        )
    ).run()


def test_valid_changelog_with_newly_created_empty_unreleased_version():
    ValidChangelogTestCase(
        get_changelog_text_with_header(
            """
## [Unreleased]

## [2026-01-01]
### Added
- Release note with Merge Request ([Merge Request](www.example.com)).
- Another release note with Merge Request ([Merge Request](www.example.com)) and Wiki ([Wiki](www.example.com)).
"""
        )
    ).run()
