import warnings

import logging

from timeio.errors import ParsingWarning
from models.parser import ParserValidationResponse
from models.parser_csv import ParserCsvCreate, ParserCsvUpdate

from timeio.parser import CsvParser

logger = logging.getLogger("app.services.trigger_ext_api")


def validate_csv_parser(
    settings: ParserCsvUpdate, raw_data: str
) -> ParserValidationResponse:
    logger.debug("Validating parser")

    csv_settings = {
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

    parser = CsvParser(csv_settings)
    with warnings.catch_warnings(record=True) as caught_warnings:
        warnings.simplefilter("always", ParsingWarning)

        try:
            df = parser.do_parse(raw_data.strip(), "project", "thing")
        except Exception as e:
            logger.error("Error: %s", e, exc_info=True)
            return ParserValidationResponse(
                data=[],
                error=str(e),
                is_valid=False,
                warnings=[str(w.message) for w in caught_warnings],
            )

        print(df)

    return ParserValidationResponse(
        data=df.to_dict(orient="records"),
        error="",
        is_valid=True,
        warnings=[str(w.message) for w in caught_warnings],
    )
