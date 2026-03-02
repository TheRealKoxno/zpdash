#!/usr/bin/env python3
import csv
import html
import ipaddress
import json
import os
import re
import zipfile
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Set, Tuple
from urllib.parse import urlparse


BASE_DIR = Path("/Users/ilyazenno/Downloads/Dumper (16feb-24feb)")
OUT_DIR = Path("/Users/ilyazenno/Desktop/zp_dumper/dashboard_output")
WINDOW_END = datetime(2026, 2, 24, 23, 59, 59)


URL_RE = re.compile(r"https?://[^\s\"'<>]+", re.IGNORECASE)
BRANCH_RE = re.compile(r"<Branch\b([^>]*)>", re.IGNORECASE)
TYPE_ATTR_RE = re.compile(r'\bType="([^"]*)"')
ACTION_ATTR_RE = re.compile(r'\bAction="([^"]*)"')
TABLE_NAME_RE = re.compile(r'<Table\b[^>]*\bName="([^"]+)"', re.IGNORECASE)
VALID_DOMAIN_RE = re.compile(r"^(?:[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?\.)+[a-z]{2,63}$")
USER_DIR_RE = re.compile(r"^User \d+$")
SESSION_RE = re.compile(r"^Session \d+\. (\d{4}-\d{2}-\d{2}) (\d{2})-(\d{2})$")
PROJECT_ZIP_RE = re.compile(r"^Project (\d+)\.zip$")


SOCIAL_DOMAINS = {
    "facebook.com",
    "instagram.com",
    "tiktok.com",
    "vk.com",
    "ok.ru",
    "x.com",
    "twitter.com",
    "youtube.com",
    "telegram.org",
    "web.telegram.org",
}

ECOM_DOMAINS = {
    "amazon.com",
    "ebay.com",
    "aliexpress.com",
    "ozon.ru",
    "wildberries.ru",
    "avito.ru",
}

SEARCH_EMAIL_UTILITY = {
    "google.com",
    "bing.com",
    "mail.ru",
    "yandex.ru",
    "yandex.com",
    "outlook.live.com",
    "gmail.com",
}

LEVEL_ORDER = ["новичок", "средний", "продвинутый", "профессионал"]

# Domain canonicalization for "same site" aliases/subdomains.
EXACT_DOMAIN_ALIASES = {
    "ya.ru": "yandex.ru",
    "yandex.com": "yandex.ru",
    "twitter.com": "x.com",
    "t.me": "telegram.org",
    "web.telegram.org": "telegram.org",
    "api.telegram.org": "telegram.org",
}

SUFFIX_CANONICAL_DOMAINS: List[Tuple[str, str]] = [
    ("facebook.com", "facebook.com"),
    ("instagram.com", "instagram.com"),
    ("telegram.org", "telegram.org"),
    ("yandex.ru", "yandex.ru"),
    ("x.com", "x.com"),
]


@dataclass
class ErrorEvent:
    time: Optional[datetime]
    category: str
    message: str
    project_key: str


@dataclass
class ProjectRecord:
    guid: str
    user_dir: str
    session: str
    session_time: Optional[datetime]
    project_file: str
    project_number: Optional[int]
    project_id: str
    variant: str
    meta_time: Optional[datetime]
    project_time: Optional[datetime]
    edit_versions: int
    domains: Set[str]
    operations: List[str]
    theme: str
    theme_tags: List[str]
    unique_actions: int
    action_pairs: Set[str]
    table_names: List[str]
    error_events: List[ErrorEvent]


@dataclass
class UserStats:
    guid: str
    user_dirs: Set[str] = field(default_factory=set)
    variants: Counter = field(default_factory=Counter)
    project_records: List[ProjectRecord] = field(default_factory=list)
    url_domains: Counter = field(default_factory=Counter)
    url_events: int = 0
    errors: List[ErrorEvent] = field(default_factory=list)
    activity_times: List[datetime] = field(default_factory=list)
    active_days: Set[str] = field(default_factory=set)
    sessions: Set[str] = field(default_factory=set)
    action_pairs: Counter = field(default_factory=Counter)
    themes: Counter = field(default_factory=Counter)
    operations: Counter = field(default_factory=Counter)


def parse_iso_dt(value: Optional[str]) -> Optional[datetime]:
    if not value:
        return None
    text = value.strip()
    if not text:
        return None
    try:
        if text.endswith("Z"):
            text = text[:-1] + "+00:00"
        dt = datetime.fromisoformat(text)
        if dt.tzinfo is not None:
            dt = dt.replace(tzinfo=None)
        return dt
    except Exception:
        return None


def parse_session_dt(session_name: str) -> Optional[datetime]:
    match = SESSION_RE.match(session_name)
    if not match:
        return None
    date_part, hh, mm = match.groups()
    try:
        return datetime.strptime(f"{date_part} {hh}:{mm}", "%Y-%m-%d %H:%M")
    except Exception:
        return None


def parse_urlstats_dt(token: str) -> Optional[datetime]:
    try:
        return datetime.strptime(token, "%Y-%m-%d-%H-%M-%S")
    except Exception:
        return None


def extract_urls(text: str) -> List[str]:
    decoded = html.unescape(text or "")
    urls = []
    for raw in URL_RE.findall(decoded):
        cleaned = raw.strip().rstrip(".,);]'\"")
        if cleaned:
            urls.append(cleaned)
    return urls


def get_domain(url: str) -> Optional[str]:
    if not url:
        return None
    try:
        host = (urlparse(url).hostname or "").lower().strip(".")
    except Exception:
        return None
    if not host:
        return None
    host = host.replace("\\.", ".").replace("\\", "").strip(".")
    if host.startswith("www."):
        host = host[4:]
    if host in {"w3.org"}:
        return None
    if not host:
        return None
    try:
        ip = ipaddress.ip_address(host)
        return str(ip)
    except ValueError:
        pass
    if not VALID_DOMAIN_RE.match(host):
        return None
    return canonicalize_domain(host)


def canonicalize_domain(host: str) -> str:
    domain = (host or "").lower().strip(".")
    if not domain:
        return domain
    domain = EXACT_DOMAIN_ALIASES.get(domain, domain)
    for suffix, canonical in SUFFIX_CANONICAL_DOMAINS:
        if domain == suffix or domain.endswith("." + suffix):
            return canonical
    return domain


def is_external_domain(domain: str) -> bool:
    if not domain:
        return False
    if domain in {"about", "blank", "localhost"}:
        return False
    try:
        ip = ipaddress.ip_address(domain)
        if ip.is_loopback or ip.is_private or ip.is_link_local:
            return False
    except ValueError:
        pass
    if domain.endswith(".local"):
        return False
    return True


def normalize_error(message: str) -> str:
    if not message:
        return "Unknown error"
    lower = message.lower()
    rules = [
        ("extension installer not found", "Extension installer not found"),
        ("filenotfoundexception", "File not found"),
        ("file not found", "File not found"),
        ("timeout", "Timeout"),
        ("timed out", "Timeout"),
        ("captcha", "Captcha/anti-bot"),
        ("proxy", "Proxy issue"),
        ("connection refused", "Connection refused"),
        ("access denied", "Access denied"),
        ("unauthorized", "Unauthorized"),
        ("forbidden", "Forbidden"),
        ("429", "Rate limit"),
        ("500", "Server 500"),
        ("503", "Server unavailable"),
        ("element not found", "Element not found"),
        ("no such element", "Element not found"),
        ("cannot find", "Not found"),
        ("nullreferenceexception", "Null reference"),
        ("argumentexception", "Argument error"),
    ]
    for needle, label in rules:
        if needle in lower:
            return label
    head = re.split(r"[\r\n]+", message.strip())[0]
    head = re.sub(r"[0-9a-f]{8}-[0-9a-f-]{27,}", "<id>", head, flags=re.IGNORECASE)
    head = re.sub(r"\b\d{3,}\b", "<n>", head)
    head = re.sub(r"\s+", " ", head).strip(" -:;,.")
    return head[:140] if head else "Unknown error"


def parse_branch_actions(state_xml: str) -> Tuple[Set[str], Set[str]]:
    pairs: Set[str] = set()
    actions: Set[str] = set()
    for match in BRANCH_RE.finditer(state_xml or ""):
        attrs = match.group(1)
        type_match = TYPE_ATTR_RE.search(attrs)
        action_match = ACTION_ATTR_RE.search(attrs)
        type_value = type_match.group(1).strip() if type_match else ""
        action_value = action_match.group(1).strip() if action_match else ""
        if type_value or action_value:
            pair = f"{type_value}:{action_value}"
            pairs.add(pair)
            if action_value:
                actions.add(action_value)
    return pairs, actions


def classify_theme(
    domains: Set[str], action_pairs: Set[str], actions: Set[str], xml_text: str, urls: List[str]
) -> Tuple[str, List[str]]:
    text = (xml_text or "").lower() + " " + " ".join((u.lower() for u in urls))
    score = Counter()
    tags = set()

    if any(d in SOCIAL_DOMAINS or d.endswith(".facebook.com") for d in domains):
        score["Соцсети"] += 4
        tags.add("Соцсети")
    if any(d in ECOM_DOMAINS for d in domains):
        score["E-commerce/маркетплейсы"] += 4
        tags.add("E-commerce/маркетплейсы")
    if any(pair.startswith("GoogleSpreadsheets:") for pair in action_pairs) or any(
        u.startswith("https://docs.google.com/spreadsheets") or "spreadsheets.google.com" in u
        for u in urls
    ):
        score["Google Sheets/отчетность"] += 4
        tags.add("Google Sheets/отчетность")
    if any(k in text for k in ["tracking/", "utm_", "lead", "offer", "oferta", "affiliate", "clk?", "funnel"]):
        score["Лидогенерация/арбитраж"] += 5
        tags.add("Лидогенерация/арбитраж")
    if any(k in text for k in ["register", "signup", "login", "password", "auth", "telegram code", "otp", "sms"]):
        score["Регистрация/аккаунты"] += 4
        tags.add("Регистрация/аккаунты")
    if any(k in text for k in ["regex", "checktext", "parse", "xpath", "innerhtml", "page text"]):
        score["Парсинг/сбор данных"] += 3
        tags.add("Парсинг/сбор данных")
    if any(k in text for k in ["cmd_setproxy", "proxychecker", "profile", "emulation", "webrtc", "timezone", "canvas"]):
        score["Антидетект/прокси"] += 2
        tags.add("Антидетект/прокси")
    if any(k in text for k in ["http\" pictureindex", "action=\"post\"", "action=\"get\"", "/api/", "rest", "json"]):
        score["API-интеграции"] += 2
        tags.add("API-интеграции")
    if any(k in text for k in ["captcha", "recaptcha", "hcaptcha", "cloudflare"]):
        score["Антибот/капча"] += 2
        tags.add("Антибот/капча")

    if not score:
        if any(a in {"CMD_NAVIGATE", "RiseEvent", "TouchEvent", "KeyBoard"} for a in actions):
            score["Общая веб-автоматизация"] += 1
        else:
            score["Служебная автоматизация"] += 1

    primary = score.most_common(1)[0][0]
    return primary, sorted(tags)


def derive_operations(action_pairs: Set[str], actions: Set[str], xml_text: str) -> List[str]:
    text = (xml_text or "").lower()
    ops: List[str] = []
    if "CMD_NAVIGATE" in actions:
        ops.append("Навигация по сайтам")
    if any(
        a in actions
        for a in {"RiseEvent", "TouchEvent", "KeyBoard", "SetValue", "Click", "CheckText", "SendKeys"}
    ) or "type=\"htmlelement\"" in text:
        ops.append("Формы/клики/DOM")
    if any(pair.startswith("HTTP:") for pair in action_pairs) or any(a in {"Post", "Get"} for a in actions):
        ops.append("HTTP/API запросы")
    if any(pair.startswith("GoogleSpreadsheets:") or pair.startswith("Table") for pair in action_pairs):
        ops.append("Таблицы/Google Sheets")
    if any(
        a in actions
        for a in {"CheckText", "Regex", "Parse", "GetText", "GetHtml", "XPath", "InnerText"}
    ):
        ops.append("Парсинг/валидация")
    if any(
        a in actions for a in {"CMD_SETPROXY", "CMD_CLEARCACHE", "CMD_CLEARCOOKIE", "Load"}
    ) or any(pair.startswith("Profile:") or pair.startswith("ProxyChecker:") for pair in action_pairs):
        ops.append("Прокси/профили/эмуляция")
    if any(a in actions for a in {"If", "IncreaseCounter", "Pause", "Switch", "Loop"}) or "counter" in text:
        ops.append("Логика/ретраи")
    if not ops:
        ops.append("Прочие действия")
    return ops


def pick_variant(counter: Counter) -> str:
    if not counter:
        return "unknown"
    if len(counter) == 1:
        return next(iter(counter))
    top_two = counter.most_common(2)
    if top_two[0][1] == top_two[1][1]:
        return "mixed"
    return top_two[0][0]


def user_level_and_confidence(
    projects: int,
    unique_action_pairs: int,
    avg_edits: float,
    advanced_flags: int,
    theme_diversity: int,
    sessions: int,
) -> Tuple[str, float, float]:
    score = 0.0
    score += min(projects, 140) / 20.0
    score += min(unique_action_pairs, 50) / 10.0
    score += min(avg_edits, 20) / 5.0
    score += advanced_flags * 0.6
    score += min(theme_diversity, 6) * 0.5
    score += min(sessions, 8) * 0.2

    if score < 5:
        level = "новичок"
        nearest = 5
    elif score < 9:
        level = "средний"
        nearest = min(abs(score - 5), abs(score - 9))
    elif score < 14:
        level = "продвинутый"
        nearest = min(abs(score - 9), abs(score - 14))
    else:
        level = "профессионал"
        nearest = abs(score - 14)

    if isinstance(nearest, (int, float)):
        boundary_distance = min(float(nearest) / 3.0, 1.0)
    else:
        boundary_distance = 0.5
    volume = min(1.0, (projects / 20.0) + (sessions / 10.0))
    confidence = 0.45 + 0.30 * volume + 0.20 * boundary_distance
    confidence = max(0.45, min(0.96, confidence))
    return level, confidence, score


def top_counter_items(counter: Counter, limit: int = 3) -> List[str]:
    return [item for item, _ in counter.most_common(limit)]


def mean_and_median(values: List[int]) -> Tuple[float, float]:
    if not values:
        return 0.0, 0.0
    vals = sorted(values)
    n = len(vals)
    mean = sum(vals) / n
    mid = n // 2
    if n % 2:
        median = float(vals[mid])
    else:
        median = (vals[mid - 1] + vals[mid]) / 2.0
    return mean, median


def summarize_user(
    user: UserStats,
    projects_count: int,
    avg_edits: float,
    level: str,
    top_themes: List[str],
    top_domains: List[str],
    top_ops: List[str],
    top_error_category: str,
) -> Tuple[str, str, str, str]:
    occupation = " / ".join(top_themes[:2]) if top_themes else "общая веб-автоматизация"
    domains_text = ", ".join(top_domains[:3]) if top_domains else "без выраженных внешних доменов"
    success_bits = []
    if "Прокси/профили/эмуляция" in top_ops:
        success_bits.append("работает с прокси/профилями")
    if "HTTP/API запросы" in top_ops:
        success_bits.append("подключает API/HTTP")
    if "Таблицы/Google Sheets" in top_ops:
        success_bits.append("ведет учет в таблицах")
    if "Формы/клики/DOM" in top_ops:
        success_bits.append("уверенно автоматизирует формы и DOM-события")
    if not success_bits:
        success_bits.append("делает базовые сценарии навигации")
    success_text = "; ".join(success_bits[:3])

    if top_error_category and top_error_category != "—":
        failure_text = f"чаще всего стопорится на: {top_error_category.lower()}"
    elif avg_edits >= 8:
        failure_text = "много итераций на стабильность и доводку флоу"
    else:
        failure_text = "явных повторяющихся runtime-ошибок мало"

    style = "итеративно и практично"
    if projects_count > 40 and avg_edits > 6:
        style = "упорно и глубоко отлаживает похожие флоу"
    elif projects_count > 40 and len(top_themes) > 2:
        style = "широко работает по разным типам задач"
    elif projects_count < 8:
        style = "точечно, небольшим числом проектов"

    characteristic = (
        f"Занимается: {occupation}. Основные сайты: {domains_text}. "
        f"Стиль: {style}. Уровень: {level}."
    )
    occupation_full = f"{occupation}; чаще работает с сайтами: {domains_text}"
    return occupation_full, success_text, failure_text, characteristic


def analyze() -> None:
    if not BASE_DIR.exists():
        raise SystemExit(f"Data directory not found: {BASE_DIR}")
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    userdir_context: Dict[str, Dict] = defaultdict(
        lambda: {
            "session_times": [],
            "session_names": set(),
            "url_domains": Counter(),
            "url_events": 0,
            "url_times": [],
        }
    )
    userdir_guid_counter: Dict[str, Counter] = defaultdict(Counter)

    project_records: List[ProjectRecord] = []
    users: Dict[str, UserStats] = {}
    parse_failures = 0

    user_dirs = sorted([p for p in BASE_DIR.iterdir() if p.is_dir() and USER_DIR_RE.match(p.name)])

    for user_dir in user_dirs:
        user_key = user_dir.name
        sessions = sorted([p for p in user_dir.iterdir() if p.is_dir() and p.name.startswith("Session ")])
        for session_dir in sessions:
            session_name = session_dir.name
            session_time = parse_session_dt(session_name)
            userdir_context[user_key]["session_names"].add(session_name)
            if session_time:
                userdir_context[user_key]["session_times"].append(session_time)

            url_stats_file = session_dir / "urlStatistics.txt"
            if url_stats_file.exists():
                try:
                    with url_stats_file.open("r", encoding="utf-8", errors="ignore") as f:
                        for line in f:
                            line = line.strip()
                            if not line:
                                continue
                            parts = line.split(" ", 1)
                            token = parts[0]
                            maybe_dt = parse_urlstats_dt(token)
                            if maybe_dt:
                                userdir_context[user_key]["url_times"].append(maybe_dt)
                            url = parts[1].strip() if len(parts) > 1 else ""
                            domain = get_domain(url)
                            if domain and is_external_domain(domain):
                                userdir_context[user_key]["url_domains"][domain] += 1
                                userdir_context[user_key]["url_events"] += 1
                except Exception:
                    pass

            for file_path in session_dir.iterdir():
                if not file_path.is_file():
                    continue
                proj_match = PROJECT_ZIP_RE.match(file_path.name)
                if not proj_match:
                    continue

                project_number = int(proj_match.group(1))
                metadata = {}
                edit_records = []
                debug_records = []
                history_state = ""
                project_id = ""
                variant = "unknown"
                guid = ""
                meta_time = None
                record_times: List[datetime] = []
                error_events: List[ErrorEvent] = []

                try:
                    with zipfile.ZipFile(file_path) as zf:
                        history_names = [n for n in zf.namelist() if n.startswith("history-")]
                        if not history_names:
                            continue
                        payload = zf.read(history_names[0])
                        records = json.loads(payload)
                        if isinstance(records, dict):
                            records = [records]
                        if not isinstance(records, list):
                            continue
                except Exception:
                    parse_failures += 1
                    continue

                for rec in records:
                    if not isinstance(rec, dict):
                        continue
                    rec_type = rec.get("Type")
                    rec_time = parse_iso_dt(rec.get("Time"))
                    if rec_time:
                        record_times.append(rec_time)
                    if rec_type == "Metadata":
                        metadata = rec
                    elif rec_type == "EditInfo":
                        edit_records.append(rec)
                    elif rec_type == "DebugInfo":
                        debug_records.append(rec)

                customer_id = metadata.get("CustomerId", "")
                guid = customer_id.split("@", 1)[0] if customer_id else f"unknown::{user_key}"
                project_id = metadata.get("ProjectId", "")
                raw_variant = (metadata.get("Variant") or "").strip().lower()
                variant = "lite" if raw_variant == "lite" else "pro"
                meta_time = parse_iso_dt(metadata.get("Time"))
                if meta_time:
                    record_times.append(meta_time)

                userdir_guid_counter[user_key][guid] += 1
                user = users.setdefault(guid, UserStats(guid=guid))
                user.user_dirs.add(user_key)
                user.sessions.add(session_name)
                user.variants[variant] += 1

                latest_state_time = None
                latest_state = ""
                for edit in edit_records:
                    hist = edit.get("History") or {}
                    state = hist.get("State") or ""
                    if not state:
                        continue
                    e_time = parse_iso_dt(edit.get("Time"))
                    if latest_state_time is None or (e_time and e_time >= latest_state_time):
                        latest_state_time = e_time
                        latest_state = state
                history_state = latest_state

                action_pairs, actions = parse_branch_actions(history_state)
                urls = extract_urls(history_state)
                domains = {d for d in (get_domain(u) for u in urls) if d and is_external_domain(d)}
                table_names = sorted(set(TABLE_NAME_RE.findall(history_state)))
                operations = derive_operations(action_pairs, actions, history_state)
                theme, theme_tags = classify_theme(domains, action_pairs, actions, history_state, urls)

                project_key = f"{guid}::{session_name}::{file_path.name}"
                for dbg in debug_records:
                    err = dbg.get("Error") or {}
                    message = (err.get("Message") or "").strip()
                    exception = (err.get("ExceptionMessage") or "").strip()
                    joined = message
                    if exception and exception not in joined:
                        joined = f"{joined} | {exception}" if joined else exception
                    if not joined:
                        continue
                    category = normalize_error(joined)
                    e_time = parse_iso_dt(dbg.get("Time"))
                    if e_time:
                        record_times.append(e_time)
                    error_events.append(
                        ErrorEvent(
                            time=e_time,
                            category=category,
                            message=joined[:1200],
                            project_key=project_key,
                        )
                    )

                session_time = parse_session_dt(session_name)
                if session_time:
                    record_times.append(session_time)
                project_time = max(record_times) if record_times else None

                project_record = ProjectRecord(
                    guid=guid,
                    user_dir=user_key,
                    session=session_name,
                    session_time=session_time,
                    project_file=file_path.name,
                    project_number=project_number,
                    project_id=project_id,
                    variant=variant,
                    meta_time=meta_time,
                    project_time=project_time,
                    edit_versions=len(edit_records),
                    domains=domains,
                    operations=operations,
                    theme=theme,
                    theme_tags=theme_tags,
                    unique_actions=len(action_pairs),
                    action_pairs=action_pairs,
                    table_names=table_names,
                    error_events=error_events,
                )
                project_records.append(project_record)

                user.project_records.append(project_record)
                user.errors.extend(error_events)
                for t in record_times:
                    user.activity_times.append(t)
                    user.active_days.add(t.strftime("%Y-%m-%d"))
                for pair in action_pairs:
                    user.action_pairs[pair] += 1
                user.themes[theme] += 1
                for op in operations:
                    user.operations[op] += 1

    # Attach urlStatistics/session activity to resolved GUID per user folder.
    for user_dir, ctx in userdir_context.items():
        if userdir_guid_counter[user_dir]:
            guid = userdir_guid_counter[user_dir].most_common(1)[0][0]
        else:
            guid = f"unknown::{user_dir}"
            users.setdefault(guid, UserStats(guid=guid))
        user = users[guid]
        user.user_dirs.add(user_dir)
        for session_name in ctx["session_names"]:
            user.sessions.add(session_name)
        for t in ctx["session_times"]:
            user.activity_times.append(t)
            user.active_days.add(t.strftime("%Y-%m-%d"))
        for t in ctx["url_times"]:
            user.activity_times.append(t)
            user.active_days.add(t.strftime("%Y-%m-%d"))
        user.url_domains.update(ctx["url_domains"])
        user.url_events += ctx["url_events"]

    # Build aggregates.
    domain_stats = defaultdict(lambda: {"users": set(), "projects": 0, "ops": Counter(), "themes": Counter()})
    theme_stats = defaultdict(lambda: {"users": set(), "projects": 0, "ops": Counter()})
    global_errors = defaultdict(lambda: {"events": 0, "users": set(), "examples": []})
    errors_by_level = defaultdict(lambda: defaultdict(lambda: {"events": 0, "users": set()}))
    last_errors_by_level = defaultdict(Counter)
    errors_by_plan = defaultdict(lambda: defaultdict(lambda: {"events": 0, "users": set()}))
    last_errors_by_plan = defaultdict(Counter)
    per_user_rows = []
    per_project_rows = []
    last_error_counter = Counter()
    level_distribution = Counter()
    churn_counter = Counter()

    for project in project_records:
        for domain in project.domains:
            item = domain_stats[domain]
            item["users"].add(project.guid)
            item["projects"] += 1
            for op in project.operations:
                item["ops"][op] += 1
            item["themes"][project.theme] += 1

        t = theme_stats[project.theme]
        t["users"].add(project.guid)
        t["projects"] += 1
        for op in project.operations:
            t["ops"][op] += 1

        project_last_error = max(project.error_events, key=lambda e: e.time or datetime.min) if project.error_events else None
        per_project_rows.append(
            {
                "guid": project.guid,
                "user_dir": project.user_dir,
                "session": project.session,
                "project_file": project.project_file,
                "project_number": project.project_number if project.project_number is not None else "",
                "project_id": project.project_id,
                "variant": project.variant,
                "project_time": project.project_time.isoformat(sep=" ") if project.project_time else "",
                "edit_versions": project.edit_versions,
                "theme": project.theme,
                "theme_tags": ", ".join(project.theme_tags),
                "domains": ", ".join(sorted(project.domains)[:8]),
                "operations": ", ".join(project.operations),
                "unique_actions": project.unique_actions,
                "table_names": ", ".join(project.table_names[:8]),
                "errors_count": len(project.error_events),
                "last_error_category": project_last_error.category if project_last_error else "",
                "last_error_time": project_last_error.time.isoformat(sep=" ") if project_last_error and project_last_error.time else "",
                "last_error_message": project_last_error.message[:500] if project_last_error else "",
            }
        )

    for guid, user in users.items():
        if not user.project_records:
            continue
        projects_count = len(user.project_records)
        avg_edits = sum(p.edit_versions for p in user.project_records) / max(projects_count, 1)
        unique_action_pairs = len(user.action_pairs)
        top_themes = top_counter_items(user.themes, 3)
        top_ops = top_counter_items(user.operations, 4)
        top_domains = top_counter_items(user.url_domains, 5)
        user_variant = pick_variant(user.variants)

        # Estimate advanced features.
        advanced_flags = 0
        union_actions = set(user.action_pairs.keys())
        union_text = " ".join(union_actions).lower() + " " + " ".join(top_ops).lower()
        if "proxy" in union_text:
            advanced_flags += 1
        if "profile" in union_text:
            advanced_flags += 1
        if "http/api" in " ".join(top_ops).lower():
            advanced_flags += 1
        if "google sheets" in " ".join(top_ops).lower():
            advanced_flags += 1
        if "парсинг" in " ".join(top_ops).lower():
            advanced_flags += 1
        if unique_action_pairs >= 20:
            advanced_flags += 1
        if avg_edits >= 8:
            advanced_flags += 1
        if len(top_themes) >= 3:
            advanced_flags += 1

        level, confidence, score = user_level_and_confidence(
            projects=projects_count,
            unique_action_pairs=unique_action_pairs,
            avg_edits=avg_edits,
            advanced_flags=advanced_flags,
            theme_diversity=len(user.themes),
            sessions=len(user.sessions),
        )
        level_distribution[level] += 1

        # Errors
        top_error = Counter(e.category for e in user.errors)
        top_error_category = top_error.most_common(1)[0][0] if top_error else "—"
        top_error_count = top_error.most_common(1)[0][1] if top_error else 0
        last_error = max(user.errors, key=lambda e: e.time or datetime.min) if user.errors else None
        if last_error:
            last_error_counter[last_error.category] += 1
            last_errors_by_level[level][last_error.category] += 1
            last_errors_by_plan[user_variant][last_error.category] += 1
        last_error_text = last_error.category if last_error else "—"
        last_error_time = last_error.time if last_error else None

        # Activity/churn
        if user.activity_times:
            first_activity = min(user.activity_times)
            last_activity = max(user.activity_times)
        else:
            first_activity = None
            last_activity = None
        inactive_hours = (
            (WINDOW_END - last_activity).total_seconds() / 3600.0 if last_activity else None
        )
        left_flag = bool(inactive_hours is not None and inactive_hours > 24.0)
        churn_counter["ушел_>1д"] += 1 if left_flag else 0
        churn_counter["активен_<=1д"] += 0 if left_flag else 1

        occupation, success_text, failure_text, characteristic = summarize_user(
            user=user,
            projects_count=projects_count,
            avg_edits=avg_edits,
            level=level,
            top_themes=top_themes,
            top_domains=top_domains,
            top_ops=top_ops,
            top_error_category=top_error_category,
        )

        stop_points = top_error_category if top_error_category != "—" else (
            "итеративная отладка/стабильность" if avg_edits >= 8 else "без явного стоп-фактора"
        )

        per_user_rows.append(
            {
                "guid": guid,
                "user_dirs": ", ".join(sorted(user.user_dirs)),
                "lite_or_pro": user_variant,
                "projects_count": projects_count,
                "sessions_count": len(user.sessions),
                "active_days": len(user.active_days),
                "first_activity": first_activity.isoformat(sep=" ") if first_activity else "",
                "last_activity": last_activity.isoformat(sep=" ") if last_activity else "",
                "inactive_hours_till_2026_02_24_end": f"{inactive_hours:.1f}" if inactive_hours is not None else "",
                "left_more_than_1_day": "yes" if left_flag else "no",
                "top_sites": ", ".join(top_domains[:5]),
                "top_themes": ", ".join(top_themes[:4]),
                "main_operations": ", ".join(top_ops[:5]),
                "edit_versions_avg": f"{avg_edits:.2f}",
                "unique_action_pairs": unique_action_pairs,
                "top_error_category": top_error_category,
                "top_error_count": top_error_count,
                "last_error_category": last_error_text,
                "last_error_time": last_error_time.isoformat(sep=" ") if last_error_time else "",
                "stop_points": stop_points,
                "level": level,
                "confidence_pct": f"{confidence * 100:.1f}",
                "score": f"{score:.2f}",
                "occupation_in_zennoposter": occupation,
                "what_works": success_text,
                "what_not_works": failure_text,
                "characteristic": characteristic,
            }
        )

        for e in user.errors:
            item = global_errors[e.category]
            item["events"] += 1
            item["users"].add(guid)
            if len(item["examples"]) < 3:
                item["examples"].append(e.message[:220])
            level_item = errors_by_level[level][e.category]
            level_item["events"] += 1
            level_item["users"].add(guid)
            plan_item = errors_by_plan[user_variant][e.category]
            plan_item["events"] += 1
            plan_item["users"].add(guid)

    # Global dashboards
    top_sites_rows = []
    for domain, stat in sorted(
        domain_stats.items(),
        key=lambda kv: (len(kv[1]["users"]), kv[1]["projects"]),
        reverse=True,
    ):
        top_sites_rows.append(
            {
                "domain": domain,
                "users_count": len(stat["users"]),
                "projects_count": stat["projects"],
                "what_users_do": ", ".join([k for k, _ in stat["ops"].most_common(3)]),
                "top_themes": ", ".join([k for k, _ in stat["themes"].most_common(2)]),
            }
        )

    top_themes_rows = []
    for theme, stat in sorted(
        theme_stats.items(),
        key=lambda kv: (len(kv[1]["users"]), kv[1]["projects"]),
        reverse=True,
    ):
        top_themes_rows.append(
            {
                "theme": theme,
                "users_count": len(stat["users"]),
                "projects_count": stat["projects"],
                "typical_actions": ", ".join([k for k, _ in stat["ops"].most_common(3)]),
            }
        )

    top_errors_rows = []
    for category, stat in sorted(
        global_errors.items(),
        key=lambda kv: (kv[1]["events"], len(kv[1]["users"])),
        reverse=True,
    ):
        top_errors_rows.append(
            {
                "error_category": category,
                "events_count": stat["events"],
                "users_count": len(stat["users"]),
                "example_message": " | ".join(stat["examples"][:2]),
            }
        )

    last_errors_rows = []
    for category, count in last_error_counter.most_common():
        last_errors_rows.append({"last_error_category": category, "users_count": count})

    errors_by_level_rows = []
    for level in LEVEL_ORDER:
        level_errors = errors_by_level.get(level, {})
        for category, stat in sorted(
            level_errors.items(),
            key=lambda kv: (kv[1]["events"], len(kv[1]["users"])),
            reverse=True,
        ):
            errors_by_level_rows.append(
                {
                    "level": level,
                    "error_category": category,
                    "events_count": stat["events"],
                    "users_count": len(stat["users"]),
                }
            )

    last_errors_by_level_rows = []
    for level in LEVEL_ORDER:
        for category, count in last_errors_by_level.get(level, Counter()).most_common():
            last_errors_by_level_rows.append(
                {
                    "level": level,
                    "last_error_category": category,
                    "users_count": count,
                }
            )

    errors_by_plan_rows = []
    for plan in ["lite", "pro", "mixed", "unknown"]:
        plan_errors = errors_by_plan.get(plan, {})
        for category, stat in sorted(
            plan_errors.items(),
            key=lambda kv: (kv[1]["events"], len(kv[1]["users"])),
            reverse=True,
        ):
            errors_by_plan_rows.append(
                {
                    "lite_or_pro": plan,
                    "error_category": category,
                    "events_count": stat["events"],
                    "users_count": len(stat["users"]),
                }
            )

    last_errors_by_plan_rows = []
    for plan in ["lite", "pro", "mixed", "unknown"]:
        for category, count in last_errors_by_plan.get(plan, Counter()).most_common():
            last_errors_by_plan_rows.append(
                {
                    "lite_or_pro": plan,
                    "last_error_category": category,
                    "users_count": count,
                }
            )

    per_user_rows.sort(key=lambda r: int(r["projects_count"]), reverse=True)
    per_project_rows.sort(key=lambda r: (r["guid"], int(r["project_number"]) if str(r["project_number"]).isdigit() else -1))

    # Write CSV files.
    def write_csv(path: Path, rows: List[Dict[str, str]]) -> None:
        if not rows:
            path.write_text("", encoding="utf-8")
            return
        with path.open("w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
            writer.writeheader()
            writer.writerows(rows)

    write_csv(OUT_DIR / "dashboard_top_sites.csv", top_sites_rows)
    write_csv(OUT_DIR / "dashboard_top_themes.csv", top_themes_rows)
    write_csv(OUT_DIR / "dashboard_top_errors.csv", top_errors_rows)
    write_csv(OUT_DIR / "dashboard_last_errors.csv", last_errors_rows)
    write_csv(OUT_DIR / "dashboard_errors_by_level.csv", errors_by_level_rows)
    write_csv(OUT_DIR / "dashboard_last_errors_by_level.csv", last_errors_by_level_rows)
    write_csv(OUT_DIR / "dashboard_errors_by_plan.csv", errors_by_plan_rows)
    write_csv(OUT_DIR / "dashboard_last_errors_by_plan.csv", last_errors_by_plan_rows)
    write_csv(OUT_DIR / "users_profile_dashboard.csv", per_user_rows)
    write_csv(OUT_DIR / "projects_detailed_dashboard.csv", per_project_rows)

    # Markdown dashboard.
    users_count = len(per_user_rows)
    projects_count = len(per_project_rows)
    all_project_counts = [int(r["projects_count"]) for r in per_user_rows]
    lite_project_counts = [int(r["projects_count"]) for r in per_user_rows if r.get("lite_or_pro") == "lite"]
    pro_project_counts = [int(r["projects_count"]) for r in per_user_rows if r.get("lite_or_pro") == "pro"]
    avg_projects_all, median_projects_all = mean_and_median(all_project_counts)
    avg_projects_lite, median_projects_lite = mean_and_median(lite_project_counts)
    avg_projects_pro, median_projects_pro = mean_and_median(pro_project_counts)
    active_users = churn_counter["активен_<=1д"]
    left_users = churn_counter["ушел_>1д"]
    lines = []
    lines.append("# ZennoPoster Dashboard (16 Feb - 24 Feb 2026)")
    lines.append("")
    lines.append("## Кратко")
    lines.append(f"- Пользователей (по GUID): **{users_count}**")
    lines.append(f"- Проектов: **{projects_count}**")
    lines.append(
        f"- Проектов на пользователя: **avg {avg_projects_all:.2f} / median {median_projects_all:.2f}**"
    )
    lines.append(
        f"- Lite: users **{len(lite_project_counts)}**, projects/user **avg {avg_projects_lite:.2f} / median {median_projects_lite:.2f}**"
    )
    lines.append(
        f"- Pro: users **{len(pro_project_counts)}**, projects/user **avg {avg_projects_pro:.2f} / median {median_projects_pro:.2f}**"
    )
    lines.append(f"- Разобранных zip-файлов: **{len(project_records)}**")
    lines.append(f"- Ошибок парсинга zip/history: **{parse_failures}**")
    lines.append(f"- Ушли (>1 дня неактивности к 2026-02-24 23:59): **{left_users}**")
    lines.append(f"- Активны в последние 24ч окна: **{active_users}**")
    lines.append("")

    lines.append("## Топ сайтов (пользователи + проекты)")
    lines.append("")
    lines.append("| Сайт | Пользователи | Проекты | Что делают |")
    lines.append("|---|---:|---:|---|")
    for row in top_sites_rows[:25]:
        lines.append(
            f"| {row['domain']} | {row['users_count']} | {row['projects_count']} | {row['what_users_do']} |"
        )
    lines.append("")

    lines.append("## Топ тем")
    lines.append("")
    lines.append("| Тема | Пользователи | Проекты | Типичные действия |")
    lines.append("|---|---:|---:|---|")
    for row in top_themes_rows[:20]:
        lines.append(
            f"| {row['theme']} | {row['users_count']} | {row['projects_count']} | {row['typical_actions']} |"
        )
    lines.append("")

    lines.append("## Топ частых ошибок")
    lines.append("")
    lines.append("| Ошибка | Событий | Пользователи |")
    lines.append("|---|---:|---:|")
    for row in top_errors_rows[:20]:
        lines.append(
            f"| {row['error_category']} | {row['events_count']} | {row['users_count']} |"
        )
    lines.append("")

    lines.append("## Топ последних ошибок пользователей")
    lines.append("")
    lines.append("| Последняя ошибка | Пользователи |")
    lines.append("|---|---:|")
    for row in last_errors_rows[:20]:
        lines.append(f"| {row['last_error_category']} | {row['users_count']} |")
    lines.append("")

    lines.append("## Ошибки по уровням пользователей")
    lines.append("")
    for level in LEVEL_ORDER:
        rows = [r for r in errors_by_level_rows if r["level"] == level][:8]
        if not rows:
            continue
        lines.append(f"### {level}")
        lines.append("")
        lines.append("| Ошибка | Событий | Пользователи |")
        lines.append("|---|---:|---:|")
        for row in rows:
            lines.append(
                f"| {row['error_category']} | {row['events_count']} | {row['users_count']} |"
            )
        lines.append("")

    lines.append("## Ошибки по плану (Lite/Pro)")
    lines.append("")
    for plan in ["lite", "pro", "mixed", "unknown"]:
        rows = [r for r in errors_by_plan_rows if r["lite_or_pro"] == plan][:8]
        if not rows:
            continue
        lines.append(f"### {plan}")
        lines.append("")
        lines.append("| Ошибка | Событий | Пользователи |")
        lines.append("|---|---:|---:|")
        for row in rows:
            lines.append(
                f"| {row['error_category']} | {row['events_count']} | {row['users_count']} |"
            )
        lines.append("")

    lines.append("## Сегменты пользователей")
    lines.append("")
    for level, count in level_distribution.most_common():
        lines.append(f"- {level}: **{count}**")
    lines.append("")

    lines.append("## Выходные файлы")
    lines.append("")
    lines.append(f"- `{OUT_DIR / 'dashboard_top_sites.csv'}`")
    lines.append(f"- `{OUT_DIR / 'dashboard_top_themes.csv'}`")
    lines.append(f"- `{OUT_DIR / 'dashboard_top_errors.csv'}`")
    lines.append(f"- `{OUT_DIR / 'dashboard_last_errors.csv'}`")
    lines.append(f"- `{OUT_DIR / 'dashboard_errors_by_level.csv'}`")
    lines.append(f"- `{OUT_DIR / 'dashboard_last_errors_by_level.csv'}`")
    lines.append(f"- `{OUT_DIR / 'dashboard_errors_by_plan.csv'}`")
    lines.append(f"- `{OUT_DIR / 'dashboard_last_errors_by_plan.csv'}`")
    lines.append(f"- `{OUT_DIR / 'users_profile_dashboard.csv'}`")
    lines.append(f"- `{OUT_DIR / 'projects_detailed_dashboard.csv'}`")
    lines.append(f"- `{OUT_DIR / 'dashboard_report.md'}`")
    lines.append("")

    (OUT_DIR / "dashboard_report.md").write_text("\n".join(lines), encoding="utf-8")

    print(f"Done. Output dir: {OUT_DIR}")
    print(f"Users: {users_count}, Projects: {projects_count}, Domains: {len(top_sites_rows)}")


if __name__ == "__main__":
    analyze()
