import argparse
import json
import statistics
import time
import urllib.error
import urllib.request
from concurrent.futures import ThreadPoolExecutor


def percentile(values, p):
    if not values:
        return None
    values = sorted(values)
    idx = int(p * (len(values) - 1))
    return values[idx]


def get_json(url, timeout=5):
    with urllib.request.urlopen(url, timeout=timeout) as resp:
        return json.loads(resp.read().decode())


def run_seq_get(base_url, count=120):
    lat = []
    errors = 0
    for _ in range(count):
        start = time.perf_counter()
        try:
            with urllib.request.urlopen(base_url + "/api/state", timeout=5) as resp:
                resp.read()
        except Exception:
            errors += 1
        lat.append((time.perf_counter() - start) * 1000)
    p95 = percentile(lat, 0.95) or 0.0
    return {
        "test": "GET /api/state seq",
        "count": count,
        "errors": errors,
        "avg_ms": round(statistics.mean(lat), 2),
        "p50_ms": round(statistics.median(lat), 2),
        "p95_ms": round(p95, 2),
        "min_ms": round(min(lat), 2),
        "max_ms": round(max(lat), 2),
    }


def run_seq_post(base_url, count=80):
    lat = []
    errors = 0
    for i in range(count):
        start = time.perf_counter()
        try:
            payload = json.dumps({"move": f"e2e4_{i}"}).encode()
            req = urllib.request.Request(
                base_url + "/move",
                data=payload,
                headers={"Content-Type": "application/json"},
                method="POST",
            )
            with urllib.request.urlopen(req, timeout=5) as resp:
                resp.read()
        except Exception:
            errors += 1
        lat.append((time.perf_counter() - start) * 1000)
    p95 = percentile(lat, 0.95) or 0.0
    return {
        "test": "POST /move seq",
        "count": count,
        "errors": errors,
        "avg_ms": round(statistics.mean(lat), 2),
        "p50_ms": round(statistics.median(lat), 2),
        "p95_ms": round(p95, 2),
        "min_ms": round(min(lat), 2),
        "max_ms": round(max(lat), 2),
    }


def run_burst_get(base_url, total=120, workers=8):
    def hit(_):
        start = time.perf_counter()
        ok = True
        try:
            with urllib.request.urlopen(base_url + "/api/state", timeout=6) as resp:
                resp.read()
        except Exception:
            ok = False
        return ok, (time.perf_counter() - start) * 1000

    lat = []
    errors = 0
    with ThreadPoolExecutor(max_workers=workers) as executor:
        for ok, ms in executor.map(hit, range(total)):
            lat.append(ms)
            if not ok:
                errors += 1

    p95 = percentile(lat, 0.95) or 0.0
    return {
        "test": "GET /api/state burst",
        "workers": workers,
        "count": total,
        "errors": errors,
        "avg_ms": round(statistics.mean(lat), 2),
        "p50_ms": round(statistics.median(lat), 2),
        "p95_ms": round(p95, 2),
        "min_ms": round(min(lat), 2),
        "max_ms": round(max(lat), 2),
    }


def run_mem_sample(base_url, count=80):
    samples = []
    errors = 0
    for _ in range(count):
        try:
            data = get_json(base_url + "/api/state", timeout=5)
            if "mem_free" in data:
                samples.append(int(data["mem_free"]))
        except Exception:
            errors += 1
        time.sleep(0.02)

    if not samples:
        return {
            "test": "mem_free sample",
            "samples": 0,
            "errors": errors,
        }

    return {
        "test": "mem_free sample",
        "samples": len(samples),
        "errors": errors,
        "mem_avg": int(sum(samples) / len(samples)),
        "mem_min": min(samples),
        "mem_max": max(samples),
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--base-url", default="http://192.168.4.1")
    parser.add_argument("--server", required=True)
    args = parser.parse_args()

    results = [
        run_seq_get(args.base_url),
        run_seq_post(args.base_url),
        run_burst_get(args.base_url),
        run_mem_sample(args.base_url),
    ]

    print(json.dumps({"server": args.server, "results": results}, ensure_ascii=False))


if __name__ == "__main__":
    main()
