import tempfile
import unittest
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from official_reader_harvest import FragmentParser, OfficialReaderClient, ReaderParser, select_sample


class OfficialReaderHarvestTests(unittest.TestCase):
    def test_reader_parser_extracts_token_and_toc(self):
        parser = ReaderParser()
        parser.feed('<meta name="csrf-token" content="token"><span class="acar_span" rel="73">مقدمة</span>')
        self.assertEqual(parser.csrf, "token")
        self.assertEqual(parser.toc, [{"id": "73", "title": "مقدمة"}])

    def test_fragment_parser_excludes_navigation(self):
        parser = FragmentParser()
        parser.feed('<div>header</div><div class="rtl"><p>نص عربي</p><p>مسألة</p></div><div>footer</div>')
        self.assertEqual(parser.parts, ["نص عربي", "مسألة"])

    def test_sample_is_evenly_spread(self):
        toc = [{"id": str(i), "title": str(i)} for i in range(532)]
        sample = select_sample(toc)
        self.assertEqual(len(sample), 25)
        self.assertEqual(sample[0]["id"], "0")
        self.assertEqual(sample[-1]["id"], "531")

    def test_valid_cache_is_reused_without_request(self):
        with tempfile.TemporaryDirectory() as directory:
            client = OfficialReaderClient(Path(directory))
            item = {"id": "1", "title": "مقدمة"}
            client._request = lambda *args, **kwargs: (_ for _ in ()).throw(AssertionError("redownloaded"))
            raw = '<div class="rtl">نص عربي سليم</div>'
            client.cache.joinpath("1.html").write_text(raw, encoding="utf-8")
            import hashlib, json
            client.state_path.write_text(json.dumps({"records": {"1": {"status": "ok", "raw_html_sha256": hashlib.sha256(raw.encode()).hexdigest()}}}), encoding="utf-8")
            self.assertEqual(client.fetch_section("token", item).status, "ok")

    def test_partial_harvest_has_failed_ids_and_is_not_complete(self):
        with tempfile.TemporaryDirectory() as directory:
            client = OfficialReaderClient(Path(directory), retries=0)
            client._request = lambda *args, **kwargs: (_ for _ in ()).throw(RuntimeError("offline"))
            record = client.fetch_section("token", {"id": "missing", "title": "مفقود"})
            self.assertEqual(record.status, "failed")
            self.assertIn("missing", json.loads(client.state_path.read_text())["records"])
