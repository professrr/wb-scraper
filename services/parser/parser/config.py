"""Parser service configuration with type-safe environment variables."""

from pydantic_settings import BaseSettings, SettingsConfigDict


class ParserSettings(BaseSettings):
    """Parser service settings.

    Reads from environment variables with PARSER_ prefix.
    Example: PARSER_CONSUMER_GROUP=parser-group
    """

    model_config = SettingsConfigDict(env_prefix="PARSER_")

    consumer_group: str = "parser-group"
    poll_timeout: float = 1.0
