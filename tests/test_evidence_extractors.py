
import io
import json

import pytest

from mananze_os.evidence_content import (
    EvidenceContentIngestion,
    EvidenceExtractionRequest,
)
from mananze_os.evidence_extractors import (
    DOCX_CONTENT_TYPE,
    XLSX_CONTENT_TYPE,
    PDF_CONTENT_TYPE,
    DOCXEvidenceExtractor,
    PDFEvidenceExtractor,
    XLSXEvidenceExtractor,
)
from mananze_os.evidence_reference import EvidenceReference


TENANT_ID = "tenant-001"
EVIDENCE_ID = "evidence-001"


def _evidence(content_type: str) -> EvidenceReference:
    return EvidenceReference(
        evidence_id=EVIDENCE_ID,
        tenant_id=TENANT_ID,
        source_type="uploaded_document",
        source_reference="test-document",
        quality="high",
        description="Test evidence",
    )


def _request(content_type: str, raw: bytes) -> EvidenceExtractionRequest:
    evidence = _evidence(content_type)
    return EvidenceExtractionRequest(
        tenant_id=TENANT_ID,
        evidence=evidence,
        raw_content=raw,
        content_type=content_type,
    )


def _docx_bytes() -> bytes:
    from docx import Document

    document = Document()
    document.add_paragraph("Mananze Security")
    document.add_paragraph("Guarding services and patrols.")

    table = document.add_table(rows=2, cols=2)
    table.cell(0, 0).text = "Service"
    table.cell(0, 1).text = "Rate"
    table.cell(1, 0).text = "Guarding"
    table.cell(1, 1).text = "R12000"

    output = io.BytesIO()
    document.save(output)
    return output.getvalue()


def _xlsx_bytes() -> bytes:
    from openpyxl import Workbook

    workbook = Workbook()
    sheet = workbook.active
    sheet.title = "Rates"
    sheet.append(["Service", "Monthly Rate"])
    sheet.append(["Guarding", 12000])
    sheet.append(["Patrol", 8000])

    output = io.BytesIO()
    workbook.save(output)
    return output.getvalue()


def _pdf_bytes() -> bytes:
    # Minimal valid PDF containing a text object.
    objects = [
        b"<< /Type /Catalog /Pages 2 0 R >>",
        b"<< /Type /Pages /Kids [3 0 R] /Count 1 >>",
        b"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 300 300] "
        b"/Resources << /Font << /F1 4 0 R >> >> /Contents 5 0 R >>",
        b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>",
        b"<< /Length 47 >>\nstream\nBT /F1 18 Tf 50 200 Td (Mananze Test) Tj ET\nendstream",
    ]

    result = bytearray(b"%PDF-1.4\n")
    offsets = [0]

    for number, obj in enumerate(objects, start=1):
        offsets.append(len(result))
        result.extend(f"{number} 0 obj\n".encode())
        result.extend(obj)
        result.extend(b"\nendobj\n")

    xref_offset = len(result)
    result.extend(f"xref\n0 {len(objects) + 1}\n".encode())
    result.extend(b"0000000000 65535 f \n")

    for offset in offsets[1:]:
        result.extend(f"{offset:010d} 00000 n \n".encode())

    result.extend(
        f"trailer\n<< /Size {len(objects) + 1} /Root 1 0 R >>\n"
        f"startxref\n{xref_offset}\n%%EOF\n".encode()
    )

    return bytes(result)


def test_pdf_extractor_preserves_page_structure():
    result = PDFEvidenceExtractor().extract(
        _request(PDF_CONTENT_TYPE, _pdf_bytes())
    )

    payload = json.loads(result.content)

    assert payload["format"] == "pdf"
    assert payload["page_count"] == 1
    assert payload["pages"][0]["page"] == 1
    assert "Mananze Test" in payload["pages"][0]["text"]
    assert result.evidence_id == EVIDENCE_ID
    assert result.tenant_id == TENANT_ID
    assert result.extractor_id == "mananze.pdf.pypdf"


def test_docx_extractor_reads_paragraphs_and_tables():
    result = DOCXEvidenceExtractor().extract(
        _request(DOCX_CONTENT_TYPE, _docx_bytes())
    )

    payload = json.loads(result.content)

    assert payload["format"] == "docx"
    assert "Mananze Security" in payload["paragraphs"]
    assert payload["tables"][0][0] == ["Service", "Rate"]
    assert payload["tables"][0][1] == ["Guarding", "R12000"]
    assert result.extractor_id == "mananze.docx.python-docx"


def test_xlsx_extractor_reads_sheets_and_cells():
    result = XLSXEvidenceExtractor().extract(
        _request(XLSX_CONTENT_TYPE, _xlsx_bytes())
    )

    payload = json.loads(result.content)

    assert payload["format"] == "xlsx"
    assert payload["sheet_count"] == 1
    assert payload["sheets"][0]["name"] == "Rates"
    assert payload["sheets"][0]["rows"][0] == ["Service", "Monthly Rate"]
    assert payload["sheets"][0]["rows"][1] == ["Guarding", 12000]
    assert result.extractor_id == "mananze.xlsx.openpyxl"


def test_ingestion_can_use_pdf_extractor():
    ingestion = EvidenceContentIngestion(
        extractor=PDFEvidenceExtractor()
    )

    result = ingestion.ingest(
        _request(PDF_CONTENT_TYPE, _pdf_bytes())
    )

    assert result.content_type == PDF_CONTENT_TYPE
    assert result.extractor_id == "mananze.pdf.pypdf"


def test_ingestion_rejects_unsupported_extractor():
    ingestion = EvidenceContentIngestion(
        extractor=PDFEvidenceExtractor()
    )

    with pytest.raises(ValueError):
        ingestion.ingest(
            _request(DOCX_CONTENT_TYPE, _docx_bytes())
        )


def test_extractors_preserve_evidence_provenance():
    for extractor, content_type, raw in [
        (PDFEvidenceExtractor(), PDF_CONTENT_TYPE, _pdf_bytes()),
        (DOCXEvidenceExtractor(), DOCX_CONTENT_TYPE, _docx_bytes()),
        (XLSXEvidenceExtractor(), XLSX_CONTENT_TYPE, _xlsx_bytes()),
    ]:
        result = extractor.extract(_request(content_type, raw))

        assert result.evidence_id == EVIDENCE_ID
        assert result.tenant_id == TENANT_ID
        assert len(result.content_hash) == 64


def test_extractors_reject_wrong_content_type():
    with pytest.raises(ValueError):
        PDFEvidenceExtractor().extract(
            _request(DOCX_CONTENT_TYPE, _docx_bytes())
        )

    with pytest.raises(ValueError):
        DOCXEvidenceExtractor().extract(
            _request(XLSX_CONTENT_TYPE, _xlsx_bytes())
        )

    with pytest.raises(ValueError):
        XLSXEvidenceExtractor().extract(
            _request(PDF_CONTENT_TYPE, _pdf_bytes())
        )
