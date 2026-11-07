from datetime import datetime, timezone
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, PrivateAttr, field_validator

HEADERS = ['aircraft_id', 'display_name', 'reported_status', 'source_updated_at', 'source_name', 'note']
MAX_ROWS = 2000
MAX_BYTES = 1024 * 1024


def parse_timestamp(value: str) -> datetime:
    try:
        parsed = datetime.fromisoformat(value.replace('Z', '+00:00'))
    except ValueError as error:
        raise ValueError('Use an ISO timestamp, for example 2026-11-07T10:00:00Z.') from error
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        raise ValueError('Include a timezone: Z or an offset such as +05:30.')
    return parsed.astimezone(timezone.utc)


class CsvRow(BaseModel):
    _csv_row: int = PrivateAttr(default=0)
    model_config = ConfigDict(extra='forbid', strict=True)
    aircraft_id: str = Field(min_length=1, max_length=64, pattern=r'^[A-Za-z0-9][A-Za-z0-9._-]*$')
    display_name: str = Field(max_length=120)
    reported_status: Literal['available', 'unavailable', 'unknown']
    source_updated_at: str = Field(min_length=1, max_length=64)
    source_name: str = Field(min_length=1, max_length=120)
    note: str = Field(max_length=1000)

    @field_validator('*', mode='before')
    @classmethod
    def trim_text(cls, value):
        return value.strip() if isinstance(value, str) else value

    @field_validator('reported_status', mode='before')
    @classmethod
    def normalize_status(cls, value):
        return value.lower() if isinstance(value, str) else value

    @field_validator('source_updated_at')
    @classmethod
    def valid_timestamp(cls, value: str) -> str:
        parse_timestamp(value)
        return value

    def normalized(self) -> dict:
        return {**self.model_dump(), 'source_updated_at': parse_timestamp(self.source_updated_at).isoformat()}


class ConfirmRequest(BaseModel):
    model_config = ConfigDict(extra='forbid')
    token: str = Field(min_length=1, max_length=2000)
    rows: list[CsvRow] = Field(min_length=1, max_length=MAX_ROWS)
