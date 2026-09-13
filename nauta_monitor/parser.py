from __future__ import annotations

import re
from dataclasses import dataclass, field
from datetime import datetime

from bs4 import BeautifulSoup

_DATETIME_RE = re.compile(r"(\d{4})/(\d{2})/(\d{2}) (\d{2}):(\d{2}):(\d{2})")


def parse_credit(text: str) -> float | None:
    if not text:
        return None
    match = re.search(r"(\d+(?:[.,]\d+)?)", text)
    if not match:
        return None
    try:
        return float(match.group(1).replace(",", "."))
    except ValueError:
        return None


def parse_datetime(text: str) -> datetime | None:
    if not text:
        return None
    match = _DATETIME_RE.search(text)
    if not match:
        return None
    try:
        return datetime(
            year=int(match.group(1)),
            month=int(match.group(2)),
            day=int(match.group(3)),
            hour=int(match.group(4)),
            minute=int(match.group(5)),
            second=int(match.group(6)),
        )
    except ValueError:
        return None


def parse_duration(text: str) -> int | None:
    if not text:
        return None
    parts = [int(part) for part in text.strip().split(":")]
    if len(parts) == 3:
        hours, minutes, seconds = parts
        return hours * 3600 + minutes * 60 + seconds
    return None


@dataclass
class SessionInfo:
    start: datetime | None
    end: datetime | None
    duration: int | None


@dataclass
class AccountInfo:
    account_status: str | None = None
    credit: float | None = None
    expiration_date: str | None = None
    access_areas: str | None = None
    last_sessions: list[SessionInfo] = field(default_factory=list)


def _normalize_label(label: str) -> str:
    label = label.lower().strip().rstrip(":")
    label = label.replace("\xa0", " ").strip()
    for search, replace in (("á", "a"), ("é", "e"), ("í", "i"), ("ó", "o"), ("ú", "u")):
        label = label.replace(search, replace)
    return " ".join(label.split())


_LABEL_TO_FIELD = {
    "estado de la cuenta": "account_status",
    "credito": "credit",
    "fecha de expiracion": "expiration_date",
    "areas de acceso": "access_areas",
}


def parse_account_info(html: str) -> AccountInfo:
    soup = BeautifulSoup(html, "html5lib")
    result = AccountInfo()

    sessioninfo = soup.select_one("table#sessioninfo")
    if sessioninfo:
        for row in sessioninfo.select("tbody tr"):
            key_td = row.select_one("td.key")
            value_td = row.find_all("td")
            if key_td is None or len(value_td) < 2:
                continue
            key = _normalize_label(key_td.get_text(" ", strip=True))
            value = value_td[1].get_text(" ", strip=True)
            field_name = _LABEL_TO_FIELD.get(key)
            if field_name == "credit":
                result.credit = parse_credit(value)
            elif field_name == "account_status":
                result.account_status = value or None
            elif field_name == "expiration_date":
                result.expiration_date = value or None
            elif field_name == "access_areas":
                result.access_areas = value or None

    traza = soup.select_one("table#sesiontraza tbody")
    if traza:
        for row in traza.select("tr"):
            cells = [cell.get_text(" ", strip=True) for cell in row.select("td")]
            if len(cells) < 3:
                continue
            result.last_sessions.append(
                SessionInfo(
                    start=parse_datetime(cells[0]),
                    end=parse_datetime(cells[1]),
                    duration=parse_duration(cells[2]),
                )
            )
    return result


def find_error(html: str) -> str | None:
    match = re.search(r'alert\("(?P<reason>[^"]*)"\)', html)
    if match:
        return match.group("reason").strip()
    return None