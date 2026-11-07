"""Bounded spreadsheet parsing and explicit text-cell exports."""
import csv
from datetime import datetime
import io
import zipfile

from openpyxl import Workbook, load_workbook
from openpyxl.cell import WriteOnlyCell
from openpyxl.utils.exceptions import InvalidFileException
from defusedxml.common import DefusedXmlException
from xml.etree.ElementTree import ParseError

from .imports import parse_csv
from .schemas import HEADERS, MAX_BYTES, MAX_ROWS


def parse_dataset(content: bytes, filename: str):
    if filename.lower().endswith('.csv'):
        return parse_csv(content, filename)
    def problem(message):
        return [], [{'row': 0, 'field': 'file', 'message': message}]
    if not filename.lower().endswith('.xlsx'):
        return problem('Choose a CSV or .xlsx file. Macro-enabled and older Excel files are not supported.')
    if len(content) > MAX_BYTES:
        return problem('The file is larger than 1 MiB. Upload a smaller file.')
    try:
        with zipfile.ZipFile(io.BytesIO(content)) as archive:
            entries = archive.infolist()
            if len(entries) > 200 or sum(entry.file_size for entry in entries) > 12 * MAX_BYTES:
                return problem('This workbook expands beyond the supported size. Export a smaller sheet as CSV.')
            if any('vbaproject' in entry.filename.lower() or 'externallinks/' in entry.filename.lower() for entry in entries):
                return problem('Remove macros and external workbook links before importing.')
        workbook = load_workbook(io.BytesIO(content), read_only=True, data_only=False, keep_links=False)
        try:
            visible = [sheet for sheet in workbook.worksheets if sheet.sheet_state == 'visible']
            if len(visible) != 1:
                return problem('Use exactly one visible worksheet containing the six template columns.')
            sheet = visible[0]
            # Read the actual cells, not untrusted dimension declarations.
            sheet.reset_dimensions()
            output = io.StringIO(newline='')
            writer = csv.writer(output)
            aircraft_id_column = None
            for number, cells in enumerate(sheet.iter_rows(), start=1):
                if number > MAX_ROWS + 1:
                    return problem(f'Use no more than {MAX_ROWS:,} records.')
                if all(cell.value is None for cell in cells):
                    writer.writerow([''] * len(HEADERS))
                    continue
                if number == 1:
                    headers = [cell.value for cell in cells[:len(HEADERS)]]
                    aircraft_id_column = headers.index('aircraft_id') if 'aircraft_id' in headers else None
                if any(cell.data_type == 'f' for cell in cells):
                    return problem(f'Row {number} contains a formula. Paste its values as text before importing.')
                if any(cell.value is not None for cell in cells[len(HEADERS):]):
                    return problem('The worksheet contains extra columns. Use the six-column template.')
                values = []
                for index, cell in enumerate(cells[:len(HEADERS)]):
                    value = cell.value
                    if isinstance(value, datetime):
                        return problem(f'Row {number}: store timestamps as ISO text with a timezone, for example 2026-11-07T10:00:00Z.')
                    if number > 1 and index == aircraft_id_column and isinstance(value, (int, float)):
                        return problem(f'Row {number}: format aircraft IDs as text to preserve leading zeroes.')
                    values.append('' if value is None else str(value))
                writer.writerow(values + [''] * (len(HEADERS) - len(values)))
            return parse_csv(output.getvalue().encode(), 'converted.csv')
        finally:
            workbook.close()
    except (zipfile.BadZipFile, OSError, ValueError, KeyError, TypeError, OverflowError, InvalidFileException, DefusedXmlException, ParseError):
        return problem('This workbook could not be read. Save a new .xlsx or UTF-8 CSV file and try again.')


def spreadsheet_bytes(rows: list[dict]) -> bytes:
    workbook = Workbook(write_only=True)
    sheet = workbook.create_sheet('Aircraft')
    for values in [HEADERS, *[[row.get(key, '') for key in HEADERS] for row in rows]]:
        cells = []
        for value in values:
            cell = WriteOnlyCell(sheet, value=str(value))
            cell.data_type = 's'  # Values beginning '=' remain literal strings.
            cells.append(cell)
        sheet.append(cells)
    output = io.BytesIO()
    workbook.save(output)
    return output.getvalue()


def csv_bytes(rows: list[dict]) -> bytes:
    output = io.StringIO(newline='')
    writer = csv.writer(output, quoting=csv.QUOTE_ALL)
    writer.writerow(HEADERS)
    for row in rows:
        values = []
        for key in HEADERS:
            value = str(row.get(key, ''))
            if value.lstrip().startswith(('=', '+', '-', '@', '\t', '\r', '\n', '＝', '＋', '－', '＠')):
                value = "'" + value
            values.append(value)
        writer.writerow(values)
    return output.getvalue().encode('utf-8-sig')
