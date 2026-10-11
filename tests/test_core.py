import unittest
from io import BytesIO
from unittest.mock import Mock
from pypdf import PdfWriter
from core import Chunk, answer, chunk_pages, read_pdf, retrieve

class CoreTests(unittest.TestCase):
    def test_page_provenance_and_overlap(self):
        chunks = chunk_pages(["abcdefghij", "두 번째 페이지"], size=6, overlap=2)
        self.assertEqual(chunks[0], Chunk(1, "abcdef"))
        self.assertEqual(chunks[1], Chunk(1, "efghij"))
        self.assertEqual(chunks[2].page, 2)

    def test_english_and_korean_retrieval(self):
        chunks = [Chunk(1, "Docker packages applications in containers."), Chunk(2, "장학금 신청 마감일은 10월 30일입니다.")]
        self.assertEqual(retrieve(chunks, "Docker containers")[0][0].page, 1)
        self.assertEqual(retrieve(chunks, "장학금 신청 마감일")[0][0].page, 2)
        self.assertEqual(retrieve(chunks, "zzzzzz"), [])

    def test_blank_pdf_rejected(self):
        writer = PdfWriter()
        writer.add_blank_page(width=100, height=100)
        data = BytesIO()
        writer.write(data)
        with self.assertRaisesRegex(ValueError, "No readable text"):
            read_pdf(data.getvalue())

    def test_generation_preserves_sources_and_disables_storage(self):
        client = Mock()
        client.responses.create.return_value.output_text = "October 30 [p. 2]"
        result = answer(client, "example-model", "Deadline?", [(Chunk(2, "October 30"), 0.8)], "English")
        self.assertIn("[p. 2]", result)
        kwargs = client.responses.create.call_args.kwargs
        self.assertFalse(kwargs["store"])
        self.assertIn("[p. 2] October 30", kwargs["input"])

if __name__ == "__main__":
    unittest.main()
