from __future__ import annotations

import os
import statistics
import threading
import time
from dataclasses import dataclass, field
from datetime import datetime
from urllib.parse import urljoin

import requests


class SpeedtestError(Exception):
    pass


@dataclass
class SpeedResult:
    download_mbps: float | None = None
    upload_mbps: float | None = None
    ping_ms: float | None = None
    jitter_ms: float | None = None
    ip: str | None = None
    server: str = ""
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat(timespec="seconds"))


class LibreSpeedClient:
    def __init__(
        self,
        base_url: str,
        dl_url: str = "garbage.php",
        ul_url: str = "empty.php",
        ping_url: str = "empty.php",
        get_ip_url: str = "getIP.php",
        download_chunks: int = 200,
        upload_kib: int = 1024,
        concurrent: int = 3,
        max_duration: float = 20.0,
        timeout: float = 15.0,
    ):
        self._base = base_url.rstrip("/") + "/"
        self._dl_url = dl_url
        self._ul_url = ul_url
        self._ping_url = ping_url
        self._get_ip_url = get_ip_url
        self._download_chunks = min(max(download_chunks, 1), 1024)
        self._upload_kib = upload_kib
        self._concurrent = max(concurrent, 1)
        self._max_duration = max(max_duration, 3.0)
        self._timeout = timeout
        self._session = requests.Session()

    def run(self) -> SpeedResult:
        result = SpeedResult(server=self._base)
        result.ping_ms, result.jitter_ms = self._latency()
        result.download_mbps = self._measure_download()
        result.upload_mbps = self._measure_upload()
        result.ip = self._get_ip()
        return result

    def _latency(self) -> tuple[float | None, float | None]:
        url = urljoin(self._base, self._ping_url)
        samples = []
        for _ in range(5):
            start = time.perf_counter()
            try:
                self._session.get(url, timeout=self._timeout)
                samples.append((time.perf_counter() - start) * 1000)
            except requests.RequestException:
                continue
        if not samples:
            return None, None
        return min(samples), statistics.stdev(samples) if len(samples) > 1 else 0.0

    def _measure_download(self) -> float | None:
        url = f"{urljoin(self._base, self._dl_url)}?ckSize={self._download_chunks}"
        stop = threading.Event()
        measured: list[tuple[int, float]] = []

        def worker() -> None:
            while not stop.is_set():
                start = time.perf_counter()
                total = 0
                try:
                    response = self._session.get(url, stream=True, timeout=self._timeout)
                    with response:
                        for chunk in response.iter_content(65536):
                            if stop.is_set():
                                break
                            total += len(chunk)
                            if time.perf_counter() - start >= 5.0:
                                break
                except requests.RequestException:
                    stop.set()
                    return
                elapsed = time.perf_counter() - start
                if total and elapsed > 0:
                    measured.append((total, elapsed))

        threads = [threading.Thread(target=worker, daemon=True) for _ in range(self._concurrent)]
        start = time.perf_counter()
        for thread in threads:
            thread.start()
        while time.perf_counter() - start < self._max_duration:
            time.sleep(0.05)
        stop.set()
        for thread in threads:
            thread.join(timeout=1.0)
        if not measured:
            raise SpeedtestError("No se pudo medir la velocidad de descarga.")
        total_bytes = sum(bytes_ for bytes_, _ in measured)
        total_time = sum(elapsed for _, elapsed in measured)
        return (total_bytes * 8) / 1_000_000 / total_time

    def _measure_upload(self) -> float | None:
        url = urljoin(self._base, self._ul_url)
        payload = os.urandom(self._upload_kib * 1024)
        stop = threading.Event()
        measured: list[tuple[int, float]] = []

        def worker() -> None:
            while not stop.is_set():
                start = time.perf_counter()
                try:
                    response = self._session.post(url, data=payload, timeout=self._timeout)
                    if not response.ok:
                        raise requests.RequestException(f"HTTP {response.status_code}")
                except requests.RequestException:
                    stop.set()
                    return
                elapsed = time.perf_counter() - start
                if elapsed > 0:
                    measured.append((len(payload), elapsed))

        threads = [threading.Thread(target=worker, daemon=True) for _ in range(self._concurrent)]
        start = time.perf_counter()
        for thread in threads:
            thread.start()
        while time.perf_counter() - start < self._max_duration:
            time.sleep(0.05)
        stop.set()
        for thread in threads:
            thread.join(timeout=1.0)
        if not measured:
            raise SpeedtestError("No se pudo medir la velocidad de subida.")
        total_bytes = sum(bytes_ for bytes_, _ in measured)
        total_time = sum(elapsed for _, elapsed in measured)
        return (total_bytes * 8) / 1_000_000 / total_time

    def _get_ip(self) -> str | None:
        url = urljoin(self._base, self._get_ip_url)
        try:
            response = self._session.get(url, timeout=self._timeout)
            text = response.text.strip()
            return text or None
        except requests.RequestException:
            return None