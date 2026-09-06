import importlib.util
from pathlib import Path
import sys
import unittest

MODULE = Path(__file__).resolve().parents[1] / "phase5.py"
spec = importlib.util.spec_from_file_location("phase5", MODULE)
phase5 = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = phase5
spec.loader.exec_module(phase5)


class FormatControlTests(unittest.TestCase):
    def test_bidi_controls_are_diagnostic_not_corruption(self):
        text = "هذا نص عربي صحيح " + "\u200f" + ("فقهي واضح " * 20)
        self.assertGreater(phase5.nonsemantic_format_control_count(text), 0)
        self.assertNotIn("bidi_or_invisible_artifact", phase5.corruption_reasons(text))

    def test_strip_controls_preserves_base_text(self):
        text = "بسم\u200f الله\u2067 الرحمن"
        self.assertEqual(
            phase5.strip_nonsemantic_format_controls(text),
            "بسم الله الرحمن",
        )

    def test_real_corruption_still_blocks(self):
        self.assertIn(
            "replacement_character",
            phase5.corruption_reasons("هذا � نص " + ("عربي " * 30)),
        )
        self.assertIn(
            "arabic_embedded_digit",
            phase5.corruption_reasons("الأ6سباب " + ("عربي " * 30)),
        )


if __name__ == "__main__":
    unittest.main()
