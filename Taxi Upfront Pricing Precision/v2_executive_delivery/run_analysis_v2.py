from __future__ import annotations
import csv
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA_PATH = ROOT / "data" / "raw_data" / "test.csv"
OUT_DIR = Path(__file__).resolve().parent


def to_float(v):
    try:
        return float(str(v).strip())
    except Exception:
        return None


def mean(values):
    vals = [v for v in values if v is not None]
    return sum(vals) / len(vals) if vals else None


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


def load_rows(path: Path):
    cleaned = []
    with path.open("r", encoding="utf-8", newline="") as f:
        for row in csv.DictReader(f):
            if row.get("b_state") != "finished":
                continue
            metered = to_float(row.get("metered_price"))
            upfront = to_float(row.get("upfront_price"))
            if metered is None or upfront is None or upfront <= 0:
                continue
            distance, duration = to_float(row.get("distance")), to_float(row.get("duration"))
            pdist, pdur = to_float(row.get("predicted_distance")), to_float(row.get("predicted_duration"))
            rel_error = abs(metered - upfront) / upfront
            cleaned.append({
                "eu_indicator": row.get("eu_indicator"),
                "entered_by": row.get("entered_by"),
                "prediction_price_type": row.get("prediction_price_type"),
                "dest_change_number": to_float(row.get("dest_change_number")),
                "gps_confidence": to_float(row.get("gps_confidence")),
                "fraud_score": to_float(row.get("fraud_score")),
                "price_difference": metered - upfront,
                "relative_error": rel_error,
                "is_switched": 1 if rel_error > 0.2 else 0,
                "distance_bias": (distance - pdist) / pdist if distance is not None and pdist not in (None, 0) else None,
                "duration_bias": (duration - pdur) / pdur if duration is not None and pdur not in (None, 0) else None,
            })
    return cleaned


def switch_table(rows, key_fn):
    agg = defaultdict(lambda: [0, 0, []])
    for r in rows:
        k = key_fn(r)
        agg[k][0] += 1
        agg[k][1] += r["is_switched"]
        agg[k][2].append(r["relative_error"])
    out = []
    for k, (rides, sw, errs) in agg.items():
        out.append((k, rides, sw / rides, mean(errs)))
    return sorted(out, key=lambda x: x[2], reverse=True)


def write_csv(path: Path, rows, headers):
    with path.open("w", encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        w.writerow(headers)
        w.writerows(rows)


def write_bar_svg(path: Path, title: str, rows):
    width, height = 980, 540
    ml, mr, mt, mb = 90, 30, 70, 120
    plot_w, plot_h = width - ml - mr, height - mt - mb
    max_y = max([r[2] for r in rows] + [0.01])
    n = max(len(rows), 1)
    bw = plot_w / n * 0.72

    parts = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}">', '<rect width="100%" height="100%" fill="white"/>']
    parts.append(f'<text x="{width/2}" y="34" text-anchor="middle" font-size="24" font-weight="bold">{title}</text>')
    for t in range(6):
        v = max_y * t / 5
        y = mt + plot_h - (v / max_y) * plot_h
        parts.append(f'<line x1="{ml}" y1="{y:.1f}" x2="{width-mr}" y2="{y:.1f}" stroke="#EAECEE"/>')
        parts.append(f'<text x="{ml-10}" y="{y+4:.1f}" text-anchor="end" font-size="11">{v*100:.0f}%</text>')
    parts.append(f'<line x1="{ml}" y1="{mt}" x2="{ml}" y2="{mt+plot_h}" stroke="#34495E"/>')
    parts.append(f'<line x1="{ml}" y1="{mt+plot_h}" x2="{width-mr}" y2="{mt+plot_h}" stroke="#34495E"/>')

    for i, (name, rides, val, _) in enumerate(rows):
        x = ml + (i + 0.14) * (plot_w / n)
        h = (val / max_y) * plot_h
        y = mt + plot_h - h
        parts.append(f'<rect x="{x:.1f}" y="{y:.1f}" width="{bw:.1f}" height="{h:.1f}" fill="#2E86DE"/>')
        parts.append(f'<text x="{x+bw/2:.1f}" y="{mt+plot_h+20}" text-anchor="middle" font-size="12">{name}</text>')
        parts.append(f'<text x="{x+bw/2:.1f}" y="{y-8:.1f}" text-anchor="middle" font-size="11">{val*100:.1f}%</text>')
        parts.append(f'<text x="{x+bw/2:.1f}" y="{mt+plot_h+38}" text-anchor="middle" font-size="10" fill="#566573">n={rides}</text>')
    parts.append('</svg>')
    path.write_text("\n".join(parts), encoding="utf-8")


def main():
    rows = load_rows(DATA_PATH)
    n = len(rows)
    switched = sum(r["is_switched"] for r in rows)
    switch_rate = switched / n if n else 0
    non_switched = [r for r in rows if r["is_switched"] == 0]
    switched_rows = [r for r in rows if r["is_switched"] == 1]

    summary = [
        f"clean_rides={n}",
        f"switched_rides={switched}",
        f"switch_rate={switch_rate:.6f}",
        f"distance_bias_not_switched={mean([r['distance_bias'] for r in non_switched]):.6f}",
        f"distance_bias_switched={mean([r['distance_bias'] for r in switched_rows]):.6f}",
        f"duration_bias_not_switched={mean([r['duration_bias'] for r in non_switched]):.6f}",
        f"duration_bias_switched={mean([r['duration_bias'] for r in switched_rows]):.6f}",
    ]
    (OUT_DIR / "analysis_summary_v2.txt").write_text("\n".join(summary) + "\n", encoding="utf-8")

    gps = switch_table(rows, lambda r: gps_bucket(r["gps_confidence"]))
    eu = switch_table(rows, lambda r: r["eu_indicator"])
    dest = switch_table(rows, lambda r: "2+" if (r["dest_change_number"] or 0) >= 2 else str(int(r["dest_change_number"] or 0)))
    fraud = switch_table(rows, lambda r: fraud_bucket(r["fraud_score"]))

    write_csv(OUT_DIR / "switch_rate_by_gps_bucket_v2.csv", gps, ["gps_bucket", "rides", "switch_rate", "mean_relative_error"])
    write_csv(OUT_DIR / "switch_rate_by_eu_indicator_v2.csv", eu, ["eu_indicator", "rides", "switch_rate", "mean_relative_error"])
    write_csv(OUT_DIR / "switch_rate_by_dest_change_v2.csv", dest, ["dest_change_number_bucket", "rides", "switch_rate", "mean_relative_error"])
    write_csv(OUT_DIR / "switch_rate_by_fraud_bucket_v2.csv", fraud, ["fraud_bucket", "rides", "switch_rate", "mean_relative_error"])

    fig_dir = OUT_DIR / "figures_v2"
    fig_dir.mkdir(exist_ok=True)
    write_bar_svg(fig_dir / "switch_rate_gps.svg", "Switch Rate by GPS Confidence", gps)
    write_bar_svg(fig_dir / "switch_rate_eu.svg", "Switch Rate by EU Indicator", eu)
    write_bar_svg(fig_dir / "switch_rate_dest.svg", "Switch Rate by Destination Changes", dest)
    write_bar_svg(fig_dir / "switch_rate_fraud.svg", "Switch Rate by Fraud Score Bucket", fraud)

    print("Analysis complete")


if __name__ == "__main__":
    main()
