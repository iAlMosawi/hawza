import json
import sqlite3
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from phase5 import corruption_reasons


SCRIPT = Path(__file__).resolve().parents[1] / "build_knowledge.py"


class BuildKnowledgeTests(unittest.TestCase):
    def test_current_v1_database_remains_valid(self):
        database = Path(__file__).resolve().parents[2] / "output" / "hawza_knowledge.sqlite"
        validator = Path(__file__).resolve().parents[1] / "validate_knowledge.py"
        result = subprocess.run(
            [sys.executable, str(validator), "--db", str(database), "--query", "التوحيد"],
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("schema_version: 1", result.stdout)

    def test_known_corruption_patterns_are_never_accepted(self):
        for value in ("�", "ليzس", "الأ6سباب", "الم}ضار"):
            self.assertTrue(corruption_reasons("نص عربي طويل " + value + " للاختبار " * 20))

    def test_builds_searchable_database_from_reviewed_chunk(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            processed = root / "processed"
            processed.mkdir()
            sources = root / "sources"
            sources.mkdir()
            (root / "manifest.json").write_text(json.dumps({"version": "1.0.0", "chunking": {"target_chars": 500, "overlap_chars": 0, "min_chars": 10}, "sources": [{"id": "aqidah-001", "path": "aqidah.txt", "title": "كتاب مثال", "category": "aqidah", "enabled": True}]}), encoding="utf-8")
            (sources / "aqidah.txt").write_text(
                "نص تجريبي حول التوحيد يشتمل على معلومات تقنية لا تمثل مصدرا دينيا. "
                "هذا النص طويل بما يكفي لاختبار بوابة الجودة التقنية دون ادعاء "
                "أنه دليل ديني أو مصدر صالح للإجابة النهائية.",
                encoding="utf-8",
            )
            output = root / "hawza_knowledge.sqlite"
            result = subprocess.run(
                [sys.executable, str(SCRIPT), "--manifest", str(root / "manifest.json"), "--sources", str(sources), "--output", str(output)],
                capture_output=True,
                text=True,
                check=False,
            )

            self.assertEqual(result.returncode, 0, result.stderr)
            with sqlite3.connect(output) as connection:
                self.assertGreaterEqual(connection.execute("SELECT count(*) FROM chunks").fetchone()[0], 1)
                self.assertEqual(connection.execute("SELECT source_id FROM chunks_fts WHERE chunks_fts MATCH 'التوحيد'").fetchone()[0], "aqidah-001")

    def test_rejects_manifest_source_that_is_missing_from_disk(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            sources = root / "sources"
            sources.mkdir()
            (root / "manifest.json").write_text(json.dumps({"version": "1.0.0", "sources": [{"id": "missing", "path": "missing.txt", "title": "Missing", "enabled": True}]}), encoding="utf-8")

            result = subprocess.run(
                [sys.executable, str(SCRIPT), "--manifest", str(root / "manifest.json"), "--sources", str(sources), "--output", str(root / "output.sqlite")],
                capture_output=True,
                text=True,
                check=False,
            )

            self.assertNotEqual(result.returncode, 0)
            self.assertIn("Manifest source not found", result.stderr)

    def test_phase5_excludes_pending_rejected_and_corrupted_evidence(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            sources = root / "sources"
            sources.mkdir()
            clean = "هذا نص عربي سليم وطويل بما يكفي لاختبار البحث في قاعدة المعرفة. " * 3
            (sources / "approved.txt").write_text(clean, encoding="utf-8")
            (sources / "pending.txt").write_text(clean.replace("سليم", "معلق"), encoding="utf-8")
            (sources / "rejected.txt").write_text(clean.replace("سليم", "مرفوض"), encoding="utf-8")
            (sources / "bad.txt").write_text("هذا نص � تالف لا يجوز عرضه كدليل ديني. " * 4, encoding="utf-8")
            manifest = {
                "version": "2.0-test",
                "phase5": {"legacy_source_ids": []},
                "chunking": {"target_chars": 500, "overlap_chars": 0, "min_chars": 20},
                "sources": [
                    {"id": "approved", "path": "approved.txt", "title": "Approved", "category": "aqeedah", "review_status": "approved", "enabled": True},
                    {"id": "pending", "path": "pending.txt", "title": "Pending", "category": "aqeedah", "enabled": True},
                    {"id": "rejected", "path": "rejected.txt", "title": "Rejected", "category": "aqeedah", "review_status": "rejected", "enabled": True},
                    {"id": "bad", "path": "bad.txt", "title": "Bad", "category": "hadith", "review_status": "approved", "enabled": True},
                ],
            }
            manifest_path = root / "manifest.json"
            manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
            output = root / "phase5.sqlite"
            report = root / "report.json"
            result = subprocess.run(
                [sys.executable, str(SCRIPT), "--manifest", str(manifest_path), "--sources", str(sources), "--output", str(output), "--quality-report", str(report)],
                capture_output=True,
                text=True,
                check=False,
            )

            self.assertNotEqual(result.returncode, 0)
            self.assertIn("No usable, safe text", result.stderr)
            # A release with an approved source whose complete extraction is
            # corrupt must fail instead of silently publishing partial data.
            self.assertFalse(output.exists())

    def test_phase5_pending_and_rejected_sources_are_not_searchable(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            sources = root / "sources"
            sources.mkdir()
            clean = "هذا نص عربي سليم وطويل بما يكفي لاختبار البحث في قاعدة المعرفة. " * 3
            for name in ("approved", "pending", "rejected"):
                (sources / f"{name}.txt").write_text(clean + name, encoding="utf-8")
            manifest = {
                "version": "2.0-test",
                "phase5": {"legacy_source_ids": []},
                "chunking": {"target_chars": 500, "overlap_chars": 0, "min_chars": 20},
                "sources": [
                    {"id": "approved", "path": "approved.txt", "title": "Approved", "category": "aqeedah", "review_status": "approved", "enabled": True},
                    {"id": "pending", "path": "pending.txt", "title": "Pending", "category": "aqeedah", "enabled": True},
                    {"id": "rejected", "path": "rejected.txt", "title": "Rejected", "category": "aqeedah", "review_status": "rejected", "enabled": True},
                ],
            }
            manifest_path = root / "manifest.json"
            manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
            output = root / "phase5.sqlite"
            result = subprocess.run([sys.executable, str(SCRIPT), "--manifest", str(manifest_path), "--sources", str(sources), "--output", str(output)], capture_output=True, text=True, check=False)
            self.assertEqual(result.returncode, 0, result.stderr)
            with sqlite3.connect(output) as connection:
                self.assertEqual(connection.execute("SELECT value FROM build_meta WHERE key='schema_version'").fetchone()[0], "2")
                self.assertEqual(connection.execute("SELECT count(*) FROM chunks WHERE source_id='approved'").fetchone()[0], 1)
                self.assertEqual(connection.execute("SELECT count(*) FROM chunks WHERE source_id IN ('pending', 'rejected')").fetchone()[0], 0)
                self.assertEqual(connection.execute("SELECT review_status FROM sources WHERE id='pending'").fetchone()[0], "pending")

    def test_phase5_legacy_source_is_compatible_without_claiming_approval(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            sources = root / "sources"
            sources.mkdir()
            (sources / "legacy.txt").write_text("هذا نص عربي سليم وطويل بما يكفي لاختبار توافق المصدر القديم. " * 3, encoding="utf-8")
            manifest = {
                "version": "2.0-test",
                "phase5": {"legacy_source_ids": ["legacy"]},
                "chunking": {"target_chars": 500, "overlap_chars": 0, "min_chars": 20},
                "sources": [{"id": "legacy", "path": "legacy.txt", "title": "Legacy", "category": "aqidah", "enabled": True}],
            }
            manifest_path = root / "manifest.json"
            manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
            output = root / "phase5.sqlite"
            result = subprocess.run([sys.executable, str(SCRIPT), "--manifest", str(manifest_path), "--sources", str(sources), "--output", str(output)], capture_output=True, text=True, check=False)
            self.assertEqual(result.returncode, 0, result.stderr)
            with sqlite3.connect(output) as connection:
                self.assertEqual(connection.execute("SELECT review_status FROM sources WHERE id='legacy'").fetchone()[0], "legacy_trusted")
