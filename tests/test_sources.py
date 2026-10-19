import json
import unittest
from io import BytesIO
from unittest.mock import Mock, patch
from pypdf import PdfReader, PdfWriter
from pypdf.generic import DecodedStreamObject, NameObject, DictionaryObject
from streamlit.testing.v1 import AppTest
from core import Chunk, CitationError, answer, read_pdf, source_pdf, export_report, validate_citations


def sample_pdf():
    writer = PdfWriter()
    for text in ['Cover page', 'Applications close on October 30.']:
        page = writer.add_blank_page(width=400, height=400)
        font = DictionaryObject({NameObject('/Type'): NameObject('/Font'), NameObject('/Subtype'): NameObject('/Type1'), NameObject('/BaseFont'): NameObject('/Helvetica')})
        page[NameObject('/Resources')] = DictionaryObject({NameObject('/Font'): DictionaryObject({NameObject('/F1'): font})})
        stream = DecodedStreamObject()
        stream.set_data(f'BT /F1 12 Tf 20 350 Td ({text}) Tj ET'.encode())
        page[NameObject('/Contents')] = writer._add_object(stream)
    data = BytesIO()
    writer.write(data)
    return data.getvalue()


class SourceTests(unittest.TestCase):
    def setUp(self):
        self.hits = [(Chunk(2, 'Applications close on October 30.'), 0.8)]

    def test_missing_and_unknown_citations_rejected(self):
        for text in ['', 'October 30', 'October 30 [p. 99]', 'October 30 [p. 2] [p. 3]']:
            with self.subTest(text=text), self.assertRaises(CitationError):
                validate_citations(text, self.hits)
        self.assertEqual(validate_citations('October 30 [p. 2]', self.hits), 'October 30 [p. 2]')

    def test_no_evidence_never_calls_provider(self):
        client = Mock()
        with self.assertRaises(CitationError):
            answer(client, 'model', 'Question', [], 'English')
        client.responses.create.assert_not_called()

    def test_real_pdf_extraction_and_export_preserve_content(self):
        data = sample_pdf()
        self.assertEqual(read_pdf(data)[1].page, 2)
        exported = PdfReader(BytesIO(source_pdf(data, [2, 2])))
        self.assertEqual(len(exported.pages), 1)
        self.assertIn('October 30', exported.pages[0].extract_text())
        self.assertNotIn('Cover page', exported.pages[0].extract_text())
        for pages in [[], [0], [3], [-1]]:
            with self.assertRaises(ValueError):
                source_pdf(data, pages)

    def test_report_roundtrip(self):
        result = json.loads(export_report('문서.pdf', '마감일?', None, self.hits))
        self.assertEqual(result['sources'][0]['page'], 2)
        self.assertIsNone(result['answer'])
        self.assertEqual(result['document'], '문서.pdf')

    def test_search_survives_rerun_and_removal_clears_result(self):
        uploaded = Mock()
        uploaded.name = 'handbook.pdf'
        uploaded.getvalue.return_value = sample_pdf()
        with patch('streamlit.file_uploader', return_value=uploaded):
            app = AppTest.from_file('../app.py').run()
            next(w for w in app.text_input if w.label == 'Ask a question').set_value('Applications close')
            app.button[0].click().run()
            self.assertFalse(app.exception)
            self.assertTrue(app.session_state['result']['hits'])
            self.assertEqual(len(app.get('download_button')), 2)
            app.run()
            self.assertFalse(app.exception)
            self.assertEqual(len(app.get('download_button')), 2)
        with patch('streamlit.file_uploader', return_value=None):
            app.run()
            self.assertNotIn('result', app.session_state)
            self.assertNotIn('document', app.session_state)

    def test_invalid_ai_citation_withheld_in_ui(self):
        uploaded = Mock()
        uploaded.name = 'handbook.pdf'
        uploaded.getvalue.return_value = sample_pdf()
        with patch('streamlit.file_uploader', return_value=uploaded), patch('core.answer', side_effect=CitationError('invalid')), patch('openai.OpenAI'):
            app = AppTest.from_file('../app.py').run()
            app.sidebar.text_input[0].set_value('test-key')
            app.sidebar.checkbox[0].check().run()
            next(w for w in app.text_input if w.label == 'Ask a question').set_value('Applications close')
            app.button[0].click().run()
            self.assertFalse(app.exception)
            self.assertEqual(app.session_state['result']['error'], 'citation')
            self.assertIsNone(app.session_state['result']['answer'])
            self.assertEqual(len(app.get('download_button')), 2)
