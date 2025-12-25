# Concepts — Storage & Partitioning Rationale

Why partition and use Parquet
- Partitioning organizes data for efficient reads by common query keys (time, symbol). Parquet provides columnar storage with compression and predicate pushdown for efficient analytics.

Partition strategy trade-offs
- Fine-grained partitions (per-day) make reads smaller but increase file count and metadata overhead.
- Coarse partitions (per-month/year) reduce file count but may require scanning large files for small queries.
- Hybrid partitioning (symbol + date) balances per-symbol queries and time-range reads.

Manifest purpose
- A manifest/catalog tracks what files/partitions exist and their time ranges, enabling fast lookup without directory scans.
- Manifests help with idempotent writes and atomic updates: write file, update manifest atomically.

Parquet considerations
- Choose compression (snappy, zstd) and row-group size to balance IO and memory.
- Preserve schema stability across writes to avoid type mismatches.

Why atomic writes and checksums
- Atomic writes prevent consumers from reading partial files. Checksums detect silent corruption and enable validation during reads.
