# Quantitative Multispecies eDNA

A reproducible pipeline that combines **qPCR** (absolute abundance for a reference species) with **metabarcoding** (compositional, multi-species) in a **joint statistical model**, then fits **spatial smooths** to map estimated DNA concentrations and produces all manuscript figures.

Where things live (each source holds a different, non-overlapping part of the project):

- **Code, Stan models, and figures** → this **GitHub** repository (cloned). Includes `code/`, `plots/` (final manuscript figures), `raw_plots/`, and this README.
- **Data** → **Zenodo** (record `20754663`, `Data.zip`): raw + lightly processed inputs (`data/`) and cached model outputs (`Intermediate_data/`). **No code is stored on Zenodo** — the code comes from GitHub. `Data.zip` is downloaded automatically by the first script you run (see Quick start).
- **Raw sequencing reads** → **NCBI SRA** (BioProject `PRJNA1426049`).

> **Note on large files:** `Data.zip` (and any `Code_and_raw_data.zip`) are **not** committed to this repository — they are too large for git. They live on Zenodo (fetched by `code/0_Download_data.R`) and only exist locally after you download them.

---

## Quick start

> **Step 0 — run this first.** [`code/0_Download_data.R`](code/0_Download_data.R) is the entry point that initiates everything. It downloads all data and raw sequences, so nothing else will run until it completes.

1. **Clone this repository** (or download it as a ZIP and unzip it).
2. **Open the RStudio project**: double-click `Quantitative-Multispecies-eDNA.Rproj`. This sets the correct working directory so `here()` resolves paths properly.
3. **Run [`code/0_Download_data.R`](code/0_Download_data.R)** — the "**0**" file. This will:
   - Download the data archive (`Data.zip`) from **Zenodo** (record `20754663`) and unpack it into the project, populating `data/` and `Intermediate_data/`. (The code is already present from cloning this repo.)
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
├── code/                 Core analysis code                 (GitHub)
├── plots/                Final manuscript figures           (GitHub)
├── raw_plots/            Figures created with other software (GitHub)
├── data/                 Raw and lightly processed inputs    (Zenodo — Data.zip)
├── Intermediate_data/    Cached pipeline outputs             (Zenodo — Data.zip / regenerated)
└── SRA/                  Raw sequencing data                 (NCBI SRA — via 0_Download_data.R)
    ├── fastq/                Per-run FASTQ files
    ├── metadata/             SRA run metadata
    ├── combined_R2.fastq.gz  Concatenated reverse reads (compressed)
    └── combined_R2.fastq     Concatenated reverse reads (decompressed)
```

---

## `code/` — core analysis code

### Step 0 — setup

- **[`0_Download_data.R`](code/0_Download_data.R)** — **run this first.** Downloads data + code from Zenodo and raw sequences from the SRA, then opens the analysis notebooks. Everything else depends on it.
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

## `plots/` — final manuscript figures

Publication-ready figures generated by [`3_All_Figures.qmd`](code/3_All_Figures.qmd) from the model outputs (joint model + spatial smooths). Files are numbered in manuscript order; the leading number is a sort key, not the figure number.

- `2_Figure_2.jpg` – `5_Figure_5.jpg` — main-text Figures 2–5.
- `6_Supplemental_Figure_1.jpg` – `16_Supplementary_Figure_11.jpg` — Supplementary Figures 1–11.
- `10_Supplementary_Figure_5_A.jpg` – `..._D.jpg` — the four panels (A–D) of Supplementary Figure 5.

> **Figure 1** is not produced by the analysis code — it (and Supplementary Figure 1) are created in other software and live in `raw_plots/` (see below).

---

## `raw_plots/` — figures made outside the analysis pipeline

Figures and source files created with other tools (not generated by the `.qmd` notebooks), kept here for provenance and for assembling the final manuscript figures.

- `1_Figure_1.jpg` / `1_Figure_1.pdf` — main-text Figure 1 (study design / overview).
- `6_Supplementary_Figure_1.jpg` / `.pdf` — Supplementary Figure 1.
- `DAG.tex` — TikZ/LaTeX source for the model directed acyclic graph.
- `Literature_species_dist_1.jpg`, `Literature_species_dist_2.jpg` — literature-derived species distribution reference figures.

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

After completing **Step 0** ([`0_Download_data.R`](code/0_Download_data.R)):

1. **Run the joint model + calibration** — render [`code/1_Run_QM_qPCR.qmd`](code/1_Run_QM_qPCR.qmd). Writes model inputs/outputs to `Intermediate_data/`.
2. **Fit spatial smooths** — render [`code/2_sdmTMB_smooths_13sp.qmd`](code/2_sdmTMB_smooths_13sp.qmd). Writes smoothed outputs and map-uncertainty objects to `Intermediate_data/`.
3. **Build final figures** — render [`code/3_All_Figures.qmd`](code/3_All_Figures.qmd). Uses `Intermediate_data/` as input.

---

## Data sources

- **Code, Stan models, and figures (`code/`, `plots/`, `raw_plots/`):** this GitHub repository.
- **Data archive (raw + lightly processed inputs and cached intermediate model outputs):** [Zenodo record 20754663](https://zenodo.org/records/20754663) (`Data.zip` → `data/` and `Intermediate_data/`). Contains no code.
- **Raw sequencing reads:** NCBI SRA BioProject [`PRJNA1426049`](https://www.ncbi.nlm.nih.gov/bioproject/PRJNA1426049).

## Notes

- This is an **RStudio project**: open `Quantitative-Multispecies-eDNA.Rproj` to get the correct working directory before running anything.
