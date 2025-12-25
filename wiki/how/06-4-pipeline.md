# Cleaning — Pipeline

Purpose
- Orchestrate schema validation, adjustments, and gap handling to produce a cleaned, canonical DataFrame ready for resampling.

Ordering and rationale
- Step 1: Schema coercion and validation — ensure timestamps are correct and types are normalized.
- Step 2: Apply `adjuster` — scale raw prices/volumes for corporate actions so aggregation is correct.
- Step 3: Gap detection/handling — detect and optionally fill or mark gaps now that timestamps and prices are consistent.
- Step 4: Final checks and metadata — add columns or flags (e.g., `is_gap`, `is_adjusted`) and return the cleaned frame.

Idempotency
- The pipeline should be safe to run multiple times on the same input (avoid double-applying adjustments or re-filling already handled gaps). Use idempotent operations or track a `cleaning_version`/flags in metadata.

Configuration
- Pipeline behaviour is driven by config: whether to adjust, gap-fill thresholds, warming/trimming policy, and output columns.

Example (conceptual)

```python
class CleaningPipeline:
    def __init__(self, config):
        self.config = config

    def run(self, raw_df, symbol):
        df = coerce_and_validate(raw_df)
        if self.config.apply_adjustments:
            df = adjust_prices(df, symbol)
        df = handle_gaps(df, self.config.gap_policy)
        df = trim_warmup(df, self.config.warmup)
        return df
```

Integration with resampling
- Run the cleaning pipeline before resampling so resamplers receive monotonic, adjusted timestamps and correct price/volume values.
- If resampling from tick/trade-level, prefer applying adjustments at trade-level and then aggregating.

Observability
- Emit logs/metrics: counts of dropped rows, number of gaps found, adjustments applied. This helps monitor data quality during backfills.

Testing
- `tests/test_pipeline.py` demonstrates expected end-to-end behaviour for synthetic raw inputs.

See also
- `src/market_data/cleaning/pipeline.py` for the orchestration code used by the project.
