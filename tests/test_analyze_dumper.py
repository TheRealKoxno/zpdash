import csv
import io
import json
import tempfile
import unittest
import zipfile
from datetime import datetime
from pathlib import Path

import analyze_dumper


def _make_project_zip_blob(
    guid: str,
    project_id: str,
    variant: str,
    iso_time: str,
    state_url: str,
) -> bytes:
    records = [
        {
            "Type": "Metadata",
            "CustomerId": f"{guid}@example.com",
            "ProjectId": project_id,
            "Variant": variant,
            "Time": iso_time,
        },
        {
            "Type": "EditInfo",
            "Time": iso_time,
            "History": {
                "State": (
                    f'<Root><Branch Type="HtmlElement" Action="CMD_NAVIGATE" />'
                    f'{state_url}</Root>'
                )
            },
        },
    ]

    payload = io.BytesIO()
    with zipfile.ZipFile(payload, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("history-1.json", json.dumps(records, ensure_ascii=False))
    return payload.getvalue()


class AnalyzeDumperMergeSourcesTests(unittest.TestCase):
    def test_merge_directory_and_zip_dedupes_overlapping_24_feb(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            base = Path(td)
            src_dir = base / "src_16_24"
            out_dir = base / "out"
            src_zip = base / "src_24_28.zip"

            dir_session = src_dir / "User 1" / "Session 1. 2026-02-24 10-00"
            dir_session.mkdir(parents=True, exist_ok=True)
            overlap_line = "2026-02-24-10-00-00 https://ya.ru/path"
            (dir_session / "urlStatistics.txt").write_text(overlap_line + "\n", encoding="utf-8")

            p1_blob = _make_project_zip_blob(
                guid="guid-1",
                project_id="P-1",
                variant="Pro",
                iso_time="2026-02-24T10:00:00",
                state_url="https://ya.ru/path",
            )
            (dir_session / "Project 1.zip").write_bytes(p1_blob)

            p2_blob = _make_project_zip_blob(
                guid="guid-1",
                project_id="P-2",
                variant="Pro",
                iso_time="2026-02-25T11:00:00",
                state_url="https://ya.ru/new",
            )

            with zipfile.ZipFile(src_zip, "w", zipfile.ZIP_DEFLATED) as zf:
                root = "24feb-28feb"
                zf.writestr(
                    f"{root}/User 1/Session 1. 2026-02-24 10-00/urlStatistics.txt",
                    overlap_line + "\n",
                )
                zf.writestr(
                    f"{root}/User 1/Session 1. 2026-02-24 10-00/Project 1.zip",
                    p1_blob,
                )
                zf.writestr(
                    f"{root}/User 1/Session 2. 2026-02-25 11-00/urlStatistics.txt",
                    "2026-02-25-11-00-00 https://ya.ru/new\n",
                )
                zf.writestr(
                    f"{root}/User 1/Session 2. 2026-02-25 11-00/Project 2.zip",
                    p2_blob,
                )

            analyze_dumper.analyze(
                data_sources=[src_dir, src_zip],
                out_dir=out_dir,
                window_end=datetime(2026, 2, 28, 23, 59, 59),
                window_label="16 Feb - 28 Feb 2026",
            )

            with (out_dir / "projects_detailed_dashboard.csv").open("r", encoding="utf-8") as f:
                projects = list(csv.DictReader(f))
            self.assertEqual(2, len(projects))

            by_pid = {row["project_id"]: row for row in projects}
            self.assertIn("P-1", by_pid)
            self.assertIn("P-2", by_pid)
            self.assertEqual("1", by_pid["P-1"]["snapshots_count"])

            with (out_dir / "dashboard_top_sites.csv").open("r", encoding="utf-8") as f:
                top_sites = list(csv.DictReader(f))
            yandex = next((r for r in top_sites if r["domain"] == "yandex.ru"), None)
            self.assertIsNotNone(yandex)
            self.assertEqual("2", yandex["projects_count"])

            with (out_dir / "users_profile_dashboard.csv").open("r", encoding="utf-8") as f:
                users = list(csv.DictReader(f))
            self.assertEqual(1, len(users))
            user = users[0]
            self.assertEqual("2", user["projects_count"])
            self.assertEqual("2", user["active_days"])
            self.assertEqual("yes", user["left_more_than_1_day"])
            self.assertIn("inactive_hours_till_window_end", user)


if __name__ == "__main__":
    unittest.main()
