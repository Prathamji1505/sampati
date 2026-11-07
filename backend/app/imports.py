import base64
import csv
from datetime import datetime, timezone
import hashlib
import hmac
import io
import json
from pathlib import PureWindowsPath
import time

from pydantic import ValidationError
from sqlalchemy import select
from sqlalchemy.orm import Session

from .models import Aircraft, ImportBatch
from .schemas import CsvRow, HEADERS, MAX_BYTES, MAX_ROWS, parse_timestamp


def safe_filename(filename: str) -> str:
    return PureWindowsPath(filename.replace('/', '\\')).name[:200] or 'aircraft.csv'


def parse_csv(content: bytes, filename: str) -> tuple[list[CsvRow], list[dict]]:
    if not filename.lower().endswith('.csv'):
        return [], [{'row': 0, 'field': 'file', 'message': 'The CSV parser requires a .csv file.'}]
    if len(content) > MAX_BYTES:
        return [], [{'row': 0, 'field': 'file', 'message': 'The file is larger than 1 MiB. Upload a smaller CSV.'}]
    try:
        text = content.decode('utf-8-sig')
    except UnicodeDecodeError:
        return [], [{'row': 0, 'field': 'file', 'message': 'Save the file as UTF-8 CSV and try again.'}]
    if '\x00' in text:
        return [], [{'row': 0, 'field': 'file', 'message': 'This file contains unsupported binary characters.'}]
    rows, errors, seen = [], [], set()
    record_count = 0
    try:
        reader = csv.reader(io.StringIO(text, newline=''), strict=True)
        headers = next(reader, [])
        if len(headers) != len(set(headers)) or set(headers) != set(HEADERS):
            return [], [{'row': 1, 'field': 'headers', 'message': 'Use these six unique headers: ' + ', '.join(HEADERS)}]
        for record_number, values in enumerate(reader, start=2):
            if not values or not any(value.strip() for value in values):
                continue
            record_count += 1
            if record_count > MAX_ROWS:
                return [], [{'row': record_number, 'field': 'file', 'message': f'Use no more than {MAX_ROWS:,} records per file.'}]
            if len(values) != len(headers):
                errors.append({'row': record_number, 'field': 'columns', 'message': f'Expected {len(headers)} values; found {len(values)}. Check commas and quoted text.'})
                continue
            try:
                row = CsvRow.model_validate(dict(zip(headers, values)))
                row._csv_row = record_number
                if row.aircraft_id in seen:
                    errors.append({'row': record_number, 'field': 'aircraft_id', 'message': f'{row.aircraft_id} occurs more than once. Keep one report per aircraft.'})
                seen.add(row.aircraft_id)
                rows.append(row)
            except ValidationError as error:
                for detail in error.errors():
                    field = str(detail['loc'][0])
                    message = str(detail['msg']).removeprefix('Value error, ')
                    if field == 'reported_status':
                        message = 'Use available, unavailable or unknown.'
                    errors.append({'row': record_number, 'field': field, 'message': message})
            if len(errors) >= 100:
                errors.append({'row': 0, 'field': 'file', 'message': 'Showing the first 100 errors. Fix these and upload again.'})
                break
    except (csv.Error, OverflowError):
        errors.append({'row': 0, 'field': 'file', 'message': 'The CSV could not be read. Check quote marks and field lengths.'})
    if not rows and not errors:
        errors.append({'row': 0, 'field': 'file', 'message': 'Add at least one aircraft below the header row.'})
    return rows, errors


def fingerprint(rows: list[CsvRow]) -> str:
    data = sorted((row.normalized() for row in rows), key=lambda row: row['aircraft_id'])
    return hashlib.sha256(json.dumps(data, sort_keys=True, ensure_ascii=False, separators=(',', ':')).encode()).hexdigest()


def snapshot(aircraft: Aircraft) -> dict:
    return {
        'aircraft_id': aircraft.aircraft_id,
        'display_name': aircraft.display_name,
        'reported_status': aircraft.reported_status,
        'source_updated_at': aircraft.source_updated_at.astimezone(timezone.utc).isoformat(),
        'source_name': aircraft.source_name,
        'note': aircraft.note,
    }


def existing_import(session: Session, digest: str, workspace_id: str):
    return session.scalar(select(ImportBatch).where(ImportBatch.workspace_id == workspace_id, ImportBatch.fingerprint == digest))


def compare_rows(session: Session, rows: list[CsvRow], workspace_id: str) -> tuple[list[dict], list[dict]]:
    current = {item.aircraft_id: item for item in session.scalars(select(Aircraft).where(Aircraft.workspace_id == workspace_id))}
    changes, errors = [], []
    for number, row in enumerate(rows, start=2):
        number = row._csv_row or number
        before = snapshot(current[row.aircraft_id]) if row.aircraft_id in current else None
        after = row.normalized()
        action = 'new' if before is None else 'unchanged' if before == after else 'updated'
        if before is not None:
            old_time, new_time = parse_timestamp(before['source_updated_at']), parse_timestamp(after['source_updated_at'])
            if new_time < old_time:
                action = 'blocked'
                errors.append({'row': number, 'field': 'source_updated_at', 'message': f'{row.aircraft_id}: this report is older than the accepted record. Supply a newer report.'})
            elif new_time == old_time and before != after:
                action = 'blocked'
                errors.append({'row': number, 'field': 'source_updated_at', 'message': f'{row.aircraft_id}: different values have the same timestamp. Resolve the conflict at the source.'})
        changes.append({'row': number, 'aircraft_id': row.aircraft_id, 'action': action, 'before': before, 'after': after})
    return changes, errors


def sign_preview(payload: dict, secret: str) -> str:
    encoded = base64.urlsafe_b64encode(json.dumps(payload, separators=(',', ':')).encode()).decode().rstrip('=')
    signature = hmac.new(secret.encode(), encoded.encode(), hashlib.sha256).hexdigest()
    return encoded + '.' + signature


def read_preview(token: str, secret: str, workspace_id: str, actor_id: str | None) -> dict:
    try:
        encoded, signature = token.rsplit('.', 1)
        expected = hmac.new(secret.encode(), encoded.encode(), hashlib.sha256).hexdigest()
        if not hmac.compare_digest(signature, expected):
            raise ValueError('Invalid signature')
        payload = json.loads(base64.urlsafe_b64decode(encoded + '=' * (-len(encoded) % 4)))
        if payload['expires'] < time.time() or payload['workspace'] != workspace_id or payload.get('actor_id') != actor_id:
            raise ValueError('Expired, wrong workspace or wrong account')
        return payload
    except (ValueError, KeyError, TypeError, json.JSONDecodeError) as error:
        raise ValueError('This preview is invalid or expired. Upload the file again.') from error
