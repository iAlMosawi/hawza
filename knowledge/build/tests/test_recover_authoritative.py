import importlib.util
from pathlib import Path
import unittest
import sys

MODULE = Path(__file__).resolve().parents[1] / "recover_authoritative.py"
spec = importlib.util.spec_from_file_location("recover_authoritative", MODULE)
recover = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = recover
spec.loader.exec_module(recover)


class SistaniExpansionTests(unittest.TestCase):
    def test_sistani_parser_excludes_script_content(self):
        parser = recover.SemanticText("sistani")
        parser.feed('''<div id="main-book-content">
          <div class="part-search"><span>البحث في:</span><select><option>جميع الكتب</option></select><button>ابحث</button></div>
          <a class="fr">السابق التالي</a><h1>كتاب الطهارة » فصل في الوضوء</h1>
          <div class="baz book-text"><p>مسألة 1: هذا هو نص الحكم الشرعي.</p><script>var branch_id = 1</script></div>
          <div class="book-list">كتاب آخر unrelated</div><div class="language-list">العربية فارسی اردو English</div>
        </div>''')
        text = " ".join(parser.parts)
        self.assertIn("مسألة 1", text)
        self.assertIn("كتاب الطهارة", text)
        self.assertNotIn("var branch_id", text)
        self.assertNotIn("البحث في", text)
        self.assertNotIn("جميع الكتب", text)
        self.assertNotIn("كتاب آخر", text)
        self.assertNotIn("العربية فارسی اردو English", text)
        self.assertNotIn("السابق التالي", text)

    def test_collects_only_same_book_sections_sorted_and_deduplicated(self):
        raw = b'''<html><body>
        <a href="/arabic/book/23720/4744/">late</a>
        <a href="/arabic/book/23720/3601/">first</a>
        <a href="/arabic/book/23720/3601/">duplicate</a>
        <a href="/arabic/book/15/100/">other book</a>
        <a href="https://example.com/arabic/book/23720/1/">external</a>
        </body></html>'''
        urls = recover.sistani_section_urls("https://www.sistani.org/arabic/book/23720/", raw)
        self.assertEqual(urls, [
            "https://www.sistani.org/arabic/book/23720/3601/",
            "https://www.sistani.org/arabic/book/23720/4744/",
        ])

    def test_non_root_url_is_not_expanded(self):
        raw = b'<a href="/arabic/book/23720/3602/">next</a>'
        self.assertEqual(
            recover.sistani_section_urls("https://www.sistani.org/arabic/book/23720/3601/", raw),
            [],
        )

    def test_shirazi_dynamic_reader_not_treated_as_static_book(self):
        self.assertEqual(recover.registry_urls({
            "official_reader_url": "https://www.alshirazi.org/library-htmlItem/203?langs=AR",
            "official_section_endpoint": "https://www.alshirazi.org/esteftatreatiseBook",
        }), [])


if __name__ == "__main__":
    unittest.main()
