# Taxi Upfront Pricing Precision — Executive Report (V2)

## Executive Summary
Upfront pricing is missing precision too often: **45.8%** of completed rides exceed the 20% error threshold and likely switch from upfront to metered pricing. This creates fare surprise and poor rider trust.  

We identified two high-impact, actionable opportunities:
1. **GPS-confidence-based fallback logic** for low-confidence location cases.  
2. **Bias correction for underpredicted distance/duration** (systematically too low on switched rides).

If executed together, these can materially reduce switches and improve pricing consistency.

## 1) Business Problem & Precision Metric
**Problem in simple terms:** We promise a price before the trip, but if actual metered fare differs by >20%, we replace the promised price. Too many replacements hurt experience and confidence.

**Pricing precision definition:** ability of upfront price to stay within ±20% of metered fare.

**Primary KPI:**
- `switch_rate = % rides with |metered_price - upfront_price| / upfront_price > 0.20`

## 2) Data Preparation Scope
- Source file: `data/raw_data/test.csv`
- Filtered to completed rides (`b_state = finished`).
- Removed rides with missing/invalid prices and `upfront_price <= 0`.
- Engineered:
  - `price_difference = metered_price - upfront_price`
  - `relative_error = |metered_price - upfront_price| / upfront_price`
  - `is_switched = 1(relative_error > 0.2)`

Analysis sample after cleaning: **3,409 rides**.

## 3) Key Insights (EDA + Root Cause)

### Portfolio-level performance
- Switch rate: **45.8%** (1,563 / 3,409).
- Indicates upfront model/rules are underperforming against 20% tolerance.

### Segment patterns
- **Low GPS confidence (<0.4)** has very high switch rate: **69.9%**.
- **High GPS confidence (>=0.8)** is much better: **42.9%**.
- **EU indicator = 0** underperforms EU=1 (56.5% vs 42.1%), suggesting regional calibration gaps.
- Destination changes (`dest_change_number >=2`) are riskier than baseline (~60.3% vs ~45.3%).

### Prediction bias (root cause signal)
Comparing switched vs non-switched rides:
- Switched rides show strong positive bias in actual vs predicted:
  - Mean distance bias: **+42.5%**
  - Mean duration bias: **+61.3%**
- Non-switched rides are near neutral:
  - Mean distance bias: **-2.0%**
  - Mean duration bias: **+3.8%**

Interpretation: a major error mode is **systematic underprediction of trip duration/distance**, not random noise.

## 4) Top Opportunities (Only Top 2)

### Opportunity 1 — GPS-Quality Fallback Pricing
**Problem:** low-confidence GPS trips are disproportionately inaccurate and drive switches.

**Supporting data:** switch rate jumps to **69.9%** when GPS confidence < 0.4.

**Proposed solution:**
- Introduce a rules layer before quote finalization:
  - If `gps_confidence < 0.4`, apply conservative pricing fallback (buffer/uplift band), OR
  - Ask for refreshed pickup pin / route recalc before showing final upfront fare.
- Add real-time quality flag to pricing service.

**Impact estimate:**
- If low-GPS segment (372 rides) switch rate drops from 69.9% to 50%, overall switch rate drops by ~**2.2 pp**.

### Opportunity 2 — Dynamic Bias Correction for Underprediction Risk
**Problem:** switched rides have large underprediction in both duration and distance.

**Supporting data:** switched rides average **+42.5%** distance and **+61.3%** duration bias vs prediction.

**Proposed solution:**
- Train a lightweight calibration model (or quantile correction) to predict expected underestimation risk using:
  - GPS confidence, region (`eu_indicator`), destination change history, entry channel, fraud/risk features, time-of-day.
- Apply dynamic correction factor to quote when underprediction risk is high.
- Start as shadow mode, then gradual rollout by region.

**Impact estimate:**
- Reducing switched rides by 15% in current switched pool would lower overall switch rate by ~**6.9 pp**.

## 5) Business + Technical Recommendations
1. **Deploy risk-based pricing guardrails** (GPS fallback + high-risk uplift) before deeper model retraining.
2. **Build calibration layer** on top of existing model to correct bias fast.
3. **Monitoring dashboard (daily):**
   - Switch rate (overall, by GPS bucket, region, destination-change bucket)
   - Mean signed error and absolute relative error
   - Underprediction share (`metered_price > upfront_price`)
4. **Experimentation:** A/B test fallback and calibration policies with guardrails on conversion, cancellation, and complaint rates.

## 6) Visual Explanations (for presentation)
- **Chart 1:** Histogram of relative error with a vertical 20% threshold line to show how much mass lies above switch boundary.
- **Chart 2:** Bar chart of switch rate by GPS-confidence bucket; highlights low-confidence risk cliff.
- **Chart 3:** Predicted-vs-actual bias comparison (switched vs non-switched) for distance and duration.

---
This V2 package includes an implementation notebook ready for reproducible reruns and extension into production analytics.
