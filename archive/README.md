# Original notebooks

The five notebooks exactly as they were exported from Truveta Studio, before the
reorganisation described in [`../docs/cleanup-notes.md`](../docs/cleanup-notes.md).

They are kept unmodified so the analytic history stays auditable and so anyone
can diff the cleaned notebooks against what actually produced the results.

**Do not run these.** Use [`../notebooks/`](../notebooks/) instead.

| File | Became |
|---|---|
| `test_group_heilbrunn_analysis.ipynb` | `notebooks/01_cohort_exposed.ipynb` |
| `control_group_heilbrunn_analysis.ipynb` | `notebooks/02_cohort_control.ipynb` |
| `drug_use_metrics_heilbrunn_analysis.ipynb` | `notebooks/03_drug_episodes.ipynb` |
| `not2d_drug_use_metrics_heilbrunn_analysis.ipynb` | `notebooks/04_drug_episodes_no_prior_t2d.ipynb` |
| `run_analysis.ipynb` | `notebooks/05_matched_analysis.ipynb` |

The one filename change: `test_group_heilbrunn_analysis (1).ipynb` lost its
` (1)` suffix. Contents are byte-identical.
