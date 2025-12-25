# Concepts — Feature Engineering Principles

Why thoughtful features
- Features (indicators) summarize historical behavior; poorly designed features introduce lookahead bias, misalignment, or unstable signals.

Key principles
- Alignment: features should be aligned to the bar close (no future data).
- Warm-up period: many indicators need history; mark or drop initial rows until the indicator is stable.
- Determinism: feature computation should be deterministic and testable given the same inputs.
- Reuse and caching: compute shared intermediate values once (e.g., rolling sums) when deriving multiple features.

Common pitfalls
- Lookahead bias: using future values leaks information and invalidates backtests.
- Not handling NaNs: features on sparse data can produce NaNs—decide whether to forward-fill, drop, or mark.

Practical patterns
- Use vectorized pandas operations and avoid per-row Python loops.
- Provide feature metadata (required history, warm-up length) so pipelines can trim appropriately.
