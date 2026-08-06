from __future__ import annotations

from typing import Any

import pandas as pd

from core.config import Settings


def run_data_quality_checks(df: pd.DataFrame, settings: Settings, report_name: str) -> dict[str, Any]:
    """TODO(student): tao bo data quality checks.

    Pseudo-code:
    1. Check row count.
    2. Check `paper_id` not null va unique.
    3. Check `title` not null.
    4. Check do dai `summary`.
    5. Check freshness bang `age_days`.
    6. Ghi ket qua vao `data/quality/`.
    """
    row_count = len(df)
    
    paper_id_valid = bool(df['paper_id'].notna().all() and df['paper_id'].is_unique) if 'paper_id' in df.columns else False
    title_valid = bool(df['title'].notna().all()) if 'title' in df.columns else False
    summary_valid = bool((df['summary'].fillna('').str.len() > 10).all()) if 'summary' in df.columns else False
    freshness_valid = bool((df['age_days'] <= settings.freshness_threshold_days).all()) if 'age_days' in df.columns else False
    
    results = {
        "row_count": row_count,
        "paper_id_valid": paper_id_valid,
        "title_valid": title_valid,
        "summary_valid": summary_valid,
        "freshness_valid": freshness_valid,
        "passed": bool(row_count > 0 and paper_id_valid and title_valid and summary_valid and freshness_valid)
    }
    
    import json
    settings.paths.quality_dir.mkdir(parents=True, exist_ok=True)
    report_path = settings.paths.quality_dir / f"{report_name}.json"
    with open(report_path, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)
        
    return results


def build_freshness_report(df: pd.DataFrame, settings: Settings, report_path) -> dict[str, Any]:
    """TODO(student): tong hop freshness report.

    Pseudo-code:
    1. Tim latest va oldest published date.
    2. Dem so dong stale.
    3. Tao payload:
       - latest_published
       - oldest_published
       - stale_rows
       - total_rows
       - is_fresh
    4. Ghi JSON report.
    """
    latest_published = str(df['published'].max()) if 'published' in df.columns else None
    oldest_published = str(df['published'].min()) if 'published' in df.columns else None
    stale_rows = int((df['age_days'] > settings.freshness_threshold_days).sum()) if 'age_days' in df.columns else 0
    total_rows = len(df)
    is_fresh = stale_rows == 0
    
    payload = {
        "latest_published": latest_published,
        "oldest_published": oldest_published,
        "stale_rows": stale_rows,
        "total_rows": total_rows,
        "is_fresh": is_fresh
    }
    
    import json
    from pathlib import Path
    
    path = Path(report_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2)
        
    return payload
