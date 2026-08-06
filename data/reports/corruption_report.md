# Corruption and Repair Comparison Report

## Evaluation Metrics Comparison
- **Baseline**:
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
- **Corrupted**:
```json
{
  "samples": 10,
  "retrieval_hit_rate": 0.8,
  "mean_token_f1": 0.7,
  "judge_accuracy": 0.7,
  "mean_judge_score": 3.8,
  "ragas": {
    "skipped": "Set RUN_RAGAS=1 to enable the slower Ragas pass."
  }
}
```
- **Repaired**:
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

## Data Quality Comparison
- **Corrupted**:
```json
{
  "row_count": 23,
  "paper_id_valid": false,
  "title_valid": true,
  "summary_valid": false,
  "freshness_valid": false,
  "passed": false
}
```
- **Repaired**:
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

## Freshness Comparison
- **Corrupted**:
```json
{
  "latest_published": "2026-07-13",
  "oldest_published": "2000-01-01",
  "stale_rows": 1,
  "total_rows": 23,
  "is_fresh": false
}
```
- **Repaired**:
```json
{
  "latest_published": "2026-08-01",
  "oldest_published": "2026-02-12",
  "stale_rows": 0,
  "total_rows": 24,
  "is_fresh": true
}
```
