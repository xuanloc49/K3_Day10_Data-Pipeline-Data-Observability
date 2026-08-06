# Phase 1 Data Pipeline Report

## Source Summary
```json
{
  "total_raw_records": 24,
  "clean_records": 24,
  "source_api": "Crossref REST API",
  "query": "agentic retrieval augmented generation large language model"
}
```

## Metrics
```json
{
  "samples": 10,
  "retrieval_hit_rate": 1.0,
  "mean_token_f1": 1.0,
  "judge_accuracy": 1.0,
  "mean_judge_score": 5,
  "ragas": {
    "skipped": "Set RUN_RAGAS=1 to enable the slower Ragas pass."
  }
}
```

## Data Quality
```json
{
  "row_count": 24,
  "paper_id_valid": true,
  "title_valid": true,
  "summary_valid": true,
  "freshness_valid": true,
  "passed": true
}
```

## Freshness
```json
{
  "latest_published": "2026-08-01",
  "oldest_published": "2026-02-12",
  "stale_rows": 0,
  "total_rows": 24,
  "is_fresh": true
}
```
