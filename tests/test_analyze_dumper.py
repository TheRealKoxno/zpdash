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
    actions=None,
    edit_versions: int = 1,
) -> bytes:
    actions = actions or ["CMD_NAVIGATE"]
    branches = "".join(
        f'<Branch Type="HtmlElement" Action="{action}" />'
        for action in actions
    )
    edit_items = []
    for idx in range(edit_versions):
        edit_items.append(
            {
                "Type": "EditInfo",
                "Time": iso_time,
                "History": {
                    "State": f"<Root>{branches}{state_url}</Root>"
                },
            }
        )
    records = [
        {
            "Type": "Metadata",
            "CustomerId": f"{guid}@example.com",
            "ProjectId": project_id,
            "Variant": variant,
            "Time": iso_time,
        },
    ] + edit_items

    payload = io.BytesIO()
    with zipfile.ZipFile(payload, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("history-1.json", json.dumps(records, ensure_ascii=False))
    return payload.getvalue()


def _make_project_record(
    *,
    guid: str = "guid-1",
    variant: str = "pro",
    project_id: str = "P-1",
    project_time: str = "2026-02-24 10:00:00",
    domains=None,
    operations=None,
    unique_actions: int = 1,
    edit_versions: int = 1,
    theme: str = "Регистрация/аккаунты",
    table_names=None,
):
    return analyze_dumper.ProjectRecord(
        guid=guid,
        user_dir="User 1",
        session="Session 1. 2026-02-24 10-00",
        session_time=datetime(2026, 2, 24, 10, 0, 0),
        project_file="Project 1.zip",
        project_number=1,
        project_id=project_id,
        variant=variant,
        meta_time=datetime.fromisoformat(project_time),
        project_time=datetime.fromisoformat(project_time),
        snapshots_count=1,
        edit_versions=edit_versions,
        domains=set(domains or []),
        operations=list(operations or []),
        theme=theme,
        theme_tags=[],
        unique_actions=unique_actions,
        action_pairs=set(),
        table_names=list(table_names or []),
        error_events=[],
        last_edit_time=datetime.fromisoformat(project_time),
        last_error_time=None,
        ended_on_error=False,
    )


class AnalyzeDumperMeaningfulProjectTests(unittest.TestCase):
    def test_project_meaningfulness_excludes_trivial_and_learning_templates(self) -> None:
        meaningful = _make_project_record(
            project_id="P-meaningful",
            domains={"example.com"},
            operations=["Навигация по сайтам", "Формы/клики/DOM"],
            unique_actions=4,
            edit_versions=4,
        )
        trivial = _make_project_record(
            project_id="P-trivial",
            domains=set(),
            operations=["Прочие действия"],
            unique_actions=0,
            edit_versions=1,
        )
        learning = _make_project_record(
            project_id="P-learning",
            domains={"lessons.zennolab.com"},
            operations=["Навигация по сайтам"],
            unique_actions=1,
            edit_versions=1,
            theme="Служебная автоматизация",
        )

        is_meaningful, score, reason = analyze_dumper.project_meaningfulness(meaningful)
        self.assertTrue(is_meaningful)
        self.assertGreaterEqual(score, 2)
        self.assertIn("внешние_домены", reason)

        self.assertFalse(analyze_dumper.project_meaningfulness(trivial)[0])
        self.assertFalse(analyze_dumper.project_meaningfulness(learning)[0])

    def test_meaningful_projects_per_user_by_day_rows_use_only_meaningful_projects(self) -> None:
        projects = [
            _make_project_record(
                guid="guid-pro",
                variant="pro",
                project_id="P-pro-1",
                project_time="2026-02-24 10:00:00",
                domains={"example.com"},
                operations=["Навигация по сайтам", "Формы/клики/DOM"],
                unique_actions=4,
                edit_versions=3,
            ),
            _make_project_record(
                guid="guid-pro",
                variant="pro",
                project_id="P-pro-2",
                project_time="2026-02-24 11:00:00",
                domains={"example.org"},
                operations=["Навигация по сайтам", "HTTP/API запросы"],
                unique_actions=3,
                edit_versions=2,
            ),
            _make_project_record(
                guid="guid-lite",
                variant="lite",
                project_id="P-lite-1",
                project_time="2026-02-25 10:00:00",
                domains={"shop.example"},
                operations=["Навигация по сайтам", "Прокси/профили/эмуляция"],
                unique_actions=3,
                edit_versions=3,
            ),
            _make_project_record(
                guid="guid-pro",
                variant="pro",
                project_id="P-pro-trivial",
                project_time="2026-02-24 12:00:00",
                domains=set(),
                operations=["Прочие действия"],
                unique_actions=0,
                edit_versions=1,
            ),
        ]

        rows = analyze_dumper.build_meaningful_projects_per_user_by_day_rows(projects)
        by_key = {(row["date"], row["lite_or_pro"]): row for row in rows}

        self.assertEqual("2", by_key[("2026-02-24", "pro")]["meaningful_projects_count"])
        self.assertEqual("1", by_key[("2026-02-24", "pro")]["users_count"])
        self.assertEqual("2.00", by_key[("2026-02-24", "pro")]["avg_projects_per_user"])
        self.assertEqual("2.00", by_key[("2026-02-24", "pro")]["median_projects_per_user"])

        self.assertEqual("1", by_key[("2026-02-25", "lite")]["meaningful_projects_count"])
        self.assertEqual("1", by_key[("2026-02-25", "lite")]["users_count"])
        self.assertEqual("1.00", by_key[("2026-02-25", "lite")]["avg_projects_per_user"])


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

    def test_analyze_writes_daily_meaningful_projects_csv(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            base = Path(td)
            src_dir = base / "src"
            out_dir = base / "out"

            session_pro = src_dir / "User 1" / "Session 1. 2026-02-24 10-00"
            session_lite = src_dir / "User 1" / "Session 2. 2026-02-25 10-00"
            session_pro.mkdir(parents=True, exist_ok=True)
            session_lite.mkdir(parents=True, exist_ok=True)

            (session_pro / "Project 1.zip").write_bytes(
                _make_project_zip_blob(
                    guid="guid-pro",
                    project_id="P-pro-1",
                    variant="Pro",
                    iso_time="2026-02-24T10:00:00",
                    state_url="https://example.com",
                    actions=["CMD_NAVIGATE", "RiseEvent", "If"],
                    edit_versions=3,
                )
            )
            (session_pro / "Project 2.zip").write_bytes(
                _make_project_zip_blob(
                    guid="guid-pro",
                    project_id="P-pro-trivial",
                    variant="Pro",
                    iso_time="2026-02-24T11:00:00",
                    state_url="",
                    actions=["SetValue"],
                    edit_versions=1,
                )
            )
            (session_lite / "Project 3.zip").write_bytes(
                _make_project_zip_blob(
                    guid="guid-lite",
                    project_id="P-lite-1",
                    variant="Lite",
                    iso_time="2026-02-25T10:00:00",
                    state_url="https://example.org",
                    actions=["CMD_NAVIGATE", "TouchEvent", "CheckText"],
                    edit_versions=3,
                )
            )

            analyze_dumper.analyze(
                data_sources=[src_dir],
                out_dir=out_dir,
                window_end=datetime(2026, 2, 25, 23, 59, 59),
                window_label="test window",
            )

            with (out_dir / "dashboard_projects_per_user_by_day.csv").open("r", encoding="utf-8") as f:
                rows = list(csv.DictReader(f))
            by_key = {(row["date"], row["lite_or_pro"]): row for row in rows}
            self.assertEqual("1", by_key[("2026-02-24", "pro")]["meaningful_projects_count"])
            self.assertEqual("1", by_key[("2026-02-24", "pro")]["users_count"])
            self.assertEqual("1.00", by_key[("2026-02-24", "pro")]["avg_projects_per_user"])
            self.assertEqual("1", by_key[("2026-02-25", "lite")]["meaningful_projects_count"])

            with (out_dir / "projects_detailed_dashboard.csv").open("r", encoding="utf-8") as f:
                project_rows = list(csv.DictReader(f))
            row_by_id = {row["project_id"]: row for row in project_rows}
            self.assertEqual("yes", row_by_id["P-pro-1"]["is_meaningful_project"])
            self.assertEqual("no", row_by_id["P-pro-trivial"]["is_meaningful_project"])


if __name__ == "__main__":
    unittest.main()
