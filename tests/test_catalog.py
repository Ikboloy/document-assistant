import json
import os
import unittest
from unittest.mock import patch, MagicMock
import catalog

class CatalogTests(unittest.TestCase):
    @patch.dict(os.environ, {}, clear=True)
    def test_disabled_without_configuration(self):
        self.assertFalse(catalog.configured())
        with self.assertRaises(catalog.CatalogError):
            catalog.list_titles()

    @patch("catalog.execute")
    def test_title_uses_variables_and_stable_id(self, execute):
        execute.return_value = {"insert_documents_one": {"id": "ok"}}
        title = 'Quote " and 한글'
        uid = "00000000-0000-0000-0000-000000000001"
        catalog.save_title(title, "ko", uid)
        query, variables = execute.call_args.args
        self.assertNotIn(title, query)
        self.assertEqual(variables["object"], {"id": uid, "title": title, "language": "ko"})
        self.assertIn("on_conflict", query)

    @patch("catalog.execute")
    def test_invalid_title_does_not_send(self, execute):
        for title, language in [("", "en"), ("x"*201, "en"), ("ok", "xx")]:
            with self.assertRaises(catalog.CatalogError):
                catalog.save_title(title, language, "00000000-0000-0000-0000-000000000001")
        execute.assert_not_called()

    @patch.dict(os.environ, {"HASURA_ENDPOINT": "http://localhost:8080/v1/graphql", "HASURA_GRAPHQL_ADMIN_SECRET": "test-only"})
    @patch("urllib.request.urlopen")
    def test_transport_errors_do_not_expose_secret(self, urlopen):
        urlopen.side_effect = OSError("test-only private detail")
        with self.assertRaises(catalog.CatalogError) as error:
            catalog.list_titles()
        self.assertNotIn("test-only", str(error.exception))

    @patch.dict(os.environ, {"HASURA_ENDPOINT": "http://localhost:8080/v1/graphql", "HASURA_GRAPHQL_ADMIN_SECRET": "test-only"})
    @patch("urllib.request.urlopen")
    def test_graphql_errors_are_not_success(self, urlopen):
        urlopen.return_value.__enter__.return_value.read.return_value = json.dumps({"errors": [{"message": "private"}]}).encode()
        with self.assertRaises(catalog.CatalogError):
            catalog.list_titles()
