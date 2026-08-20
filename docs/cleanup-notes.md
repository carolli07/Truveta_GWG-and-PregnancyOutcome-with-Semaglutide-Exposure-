# Cleanup notes

How the notebooks in `notebooks/` differ from the originals, which are preserved
byte-for-byte in `archive/original_notebooks/`.

**The analysis is unchanged.** Every derivation, threshold, code set, model
specification and output filename is the same. What changed is organisation,
naming and documentation. The two exceptions that touch behaviour are listed
under "Substantive fixes" and both were needed to make the notebooks run
top-to-bottom.

## File mapping

| Original | Cleaned |
|---|---|
| `test_group_heilbrunn_analysis (1).ipynb` | `notebooks/01_cohort_exposed.ipynb` |
| `control_group_heilbrunn_analysis.ipynb` | `notebooks/02_cohort_control.ipynb` |
| `drug_use_metrics_heilbrunn_analysis.ipynb` | `notebooks/03_drug_episodes.ipynb` |
| `not2d_drug_use_metrics_heilbrunn_analysis.ipynb` | `notebooks/04_drug_episodes_no_prior_t2d.ipynb` |
| `run_analysis.ipynb` | `notebooks/05_matched_analysis.ipynb` |

## Structural changes

* **Header on every notebook** stating what it does, what it reads, what it
  writes, and where it sits in the run order.
* **A single CONFIG cell** near the top of each notebook holds every population
  title, code set URL, ICD-10 code list, date cutoff, window width, threshold
  and input/output filename. These were previously scattered as literals
  throughout the notebooks — the 60-day treatment gap, for example, appeared in
  five separate places.
* **Numbered sections with markdown explanations** of what each step does and
  why, replacing bare code runs.
* **Superseded code moved to an "Appendix"** at the end of each notebook,
  commented out and labelled. Previously these were interleaved with live code
  under headings like `Don't Run`, which made the actual pipeline hard to
  follow. Nothing was deleted.
* **Exploratory one-liners consolidated.** Repeated `.head()`, `.shape` and
  `.value_counts()` cells were folded into the step they belong to as labelled
  print statements, so cohort attrition is legible as you scroll.
* **Repeated blocks turned into loops or small functions** where the repetition
  was mechanical: the seven `mark_condition_in_pregnancy` calls, the five
  `condition_before_pregnancy` calls, the three `closest_bmi` derivations, the
  two `accumulated_persistence` calculations, the twelve `load_condition_data`
  calls, and the three concept-decode merges on the weights table.
* **Chinese-language comments in `run_analysis.ipynb` translated to English.**
* **`src/truveta_helpers.py` added** as a single documented reference copy of
  the helper functions that every notebook duplicates. The notebooks still carry
  their own inline copies so each can be uploaded and run alone.
* **`docs/variables.md` added** — data dictionary for the cohort files.

## Substantive fixes

Two changes affect execution. Both are corrections to inconsistencies that made
the original notebooks fail if run from a clean kernel.

1. **The unnamed LMP column.** In `test_group_heilbrunn_analysis (1).ipynb` the
   estimated LMP was assigned to a column named `""` (an empty string), then
   referred to inconsistently as `""`, `lmp_date` and `estimated_LMP` in
   different cells — so a clean run raised `KeyError` at the first
   `mark_condition_in_pregnancy` call. It is now `estimated_LMP` throughout,
   matching the control notebook, which computes the identical quantity under
   that name.

2. **`obstetric_care` naming in the control cohort.** Notebook 02 wrote
   `Obstetriccare` while notebook 05 expected `obstetric_care`. Notebook 02 now
   writes `obstetric_care` and keeps `Obstetriccare` as an alias column, and
   notebook 05 accepts either name. The values are unchanged. Note this does
   *not* resolve the definition difference between arms — see the README.

## Smaller corrections

* `test_df["preg_related_htn"]` was assigned from columns of the parent `test`
  frame, relying on index alignment between a frame and its own subset. Now
  computed from `test_df`'s own columns. Same values.
* In notebook 05 the GWG categorisation is computed in memory on every run
  rather than depending on it having been written back into `test_t3.csv` by an
  earlier session. The write-back is preserved but commented out, since it is
  no longer required for the notebook to work.
* The duplicate derivation of `t2d_before_pregnancy` / `hyper_before_pregnancy`
  against the legacy `estimated_conception_date` was moved to the appendix. It
  was overwritten a few cells later by the `estimated_LMP` version, so it never
  affected results.
* The legacy three-group regression section at the end of the control notebook
  read `delivery_df_t3.csv`, a filename no notebook produces. The appendix copy
  points at `test_t3.csv` and says so.

## Things deliberately left alone

* `drugexporsure.csv` keeps its misspelling — notebook 05 reads that exact name.
* `preTreatmentBMI` still anchors on the delivery date.
* `applymap` is still used in the GWG post-hoc residual flags rather than the
  newer `DataFrame.map`, to stay compatible with older pandas in the Truveta
  image.
* Both `adjusted_summary_all.csv` and `unadjusted_summary_all.csv` are still
  written from the minimally adjusted models. A markdown note in notebook 05
  explains which file holds what.
* The bariatric-surgery arm is still built in notebook 01 even though the
  matched analysis does not use it.
