import warnings

import logging
from typing import Any

from models.parser_detailed import ParserDetailedUpdate
from parser import PandasParser
from timeio.errors import ParsingWarning
from models.parser import ParsedDataResponse
from models.parser_csv import ParserCsvCreate, ParserCsvUpdate

from timeio.parser import CsvParser

logger = logging.getLogger("app.services.trigger_ext_api")

def parse_csv_data(settings: ParserCsvUpdate, raw_data: str) -> ParsedDataResponse:
    return parse_data_with_parser(get_csv_parser_by_settings(settings), raw_data)

def get_csv_parser_by_settings(
        settings: ParserCsvUpdate
) -> CsvParser:
    translated_settings = {
        "decimal": ".",
        "delimiter": settings.delimiter,
        "skipfooter": settings.footlines_to_exclude,
        "timestamp_columns": [
            {"column": x.column, "format": x.timestamp_format}
            for x in settings.timestamp_columns
        ],
        "headlines_to_exclude": settings.headlines_to_exclude,
        "footlines_to_exclude": settings.footlines_to_exclude,
        "timezone": settings.timezone,
        "comment": settings.comment,
        "header": settings.header,
    }
    logger.debug("Translated settings for CSV parser", translated_settings)
    return CsvParser(translated_settings)

def parse_data_with_parser(parser: PandasParser, raw_data: str):
    with warnings.catch_warnings(record=True) as caught_warnings:
        warnings.simplefilter("always", ParsingWarning)

        try:
            df = parser.do_parse(raw_data.strip(), "project", "thing")
        except Exception as e:
            logger.error("Error: %s", e, exc_info=True)
            return ParsedDataResponse(
                data=[],
                error=str(e),
                is_valid=False,
                warnings=[str(w.message) for w in caught_warnings],
            )

        print(df)

    return ParsedDataResponse(
        data=df.to_dict(orient="records"),
        error="",
        is_valid=True,
        warnings=[str(w.message) for w in caught_warnings],
    )
