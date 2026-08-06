from __future__ import annotations

from typing import Any


def generate_phase1_report(
    report_path,
    source_summary: dict[str, Any],
    metrics: dict[str, Any],
    quality: dict[str, Any],
    freshness: dict[str, Any],
) -> None:
    """TODO(student): viet markdown report cho baseline phase.

    Pseudo-code:
    1. Gom source summary.
    2. In metrics retrieval/evaluation.
    3. In data quality va freshness.
    4. Ghi markdown vao report_path.
    """
    import json
    from pathlib import Path
    
    md_content = f"""# Phase 1 Data Pipeline Report

## Source Summary
```json
{json.dumps(source_summary, indent=2)}
```

## Metrics
```json
{json.dumps(metrics, indent=2)}
```

## Data Quality
```json
{json.dumps(quality, indent=2)}
```

## Freshness
```json
{json.dumps(freshness, indent=2)}
```
"""
    path = Path(report_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(md_content)


def generate_corruption_report(
    report_path,
    baseline_metrics: dict[str, Any],
    corrupted_metrics: dict[str, Any],
    repaired_metrics: dict[str, Any],
    corrupted_quality: dict[str, Any],
    repaired_quality: dict[str, Any],
    corrupted_freshness: dict[str, Any],
    repaired_freshness: dict[str, Any],
) -> None:
    """TODO(student): viet markdown report so sanh baseline/corrupted/repaired."""
    import json
    from pathlib import Path
    
    md_content = f"""# Corruption and Repair Comparison Report

## Evaluation Metrics Comparison
- **Baseline**:
```json
{json.dumps(baseline_metrics, indent=2)}
```
- **Corrupted**:
```json
{json.dumps(corrupted_metrics, indent=2)}
```
- **Repaired**:
```json
{json.dumps(repaired_metrics, indent=2)}
```

## Data Quality Comparison
- **Corrupted**:
```json
{json.dumps(corrupted_quality, indent=2)}
```
- **Repaired**:
```json
{json.dumps(repaired_quality, indent=2)}
```

## Freshness Comparison
- **Corrupted**:
```json
{json.dumps(corrupted_freshness, indent=2)}
```
- **Repaired**:
```json
{json.dumps(repaired_freshness, indent=2)}
```
"""
    path = Path(report_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(md_content)
