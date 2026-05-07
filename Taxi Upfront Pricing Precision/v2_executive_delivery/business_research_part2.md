# Business Research — Part 2 (Execution Plan)

## Objective
Reduce pricing switches (relative error >20%) while protecting conversion and trust.

## Prioritized experiments
1. **GPS fallback policy**: if `gps_confidence < 0.4`, apply robust quote policy (re-pin prompt or conservative buffer).
2. **Underprediction correction**: apply dynamic uplift where duration/distance underprediction risk is high.

## Experiment design
- **Design**: 3-arm A/B/n test for 2–4 weeks.
  - Control: current upfront logic.
  - Treatment A: GPS fallback.
  - Treatment B: GPS fallback + dynamic uplift.
- **Primary KPI**: switch rate.
- **Guardrails**: quote acceptance, cancellation, rider complaints, gross margin.
- **Segmentation**: region (`eu_indicator`), GPS bucket, destination-change bucket.

## Measurement framework
- Daily monitoring by segment and city.
- Trigger rollback if complaint rate worsens by >10% relative or conversion drops >2pp.
- Success criteria: >=5pp absolute switch-rate reduction with neutral guardrails.

## Rollout plan
- Week 1: shadow scoring + backtesting.
- Week 2–3: 10% traffic pilot in highest-risk segments.
- Week 4+: scale to 50% then 100% if KPI passes.

## Operational recommendations
- Add pricing quality dashboard to the ops review cadence.
- Enforce weekly recalibration of uplift factors from fresh telemetry.
- Add alerting for sudden GPS confidence degradation and route-change spikes.
