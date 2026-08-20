# Data dictionary

Columns in the cohort files written by the notebooks. All files live in the
Truveta study output path (`study.get_output_path(fs=True)`), one row per person
unless noted.

Legend for **Where**: **E** = exposed cohort (`test_t3.csv`, notebook 01),
**C** = control cohort (`control_t1.csv`, notebook 02),
**D** = drug exposure file (`drugexporsure.csv`, notebook 03).

---

## Identifiers and dates

| Variable | Where | Type | Definition |
|---|---|---|---|
| `PersonId` | E C D | str | Truveta person identifier |
| `delivery_date` | E C | date | Index delivery date |
| `estimated_LMP` | E C | date | Estimated last menstrual period, back-calculated from the pregnancy Z-code closest to delivery |
| `event_date` | E | date | Exposure date — first bariatric surgery or first semaglutide dispense |
| `zcodetime` | E C | date | Date of the Z-code encounter used to derive `estimated_LMP` |
| `zcode` | E C | str | The Z-code description used |
| `gestational_week_zcode` | E C | float | Weeks of gestation stated by that Z-code |
| `source_type` | E | str | `med`, `med_wo_t2d` or `surgery` — which exposure preceded the delivery |

## Gestational age

| Variable | Where | Type | Definition |
|---|---|---|---|
| `gestational_week` | E C | float | Gestational age at delivery in weeks; cohort restricted to 24–42 |
| `gestational_age_days_at_delivery` | E C | int | Same quantity in days |
| `preterm` | E C | 0/1 | `gestational_week < 37` |
| `zcode_count` | E C | int | Number of qualifying pregnancy Z-code encounters — proxy for prenatal-care engagement / data density |

## Weight and BMI

| Variable | Where | Type | Definition |
|---|---|---|---|
| `prepreg_weight` | E C | kg | Weight closest to `estimated_LMP` within ±12 weeks |
| `predelivery_weight` | E C | kg | Weight closest to delivery within the preceding 4 weeks |
| `pretreatment_weight` | E | kg | Weight closest to `event_date` within the preceding 183 days |
| `has_prepreg_weight`, `has_predelivery_weight`, `has_both_weights` | E C | bool | Availability flags; the cohort keeps `has_both_weights == True` |
| `gestation_weight` | E C | kg | **Gestational weight gain** = `predelivery_weight − prepreg_weight` |
| `weight_loss` | E | kg | `pretreatment_weight − prepreg_weight` — weight change between treatment start and conception |
| `PrePregnancyBMI` | E C | float | BMI measurement closest to `estimated_LMP` |
| `nearDeliveryBMI` | E C | float | BMI measurement closest to `delivery_date` |
| `preTreatmentBMI` | E | float | BMI closest to `delivery_date` (see caveat in the README — anchored on delivery, not on `event_date`) |
| `bmi_category` | E C | str | `Underweight` / `Normal weight` / `Overweight` / `Obese` (WHO cut-points) |
| `gwg_low_bound`, `gwg_high_bound` | E C | kg | IOM/NASEM 2009 recommended GWG range at this gestational age and BMI category |
| `gwg_category` | E C | str | `Inadequate` / `Adequate` / `Excessive` |
| `gwg_excessive_flag` | analysis | yes/no | `gwg_category == "Excessive"`, created in notebook 05 |
| `months_between_event_and_conception` | E | float | Months from `event_date` to `estimated_LMP`; positive = conception after exposure started |

## Exposure and treatment metrics

| Variable | Where | Type | Definition |
|---|---|---|---|
| `DrugStart`, `DrugEnd` | D | date | First fill date and last days-supply end date |
| `Supply` | D | days | Median days supply per fill |
| `supply_days` | analysis | days | `DrugEnd − DrugStart`, the length of the treatment window |
| `NumDrugEpisodes` | D | int | Number of treatment episodes (new episode after a gap > 60 days) |
| `Discontinued60` | D | bool | Any gap > 60 days between fills |
| `TotalDiscontinuationTime` | D | days | Total time in gaps longer than 60 days |
| `Reinitiation` | D | bool | Any gap > 60 days that was followed by another fill |
| `AccumulatedPersistenceBeforeDelivery` | D | days | Sum of episode durations, truncated at delivery |
| `AccumulatedPersistenceBeforePregnancy` | D | days | Sum of episode durations, truncated at `estimated_LMP` |
| `ExposedInPregnancy` | D | bool | Any treatment coverage extending past `estimated_LMP` |
| `TotalExposureDaysInPregnancy` | D | days | Total covered days after `estimated_LMP` |
| `med_indict` | D | str | `Diabetes` (Ozempic, Rybelsus) / `Obesity` (Wegovy) / `Unknown`, from the first fill |
| `exposed_T1`, `exposed_T2`, `exposed_T3` | analysis | bool | Treatment window overlaps that trimester |
| `pregnancy_exposure_group` | analysis | str | `No_exposure`, `T1_only`, `T1_T2`, `T2_only`, `T2_T3`, `T3_only`, `Throughout` |
| `user_group` | analysis | str | `continued_user`, `former_user`, `non_user` |
| `new_refill` | analysis | bool | Continued users with more than one treatment episode |

## Outcomes

| Variable | Where | Type | Definition |
|---|---|---|---|
| `gest_diabet` | E C | bool | Gestational diabetes recorded during pregnancy |
| `gest_hyper` | E C | bool | Gestational hypertension recorded during pregnancy |
| `preeclampsia` | E C | bool | Preeclampsia recorded during pregnancy |
| `gest_diabetes_no_prior_t2d` | E C | bool | `gest_diabet` **and not** `t2d_before_pregnancy` — incident gestational diabetes |
| `gest_hyper_no_prior_hyper` | E C | bool | `gest_hyper` **and not** `hyper_before_pregnancy` |
| `preeclampsia_no_prior_hyper` | E C | bool | `preeclampsia` **and not** `hyper_before_pregnancy` |
| `preg_related_htn` | analysis | bool | `gest_hyper_no_prior_hyper` **or** `preeclampsia_no_prior_hyper` |
| `csection` | E C | bool | Caesarean delivery procedure during pregnancy |
| `delivery_type` | E C | str | `C-section` / `Vaginal` |
| `excessive_fetal_weight` | E C | bool | Excessive fetal weight recorded during pregnancy |
| `intra_grow_restrict` | E C | bool | Intrauterine growth restriction during pregnancy |
| `infant_gest_age_class` | E C | str | `Excessive` / `Average`, from `excessive_fetal_weight` |

## Covariates and history

| Variable | Where | Type | Definition |
|---|---|---|---|
| `t2d_before_pregnancy` | E C | bool | Type 2 diabetes recorded before `estimated_LMP` |
| `hyper_before_pregnancy` | E C | bool | Hypertension recorded before `estimated_LMP` |
| `hyperlipid` | E C | bool | Hyperlipidaemia before `estimated_LMP` |
| `osa` | E C | bool | Obstructive sleep apnoea before `estimated_LMP` |
| `depression` | E C | bool | Major depression before `estimated_LMP` |
| `prior_Csection` | E C | bool | Prior-caesarean ICD-10 code at any time |
| `Prior_Preterm_Birth` | E C | bool | Prior-preterm-birth ICD-10 code at any time |
| `parity` | E C | str | `Primiparous` / `Multiparous` / `Unknown` |
| `obstetric_care` | E C | bool | Prenatal-care record. **Definition differs by arm** — during pregnancy for E, any time for C (see README) |
| `Obstetriccare` | C | bool | Legacy alias for `obstetric_care` |

## Demographics

| Variable | Where | Type | Definition |
|---|---|---|---|
| `BirthDateTime` | E C | date | Date of birth |
| `age_at_delivery` | E C | float | Age in years at delivery |
| `age_at_event` | E | float | Age in years at `event_date` |
| `Race`, `Ethnicity`, `Gender` | E C | str | As recorded in Truveta |
| `race_ethnicity` | E C | str | `Non-Hispanic White`, `Non-Hispanic Black`, `Hispanic`, `Other`, `Unknown` |
| `Income` | E C | str | `≤50000`, `50001-80000`, `>80000`, `Unknown` — collapsed from the SDOH estimated annual income bracket |

---

## Exclusions applied during cohort construction

Applied in both notebook 01 and notebook 02 unless noted:

1. Ectopic pregnancy (condition or procedure record) — excluded.
2. Multiple gestation — excluded.
3. Both semaglutide and bariatric surgery — excluded (notebook 01 only; keeps
   the exposure arms mutually exclusive).
4. Delivery before 2022-01-01 — excluded.
5. Delivery whose own code text says preterm/premature — excluded, because
   gestational age comes from Z-codes instead.
6. Gestational age outside 24–42 weeks — excluded.
7. Missing pre-pregnancy or pre-delivery weight — excluded from the main
   analysis (retained in `full_med_wo_weight.csv` / `full_control_df.csv` for
   the sensitivity analysis).
8. Stillbirth — excluded.
9. Missing pre-pregnancy BMI — controls only, applied in notebook 05.
10. Semaglutide initiated during pregnancy — excluded in notebook 05.

Additional exposure-window filters: bariatric surgery before 2017-01-01 and
semaglutide dispensing before 2021-01-01 are not counted as exposures.
