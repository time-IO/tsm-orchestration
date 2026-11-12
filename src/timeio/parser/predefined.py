"""Current predefined parser support and UI recommendations."""

# The file worker currently supports TrueLog100; MQTT implementations use a
# different processing interface. Extend this when more combinations are supported.
FILE_INGEST_PREDEFINED_PARSERS = ("truelog100",)

PREDEFINED_PARSER_RECOMMENDATIONS = {
    "mqtt": ("campbell_cr6", "ydoc_ml417", "chirpstack_generic", "quaesta"),
    "file": FILE_INGEST_PREDEFINED_PARSERS,
}
