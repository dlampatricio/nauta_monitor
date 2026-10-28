from __future__ import annotations

import os
import random
import statistics
import threading
import time
from dataclasses import dataclass

import requests

DEFAULT_API = "https://api.fast.com"
# Token público que usa el propio cliente JS de fast.com (app-*.js).
DEFAULT_TOKEN = "YXNkZmFzZGxmbnNkYWZoYXNkZmhrYWxm"

_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
    ),
    "Accept": "*/*",
}


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


def _range_size(header: str | None) -> int | None:
    if not header or "/" not in header:
        return None
    total = header.rsplit("/", 1)[-1]
    return int(total) if total.isdigit() else None


class FastClient:
    """Mide latencia y velocidad contra fast.com (Netflix Open Connect).

    Usa los mismos endpoints que el cliente JS de fast.com, sin navegador:
    los targets de descarga salen de `api.fast.com/netflix/speedtest/v2` y los
    de subida de `api.fast.com/oca/speedtest`.
    """

    def __init__(
        self,
        api_url: str = DEFAULT_API,
        token: str = "",
        connections: int = 3,
        max_duration: float = 10.0,
        max_mb: float = 50.0,
        timeout: float = 20.0,
    ):
        self._api = (api_url or DEFAULT_API).rstrip("/")
        self._token = token or DEFAULT_TOKEN
        self._connections = max(1, min(connections, 8))
        self._max_duration = max(max_duration, 3.0)
        self._max_bytes = max(max_mb, 1.0) * 1_000_000
        self._timeout = timeout
        self._session = requests.Session()
        self._session.headers.update(_HEADERS)

    def run(self) -> SpeedResult:
        targets, info, server = self._download_targets()
        result = SpeedResult(ip=info.get("ip"), server=server)
        result.ping_ms, result.jitter_ms, size = self._latency(targets)
        result.download_mbps = self._download(targets, size)
        result.upload_mbps = self._upload(self._upload_targets())
        return result

    def _get_json(self, path: str, url_count: int):
        try:
            response = self._session.get(
                path,
                params={"https": "true", "token": self._token, "urlCount": url_count},
                timeout=self._timeout,
            )
            response.raise_for_status()
            return response.json()
        except (requests.RequestException, ValueError) as exc:
            raise SpeedtestError(
                f"No se pudo contactar con fast.com ({self._api}): {exc}. "
                "Necesitas una conexión a internet activa (sesión Nauta iniciada)."
            ) from exc

    def _download_targets(self) -> tuple[list[str], dict, str]:
        data = self._get_json(f"{self._api}/netflix/speedtest/v2", 5)
        targets = data.get("targets") or []
        urls = [target.get("url") for target in targets if target.get("url")]
        if not urls:
            raise SpeedtestError("fast.com no devolvió servidores de descarga.")
        city = next(
            (
                target["location"]["city"]
                for target in targets
                if target.get("location", {}).get("city")
            ),
            None,
        )
        server = f"fast.com ({city})" if city else "fast.com"
        return urls, data.get("client") or {}, server

    def _upload_targets(self) -> list[str]:
        data = self._get_json(f"{self._api}/oca/speedtest", 3)
        entries = data.get("targets") or [] if isinstance(data, dict) else data
        urls = [
            entry.get("url")
            for entry in entries
            if isinstance(entry, dict) and entry.get("url")
        ]
        if not urls:
            raise SpeedtestError("fast.com no devolvió servidores de subida.")
        return urls

    def _latency(self, targets: list[str]) -> tuple[float | None, float | None, int | None]:
        url = targets[0]
        size: int | None = None
        # Primer request de calentamiento: DNS + TLS no deben contar como jitter.
        try:
            response = self._session.get(
                url, headers={"Range": "bytes=0-0"}, timeout=self._timeout
            )
            response.raise_for_status()
            size = _range_size(response.headers.get("Content-Range"))
        except requests.RequestException:
            pass
        samples: list[float] = []
        for _ in range(5):
            start = time.perf_counter()
            try:
                response = self._session.get(
                    url, headers={"Range": "bytes=0-0"}, timeout=self._timeout
                )
                response.raise_for_status()
                samples.append((time.perf_counter() - start) * 1000)
                size = size or _range_size(response.headers.get("Content-Range"))
            except requests.RequestException:
                continue
        if not samples:
            return None, None, size
        jitter = statistics.stdev(samples) if len(samples) > 1 else 0.0
        return min(samples), jitter, size

    def _download(self, targets: list[str], size: int | None) -> float:
        deadline = time.perf_counter() + self._max_duration
        stop = threading.Event()
        lock = threading.Lock()
        counted = {"bytes": 0}
        samples: list[tuple[int, float]] = []

        def account(chunk_size: int) -> bool:
            with lock:
                if counted["bytes"] >= self._max_bytes:
                    stop.set()
                    return False
                counted["bytes"] += chunk_size
                return True

        def worker(index: int) -> None:
            total = 0
            start_time = time.perf_counter()
            while not stop.is_set() and time.perf_counter() < deadline:
                offset = random.randrange(size) if size and size > 1 else 0
                try:
                    response = self._session.get(
                        targets[index % len(targets)],
                        headers={"Range": f"bytes={offset}-"},
                        stream=True,
                        timeout=self._timeout,
                    )
                    with response:
                        response.raise_for_status()
                        for chunk in response.iter_content(65536):
                            if stop.is_set() or time.perf_counter() >= deadline:
                                break
                            if not account(len(chunk)):
                                break
                            total += len(chunk)
                except requests.RequestException:
                    time.sleep(0.2)
            elapsed = time.perf_counter() - start_time
            if total and elapsed > 0:
                samples.append((total, elapsed))

        threads = [
            threading.Thread(target=worker, args=(index,), daemon=True)
            for index in range(self._connections)
        ]
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join(timeout=self._max_duration + self._timeout)

        if not samples:
            raise SpeedtestError("No se pudo medir la velocidad de descarga.")
        return sum(bytes_ for bytes_, _ in samples) * 8 / 1_000_000 / sum(
            elapsed for _, elapsed in samples
        )

    def _upload(self, targets: list[str]) -> float:
        payload = os.urandom(2 * 1024 * 1024)
        chunk_size = 128 * 1024
        deadline = time.perf_counter() + self._max_duration
        timeout = max(self._timeout, 60.0)
        total = 0
        spent = 0.0
        failures = 0
        while time.perf_counter() < deadline and total < self._max_bytes:
            start = time.perf_counter()
            try:
                response = self._session.post(
                    targets[failures % len(targets)],
                    data=payload[:chunk_size],
                    headers={"Content-Type": "application/octet-stream"},
                    timeout=timeout,
                )
                response.raise_for_status()
            except requests.RequestException:
                failures += 1
                if failures >= 3:
                    break
                continue
            spent += time.perf_counter() - start
            total += chunk_size
            if spent < self._max_duration / 2:
                chunk_size = min(chunk_size * 2, len(payload))
        if not total or not spent:
            raise SpeedtestError("No se pudo medir la velocidad de subida.")
        return total * 8 / 1_000_000 / spent
