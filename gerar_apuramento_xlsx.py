import csv
import zipfile
from datetime import datetime
from pathlib import Path
from xml.sax.saxutils import escape

CSV_PATH = Path(r"d:\Data mining\PJTDataMining\pns2019.csv")
OUTPUT_PATH = Path(r"d:\Data mining\PJTDataMining\apuramento_idades_25_59.xlsx")

ATTRS = [
    "V0026",
    "C006",
    "C008",
    "C009",
    "D009",
    "E001",
    "VDF002",
    "I00102",
    "Q060",
    "Q061",
    "Q062",
    "Q06306",
    "J001",
    "J01101",
    "P006",
    "P01101",
    "P02001",
    "P023",
    "P027",
    "P02801",
    "P034",
    "P035",
    "P037",
    "P050",
    "P00104",
    "P00404",
    "W00101",
    "W00201",
]

PRIMARY_CANDIDATES = ["Q060", "Q00201"]
COMPLETION_CANDIDATES = [
    "Q0001", "Q0002", "Q0003", "Q0004", "Q0005", "Q0006", "Q0007",
    "Q009", "Q010", "Q011", "Q012", "Q060", "Q00201"
]


def parse_bool(val):
    if val is None:
        return False
    v = str(val).strip().lower()
    if v in {"", "na", "n/a", "nan", "none"}:
        return False
    if v in {"1", "1.0", "true", "yes", "sim", "verdadeiro"}:
        return True
    if v in {"0", "0.0", "false", "no", "nao", "falso"}:
        return False
    try:
        return float(v) == 1
    except ValueError:
        return False


def get_primary_value(row):
    for col in PRIMARY_CANDIDATES:
        if col in row and row[col] not in (None, ""):
            return row[col]
    return None


def row_passes(row):
    try:
        idade = float(str(row.get("C008", "")).strip().replace(",", "."))
    except Exception:
        return False
    if not 25 <= idade <= 59:
        return False

    sexo = str(row.get("C006", "")).strip()
    if sexo not in {"1", "2"}:
        return False

    primary = get_primary_value(row)
    if primary is None or not parse_bool(primary):
        return False

    completion_found = False
    for col in COMPLETION_CANDIDATES:
        if col in row and row[col] not in (None, ""):
            completion_found = True
            if not parse_bool(row[col]):
                return False

    # Se a base tiver a flag de questionário concluído, ela deve ser verdadeira.
    # Se não houver nenhuma flag detectada, seguimos com a regra principal.
    return True


def read_filtered_rows():
    with CSV_PATH.open("r", encoding="latin1", newline="") as f:
        reader = csv.DictReader(f)
        if not reader.fieldnames:
            raise ValueError(f"Arquivo CSV sem cabeçalho: {CSV_PATH}")

        rows = []
        for row in reader:
            if row_passes(row):
                item = {}
                for col in ATTRS:
                    if col in row:
                        val = row[col]
                        if val is None:
                            item[col] = ""
                        else:
                            item[col] = str(val).strip()
                    else:
                        item[col] = ""
                rows.append(item)

    return rows


def excel_cell_xml(value, cell_ref):
    text = "" if value is None else str(value)
    return f'<c r="{cell_ref}" t="inlineStr"><is><t>{escape(text)}</t></is></c>'


def build_sheet_xml(headers, rows):
    xml_rows = []
    for r_idx, row in enumerate([headers] + rows, start=1):
        cells = []
        for c_idx, value in enumerate(row, start=1):
            cell_ref = f"{chr(64 + c_idx)}{r_idx}"
            cells.append(excel_cell_xml(value, cell_ref))
        xml_rows.append(f'<row r="{r_idx}">' + ''.join(cells) + '</row>')
    return ''.join(xml_rows)


def write_xlsx(headers, rows):
    sheet_xml = build_sheet_xml(headers, rows)
    workbook_xml = '''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<workbook xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main"
          xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships">
  <sheets>
    <sheet name="apuramento" sheetId="1" r:id="rId1"/>
  </sheets>
</workbook>'''

    rels_xml = '''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
  <Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet" Target="worksheets/sheet1.xml"/>
  <Relationship Id="rId2" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/styles" Target="styles.xml"/>
</Relationships>'''

    content_types_xml = '''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">
  <Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>
  <Default Extension="xml" ContentType="application/xml"/>
  <Override PartName="/xl/workbook.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet.main+xml"/>
  <Override PartName="/xl/worksheets/sheet1.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.worksheet+xml"/>
  <Override PartName="/xl/styles.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.styles+xml"/>
</Types>'''

    styles_xml = '''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<styleSheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">
  <fonts count="1"><font><sz val="11"/><name val="Calibri"/></font></fonts>
  <fills count="1"><fill><patternFill patternType="none"/></fill></fills>
  <borders count="1"><border><left/><right/><top/><bottom/><diagonal/></border></borders>
  <cellStyleXfs count="1"><xf numFmtId="0" fontId="0" fillId="0" borderId="0"/></cellStyleXfs>
  <cellXfs count="1"><xf numFmtId="0" fontId="0" fillId="0" borderId="0" xfId="0"/></cellXfs>
  <cellStyles count="1"><cellStyle name="Normal" xfId="0" builtinId="0"/></cellStyles>
</styleSheet>'''

    root_rels_xml = '''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
  <Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="xl/workbook.xml"/>
</Relationships>'''

    with zipfile.ZipFile(OUTPUT_PATH, "w", compression=zipfile.ZIP_DEFLATED) as z:
        z.writestr("[Content_Types].xml", content_types_xml)
        z.writestr("_rels/.rels", root_rels_xml)
        z.writestr("xl/workbook.xml", workbook_xml)
        z.writestr("xl/_rels/workbook.xml.rels", rels_xml)
        z.writestr("xl/worksheets/sheet1.xml", f'''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">
  <sheetData>{sheet_xml}</sheetData>
</worksheet>''')
        z.writestr("xl/styles.xml", styles_xml)


if __name__ == "__main__":
    if not CSV_PATH.exists():
        raise FileNotFoundError(f"CSV não encontrado: {CSV_PATH}")

    rows = read_filtered_rows()
    headers = ATTRS

    # Se a tabela estiver vazia, ainda gera o arquivo com cabeçalho vazio.
    output_rows = [
        {col: row.get(col, "") for col in headers}
        for row in rows
    ]

    export_rows = []
    for row in output_rows:
        export_rows.append([row.get(col, "") for col in headers])

    write_xlsx(headers, export_rows)
    print(f"Arquivo gerado: {OUTPUT_PATH}")
    print(f"Registros exportados: {len(export_rows)}")
