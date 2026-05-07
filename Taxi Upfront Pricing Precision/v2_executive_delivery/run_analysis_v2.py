"""Runnable, dependency-light upfront pricing precision analysis.

This script uses only the Python standard library so it can run in restricted
execution environments without pandas/numpy/matplotlib.
"""

from __future__ import annotations
import csv
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA_PATH = ROOT / "data" / "raw_data" / "test.csv"
OUT_DIR = Path(__file__).resolve().parent


def to_float(value: str):
    if value is None:
        return None
    value = str(value).strip()
    if value == "":
        return None
    try:
        return float(value)
    except ValueError:
        return None


def load_and_prepare_rows(path: Path):
    cleaned = []
    with path.open("r", encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            if row.get("b_state") != "finished":
                continue

            metered = to_float(row.get("metered_price"))
            upfront = to_float(row.get("upfront_price"))
            if metered is None or upfront is None or upfront <= 0:
                continue

            distance = to_float(row.get("distance"))
            duration = to_float(row.get("duration"))
            pred_distance = to_float(row.get("predicted_distance"))
            pred_duration = to_float(row.get("predicted_duration"))
            gps_conf = to_float(row.get("gps_confidence"))
            dest_change = to_float(row.get("dest_change_number"))
            fraud_score = to_float(row.get("fraud_score"))

            price_difference = metered - upfront
            relative_error = abs(price_difference) / upfront
            is_switched = 1 if relative_error > 0.2 else 0

            distance_bias = None
            if distance is not None and pred_distance not in (None, 0):
                distance_bias = (distance - pred_distance) / pred_distance

            duration_bias = None
            if duration is not None and pred_duration not in (None, 0):
                duration_bias = (duration - pred_duration) / pred_duration

            cleaned.append(
                {
                    "order_id_new": row.get("order_id_new"),
                    "entered_by": row.get("entered_by"),
                    "eu_indicator": row.get("eu_indicator"),
                    "prediction_price_type": row.get("prediction_price_type"),
                    "metered_price": metered,
                    "upfront_price": upfront,
                    "gps_confidence": gps_conf,
                    "dest_change_number": dest_change,
                    "fraud_score": fraud_score,
                    "price_difference": price_difference,
                    "relative_error": relative_error,
                    "is_switched": is_switched,
                    "distance_bias": distance_bias,
                    "duration_bias": duration_bias,
                }
            )
    return cleaned


def mean(values):
    vals = [v for v in values if v is not None]
    return (sum(vals) / len(vals)) if vals else None


def gps_bucket(v):
    if v is None:
        return "missing"
    if v < 0.4:
        return "<0.4"
    if v < 0.6:
        return "0.4-0.6"
    if v < 0.8:
        return "0.6-0.8"
    return ">=0.8"


def fraud_bucket(v):
    if v is None:
        return "missing"
    if v < 0.2:
        return "low"
    if v < 0.5:
        return "mid"
    if v < 0.8:
        return "high"
    return "very_high"


def switch_table(rows, key_fn):
    agg = defaultdict(lambda: {"rides": 0, "sw": 0, "errors": []})
    for r in rows:
        k = key_fn(r)
        agg[k]["rides"] += 1
        agg[k]["sw"] += r["is_switched"]
        agg[k]["errors"].append(r["relative_error"])

    out = []
    for k, v in agg.items():
        out.append((k, v["rides"], v["sw"] / v["rides"], mean(v["errors"])))
    return sorted(out, key=lambda x: x[2], reverse=True)


def write_csv(path: Path, rows, header):
    with path.open("w", encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        w.writerow(header)
        for r in rows:
            w.writerow(r)


def main():
    rows = load_and_prepare_rows(DATA_PATH)
    n = len(rows)
    switched = sum(r["is_switched"] for r in rows)
    switch_rate = switched / n if n else 0

    not_switched = [r for r in rows if r["is_switched"] == 0]
    switched_rows = [r for r in rows if r["is_switched"] == 1]

    summary_lines = [
        f"clean_rides={n}",
        f"switched_rides={switched}",
        f"switch_rate={switch_rate:.6f}",
        f"distance_bias_not_switched={mean([r['distance_bias'] for r in not_switched]):.6f}",
        f"distance_bias_switched={mean([r['distance_bias'] for r in switched_rows]):.6f}",
        f"duration_bias_not_switched={mean([r['duration_bias'] for r in not_switched]):.6f}",
        f"duration_bias_switched={mean([r['duration_bias'] for r in switched_rows]):.6f}",
    ]
    (OUT_DIR / "analysis_summary_v2.txt").write_text("\n".join(summary_lines) + "\n", encoding="utf-8")

    write_csv(
        OUT_DIR / "switch_rate_by_gps_bucket_v2.csv",
        switch_table(rows, lambda r: gps_bucket(r["gps_confidence"])),
        ["gps_bucket", "rides", "switch_rate", "mean_relative_error"],
    )

    write_csv(
        OUT_DIR / "switch_rate_by_eu_indicator_v2.csv",
        switch_table(rows, lambda r: r["eu_indicator"]),
        ["eu_indicator", "rides", "switch_rate", "mean_relative_error"],
    )

    write_csv(
        OUT_DIR / "switch_rate_by_dest_change_v2.csv",
        switch_table(rows, lambda r: "2+" if (r["dest_change_number"] or 0) >= 2 else str(int(r["dest_change_number"] or 0))),
        ["dest_change_number_bucket", "rides", "switch_rate", "mean_relative_error"],
    )

    write_csv(
        OUT_DIR / "switch_rate_by_fraud_bucket_v2.csv",
        switch_table(rows, lambda r: fraud_bucket(r["fraud_score"])),
        ["fraud_bucket", "rides", "switch_rate", "mean_relative_error"],
    )

    print("Analysis complete.")
    print("Output directory:", OUT_DIR)


if __name__ == "__main__":
    main()
