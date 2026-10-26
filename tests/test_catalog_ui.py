import unittest
from unittest.mock import patch
from streamlit.testing.v1 import AppTest

SOURCE = """
import streamlit as st
from catalog_ui import render_catalog
if "doc" not in st.session_state:
    st.session_state["doc"] = {}
render_catalog(lambda en, ko: en, st.session_state["doc"], "sample.pdf")
"""

class CatalogUITests(unittest.TestCase):
    @patch("catalog.configured", return_value=True)
    @patch("catalog.list_titles", return_value=[])
    @patch("catalog.save_title")
    def test_save_requires_consent(self, save, listing, configured):
        app = AppTest.from_string(SOURCE).run()
        self.assertFalse(app.exception)
        app.button[0].click().run()
        save.assert_not_called()
        app.checkbox[0].check()
        app.button[0].click().run()
        save.assert_called_once()
        first_id = save.call_args.args[2]
        app.button[0].click().run()
        self.assertEqual(save.call_args.args[2], first_id)

    @patch("catalog.configured", return_value=True)
    @patch("catalog.list_titles", return_value=[{"id": "00000000-0000-0000-0000-000000000001", "title": "Example", "language": "en", "created_at": "2026-01-01"}])
    @patch("catalog.delete_title")
    def test_delete_requires_confirmation(self, delete, listing, configured):
        app = AppTest.from_string('from catalog_ui import render_catalog\nrender_catalog(lambda en, ko: en)').run()
        app.button[0].click().run()
        delete.assert_not_called()
        app.checkbox[0].check()
        app.button[0].click().run()
        delete.assert_called_once_with("00000000-0000-0000-0000-000000000001")
