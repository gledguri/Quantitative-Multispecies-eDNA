# Quantitative Multispecies eDNA

A reproducible pipeline that combines **qPCR** (absolute abundance for a reference species) with **metabarcoding** (compositional, multi-species) in a **joint statistical model**, then fits **spatial smooths** to map estimated DNA concentrations and produces all manuscript figures.

This GitHub repository holds the **code**. The **data** is hosted externally and is downloaded automatically by the first script you run (see Quick start):

- **Code** → this GitHub repository (cloned).
- **Data** → **Zenodo** (record `20753379`): processed + raw data, intermediate model outputs, and figures.
- **Raw sequencing reads** → **NCBI SRA** (BioProject `PRJNA1426049`).

---

## Quick start

> **Step 0 — run this first.** [`code/0_Download_data_and_code.R`](code/0_Download_data_and_code.R) is the entry point that initiates everything. It downloads all data and raw sequences, so nothing else will run until it completes.

1. **Clone this repository** (or download it as a ZIP and unzip it).
2. **Open the RStudio project**: double-click `Quantitative-Multispecies-eDNA.Rproj`. This sets the correct working directory so `here()` resolves paths properly.
3. **Run [`code/0_Download_data_and_code.R`](code/0_Download_data_and_code.R)** — the "**0**" file. This will:
   - Download the processed data + code archive from **Zenodo** (record `20753379`) and unpack it into the project.
   - Download the raw sequencing reads from the **NCBI SRA** (BioProject `PRJNA1426049`) into `SRA/` via the Python helper scripts.
   - Concatenate and decompress the reads into `SRA/combined_R2.fastq`.
4. **Run the analysis notebooks in order** (see [Recommended run order](#recommended-run-order)).

**Prerequisites**

- R (with RStudio recommended) and the packages `here`, `jsonlite`, `R.utils` (auto-installed if missing), plus the analysis packages used in the notebooks (`tidyverse`, `rstan`, `sf`, `sdmTMB`, `viridis`, `cowplot`).
- **Python 3** on your `PATH` (used by the SRA download scripts; lightweight deps `requests` and `pandas` are auto-installed).
- Internet access. A 1-hour download timeout is set for the large sequencing files.

---

## Repository structure

```
Quantitative-Multispecies-eDNA/
├── code/                 Core analysis code (this repo)
├── data/                 Raw and lightly processed inputs   (from Zenodo)
├── Intermediate_data/    Cached pipeline outputs            (from Zenodo / regenerated)
├── raw_plots/            Figures created with other software(from Zenodo)
└── SRA/                  Raw sequencing data                (from NCBI SRA / can be downloaded through 0_.R)
    ├── fastq/                Per-run FASTQ files
    ├── metadata/             SRA run metadata
    ├── combined_R2.fastq.gz  Concatenated reverse reads (compressed)
    └── combined_R2.fastq     Concatenated reverse reads (decompressed)
```

---

## `code/` — core analysis code

### Step 0 — setup

- **[`0_Download_data_and_code.R`](code/0_Download_data_and_code.R)** — **run this first.** Downloads data + code from Zenodo and raw sequences from the SRA, then opens the analysis notebooks. Everything else depends on it.
- **[`sra_python/download_sra.py`](code/sra_python/download_sra.py)** — downloads FASTQ files and run metadata for BioProject `PRJNA1426049` into `SRA/fastq/` and `SRA/metadata/`. Called by step 0.
- **[`sra_python/concatenate_fastq.py`](code/sra_python/concatenate_fastq.py)** — concatenates the per-run reverse reads into a single `SRA/combined_R2.fastq.gz`. Called by step 0.

### Analysis notebooks (Quarto `.qmd`)

- **[`1_Run_QM_qPCR.qmd`](code/1_Run_QM_qPCR.qmd)** — runs the joint model linking qPCR (absolute, reference species) with metabarcoding (compositional), producing model-ready objects and posterior outputs.
- **[`2_sdmTMB_smooths_13sp.qmd`](code/2_sdmTMB_smooths_13sp.qmd)** — fits spatial (`sdmTMB`) smooths to the joint-model concentration estimates and produces map-ready outputs.
- **[`3_All_Figures.qmd`](code/3_All_Figures.qmd)** — produces the final figures from the model outputs (joint model + smooths).

### Stan models — `code/Stan_models/` (used by `1_Run_QM_qPCR.qmd`)

- **`Joint_model.stan`** — joint model linking qPCR (absolute, reference species) with metabarcoding (compositional, multi-species).
- **`Mock_model.stan`** — mock-community calibration component (e.g., amplification efficiency / bias parameters).
- **`Mock_model.rds`** — saved fitted calibration object for the mock model (kept here for reuse).

### R helper scripts

- **[`load_QM-qPCR_data.R`](code/load_QM-qPCR_data.R)** — loads raw inputs from `data/` and standardizes formats.
- **[`qm_data_prep_functions.R`](code/qm_data_prep_functions.R)** — shared utilities for cleaning, joins, reshaping, and QC.
- **[`smoothers.R`](code/smoothers.R)** — helper functions for the smoothing / mapping stage.

---

## `data/` — raw and lightly processed inputs

Downloaded from Zenodo. Used by the workflow.

- `hake_qpcr/` — qPCR inputs for the reference species.
- `metabarcoding/` — metabarcoding reads for environmental samples.
- `metabarcoding_db/` — taxonomy / reference database products used in assignment.
- `metabarcoding_mocks/` — mock-community inputs/outputs used for amplification-bias calibration.
- `metadata/` — station/sample metadata (locations, depths, cruise/station IDs, etc.).

---

## `Intermediate_data/` — cached pipeline outputs

Downloaded from Zenodo so you can skip expensive steps. **Everything here is regenerated by `1_Run_QM_qPCR.qmd` and `2_sdmTMB_smooths_13sp.qmd`.**

- `Joint_mod_data_input.rds` — compiled data object passed into the joint model.
- `Joint_mod_output.rds` — joint-model results / posterior summaries.
- `Mock_mod_output.rds` — mock-community calibration outputs (amplification efficiencies / bias-correction objects).
- `Log_D_est.rds` — species-by-sample estimated log DNA concentrations from the joint model.
- `Log_D_est_smoothed.rds` — smoothed (`sdmTMB`) versions of `Log_D_est`.
- `all_maps_se.rds` — standard errors / uncertainty layers for mapped smooth predictions.

---

## Recommended run order

After completing **Step 0** ([`0_Download_data_and_code.R`](code/0_Download_data_and_code.R)):

1. **Run the joint model + calibration** — render [`code/1_Run_QM_qPCR.qmd`](code/1_Run_QM_qPCR.qmd). Writes model inputs/outputs to `Intermediate_data/`.
2. **Fit spatial smooths** — render [`code/2_sdmTMB_smooths_13sp.qmd`](code/2_sdmTMB_smooths_13sp.qmd). Writes smoothed outputs and map-uncertainty objects to `Intermediate_data/`.
3. **Build final figures** — render [`code/3_All_Figures.qmd`](code/3_All_Figures.qmd). Uses `Intermediate_data/` as input.

---

## Data sources

- **Code:** this GitHub repository.
- **Data archive (processed + raw data, intermediate outputs, figures):** [Zenodo record 20753379](https://zenodo.org/records/20753379) (`Code_and_raw_data.zip`).
- **Raw sequencing reads:** NCBI SRA BioProject [`PRJNA1426049`](https://www.ncbi.nlm.nih.gov/bioproject/PRJNA1426049).

## Notes

- This is an **RStudio project**: open `Quantitative-Multispecies-eDNA.Rproj` to get the correct working directory before running anything.
