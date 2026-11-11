from sqlmodel import Session
from .parser_predefined import ParserPredefinedRepository


class ParserMqttRepository(ParserPredefinedRepository):
    """Keep the legacy MQTT selection limited to its current implementations."""

    def __init__(self, session: Session):
        super().__init__(session, recommended_for="mqtt")
