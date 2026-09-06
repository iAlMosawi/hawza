import importlib.util
from pathlib import Path
import sys
import unittest

MODULE = Path(__file__).resolve().parents[1] / "recover_shirazi_static.py"
spec = importlib.util.spec_from_file_location("recover_shirazi_static", MODULE)
recover = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = recover
spec.loader.exec_module(recover)


class ShiraziStaticRecoveryTests(unittest.TestCase):
    def test_extracts_book_and_excludes_related_books(self):
        body = " ".join([
            "مقدمة المسائل الاسلامية",
            "أصول الدين",
            "أحكام التقليد",
            "أحكام الطهارة",
            "أحكام الصلاة",
            "أحكام الصوم",
            "أحكام الإرث",
            "نص فقهي " * 15000,
            "كتب ذات صلة",
            "كتاب لا ينبغي إدخاله",
        ])
        html = f"<html><body><nav>تنقل</nav><main>{body}</main><script>bad()</script></body></html>"
        text = recover.extract_book_text(html)
        self.assertIn("أحكام التقليد", text)
        self.assertIn("أحكام الإرث", text)
        self.assertNotIn("كتاب لا ينبغي إدخاله", text)
        self.assertNotIn("bad()", text)

    def test_refuses_missing_end_marker(self):
        html = "<p>مقدمة المسائل الاسلامية</p>" + "<p>نص</p>" * 50000
        with self.assertRaisesRegex(RuntimeError, "end marker"):
            recover.extract_book_text(html)

    def test_refuses_replacement_character(self):
        body = " ".join([
            "مقدمة المسائل الاسلامية", "أصول الدين", "أحكام التقليد",
            "أحكام الطهارة", "أحكام الصلاة", "أحكام الصوم", "أحكام الإرث",
            ("نص فقهي " * 15000) + "�", "كتب ذات صلة",
        ])
        with self.assertRaisesRegex(RuntimeError, "unsafe/corrupt"):
            recover.extract_book_text(f"<body>{body}</body>")


if __name__ == "__main__":
    unittest.main()
