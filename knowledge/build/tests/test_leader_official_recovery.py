import importlib.util
from pathlib import Path
import sys
import unittest

MODULE = Path(__file__).resolve().parents[1] / "leader_official_recovery.py"
spec = importlib.util.spec_from_file_location("leader_recovery", MODULE)
module = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = module
spec.loader.exec_module(module)


class LeaderRecoveryTests(unittest.TestCase):
    def test_keeps_heading_and_answer_but_not_site_chrome(self):
        html = '''<header>العربية site navigation</header><main id="body">
        <article id="tree_content"><article class="content"><div class="article_heading"><h6>كتاب الطهارة</h6></div>
        <div class="details"><p>السؤال: هل يجوز؟</p><p>الجواب: نعم، مع الشرائط.</p><script>var x = 1</script></div></article></article>
        <div class="language-list">العربية English فارسی</div><a>التالي</a></main>'''.encode()
        text = module.extract_book(html)
        self.assertIn("كتاب الطهارة", text)
        self.assertIn("الجواب: نعم", text)
        self.assertNotIn("var x", text)
        self.assertNotIn("العربية English", text)
        self.assertNotIn("التالي", text)


if __name__ == "__main__":
    unittest.main()
