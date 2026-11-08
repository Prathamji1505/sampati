"""Strict relief intake contract. Invalid text remains reviewable as evidence."""
import csv
from datetime import timedelta
import hashlib
import io
import json
from decimal import Decimal

from fastapi import HTTPException
from pydantic import BaseModel, ConfigDict, Field, ValidationError, field_validator

from .models import utcnow
from .relief import RequestFields, normalized
from .schemas import parse_timestamp

CONTRACT = 'sampati.relief-intake.v1'
MAX_FILE = 256 * 1024
MAX_ROWS = 200
HEADERS = ['schema_version', 'report_reference', 'observed_at', 'reference', *RequestFields.model_fields]


class IntakeRow(RequestFields):
    reference: str = Field(min_length=1, max_length=64, pattern=r'^[A-Za-z0-9][A-Za-z0-9._/-]*$')


class Envelope(BaseModel):
    model_config = ConfigDict(extra='forbid')
    schema_version: str
    report_reference: str = Field(min_length=1, max_length=64, pattern=r'^[A-Za-z0-9][A-Za-z0-9._/-]*$')
    observed_at: str = Field(min_length=1, max_length=64)
    requests: list = Field(min_length=1, max_length=MAX_ROWS)

    @field_validator('schema_version')
    @classmethod
    def contract(cls, value):
        if value != CONTRACT:
            raise ValueError(f'Use schema_version {CONTRACT}.')
        return value

    @field_validator('observed_at')
    @classmethod
    def dated(cls, value):
        observed = parse_timestamp(value)
        if observed > utcnow() + timedelta(minutes=5):
            raise ValueError('The observation time is more than five minutes in the future.')
        return value


def stable_hash(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(',', ':')).encode()).hexdigest()


def unique_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f'Duplicate JSON key: {key}.')
        result[key] = value
    return result


def errors_for(exc, row=None):
    return [{'row': row, 'field': '.'.join(str(part) for part in error['loc']), 'message': error['msg']}
        for error in exc.errors(include_url=False, include_input=False)]


def parse_file(content, filename):
    extension = filename.rsplit('.', 1)[-1].lower()
    if len(content) > MAX_FILE:
        raise HTTPException(413, 'Use a CSV or JSON file no larger than 256 KiB.')
    if extension not in {'csv', 'json'}:
        raise HTTPException(422, 'Use a UTF-8 CSV or JSON relief file. Download the format guide for the required fields.')
    try:
        text = content.decode('utf-8-sig')
        if '\x00' in text:
            raise UnicodeError()
    except UnicodeError:
        raise HTTPException(422, 'The file must contain UTF-8 text, not a binary workbook.')
    result = {'raw_text': text, 'rows': [], 'errors': [], 'report_reference': None,
        'observed_at': None, 'observed_at_raw': None}
    result['fingerprint'] = stable_hash({'format': extension, 'text': text})
    try:
        row_numbers = None
        if extension == 'json':
            payload = json.loads(text, parse_float=Decimal, parse_constant=lambda value: (_ for _ in ()).throw(ValueError(f'{value} is not a valid number.')),
                object_pairs_hook=unique_object)
        else:
            reader = csv.reader(io.StringIO(text, newline=''), strict=True)
            headers = next(reader, [])
            if len(headers) != len(set(headers)) or set(headers) - set(HEADERS) or set(HEADERS) - {'note'} - set(headers):
                raise ValueError('CSV headers must match the format guide, without repeated or unknown columns. Only note is optional.')
            records = []
            row_numbers = []
            metadata = None
            for values in reader:
                if not values:
                    continue
                if len(values) != len(headers):
                    raise ValueError(f'CSV row {reader.line_num} has a different number of columns from the header.')
                record = dict(zip(headers, values))
                current = {key: record.pop(key) for key in ('schema_version', 'report_reference', 'observed_at')}
                if metadata is not None and current != metadata:
                    raise ValueError('Every CSV row must use the same schema version, report reference and observation time.')
                metadata = current
                records.append(record)
                row_numbers.append(reader.line_num)
                if len(records) > MAX_ROWS:
                    raise ValueError('Use at most 200 requests per file.')
            payload = {**(metadata or {}), 'requests': records}
        envelope = Envelope.model_validate(payload)
        result.update(report_reference=envelope.report_reference, observed_at_raw=envelope.observed_at,
            observed_at=parse_timestamp(envelope.observed_at))
        seen = set()
        for ordinal, values in enumerate(envelope.requests):
            index = row_numbers[ordinal] if row_numbers is not None else ordinal + 1
            try:
                row = IntakeRow.model_validate(values)
                reference = row.reference.upper()
                if reference in seen:
                    result['errors'].append({'row': index, 'field': 'reference', 'message': 'This reference is repeated within the file.'})
                seen.add(reference)
                result['rows'].append({'row': index, 'reference': reference, **normalized(row), 'needed_by_raw': row.needed_by})
            except ValidationError as exc:
                result['errors'].extend(errors_for(exc, index))
        if not result['errors']:
            # Equivalent CSV/JSON and decimal/time representations share one identity.
            result['fingerprint'] = stable_hash({'contract': CONTRACT, 'report_reference': envelope.report_reference,
                'observed_at': result['observed_at'].isoformat(), 'requests': sorted([
                    {key: value for key, value in row.items() if key not in {'row', 'needed_by_raw'}}
                    for row in result['rows']], key=lambda row: row['reference'])})
    except ValidationError as exc:
        result['errors'].extend(errors_for(exc))
    except (ValueError, csv.Error, RecursionError) as exc:
        result['errors'].append({'row': None, 'field': 'file', 'message': str(exc)[:300] or 'The file could not be read.'})
    return result


def example_payload(reference=None, now=None):
    now = now or utcnow()
    from uuid import uuid4
    suffix = uuid4().hex[:10].upper()
    return {'schema_version': CONTRACT, 'report_reference': 'EXAMPLE-' + suffix, 'observed_at': now.isoformat(),
        'requests': [{'reference': reference or 'EXAMPLE-REQ-' + suffix, 'requesting_organisation': 'Fictional community relief desk',
            'locality': 'Fictional Riverside Ward', 'category': 'shelter', 'item_name': 'Family shelter kits', 'quantity': '12.125',
            'unit': 'kits', 'needed_by': (now + timedelta(days=2)).isoformat(), 'source_name': 'Fictional relief desk report',
            'note': 'Fictional example for learning the intake workflow.'}]}
