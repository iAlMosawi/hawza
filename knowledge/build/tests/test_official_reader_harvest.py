import tempfile
import unittest
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from official_reader_harvest import FragmentParser, ReaderParser, select_sample


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

