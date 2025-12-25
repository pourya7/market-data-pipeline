# Concepts — Market Microstructure

Why microstructure matters
- Trades and quotes at the tick level carry market mechanics (spread, liquidity, order-flow) that affect price formation; understanding microstructure helps make correct choices when cleaning and resampling.

Key ideas
- Trades vs Quotes: trades record executed transactions; quotes record best-bid/ask. Both inform different analytics.
- Spread and mid-price: spread = ask - bid; mid = (ask + bid) / 2. Using mid-price vs last trade depends on the analysis.
- Liquidity and volatility: sparse liquidity leads to large price jumps and stale prices; resampling and gap policies must consider this.

Implications for the pipeline
- Use trade timestamps and quote lifetimes carefully; quoting conventions differ by provider.
- When reconstructing bars from trades, be mindful of outliers and misreported trades (filter by size or exchange).

Practical tips
- Where available, use exchange-level metadata (exchange code) to treat data consistently.
- Consider filtering nanoprice trades or obvious reporting errors before aggregation.
