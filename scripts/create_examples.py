"""Create small, fictional CSV fixtures. Run with the project's Python interpreter."""
import csv
from datetime import timedelta
from pathlib import Path

from backend.app.main import sample_rows
from backend.app.schemas import HEADERS, parse_timestamp

ROOT = Path(__file__).resolve().parents[1]
EXAMPLES = ROOT / 'examples'


def write(name, records, headers=HEADERS):
    with (EXAMPLES / name).open('w', encoding='utf-8', newline='') as output:
        writer = csv.DictWriter(output, fieldnames=headers, extrasaction='ignore')
        writer.writeheader()
        writer.writerows(records)


def main():
    EXAMPLES.mkdir(exist_ok=True)
    records = sample_rows()
    write('fictional-fleet.csv', records)
    write('duplicate-id.csv', [records[0], records[0]])
    write('missing-field.csv', [{**records[0], 'source_name': ''}])
    write('invalid-status.csv', [{**records[0], 'reported_status': 'ready'}])
    write('invalid-timestamp.csv', [{**records[0], 'source_updated_at': '2026-11-07 10:00'}])
    write('older-report.csv', [{**records[0], 'source_updated_at': (parse_timestamp(records[0]['source_updated_at']) - timedelta(days=1)).isoformat(), 'reported_status': 'unavailable'}])
    write('newer-update.csv', [{**records[0], 'source_updated_at': (parse_timestamp(records[0]['source_updated_at']) + timedelta(minutes=1)).isoformat(), 'reported_status': 'unavailable', 'note': 'Fictional later source update.'}])
    print('Seven fictional CSV files written to examples/. Import fictional-fleet.csv before testing old/new updates.')


if __name__ == '__main__':
    main()
