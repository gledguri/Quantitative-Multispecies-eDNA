# =============================================================================
# Download_data_and_code.R
# =============================================================================
#
# START HERE — This is the first script to run for reproducing the analysis.
#
# This script downloads all data, code, and raw sequencing files needed to run
# the Quantitative Multispecies eDNA (QM-qPCR) pipeline. It performs three
# main steps:
#
#   1. Download processed data and code from Zenodo (record 20753379)
#      - Code_and_raw_data.zip: contains analysis notebooks, Stan models,
#        helper functions, raw/intermediate data, and metadata
#      - After unzipping, project directories (code/, data/, Intermediate_data/)
#        are populated with all files needed for the analysis
#
#   2. Download raw sequencing data from NCBI SRA (BioProject PRJNA1426049)
#      - Fetches paired-end FASTQ files via ENA and saves to SRA/fastq/
#      - Run metadata is saved to SRA/metadata/
#      - All FASTQ files are concatenated into SRA/combined_R2.fastq.gz
#        and decompressed to SRA/combined_R2.fastq
#
#   3. Open analysis notebooks (Quarto .qmd files) for the next steps:
#      - 1_Run_QM_qPCR.qmd       : Joint QM-qPCR model of hake survey samples
#      - 2_sdmTMB_smooths_13sp.qmd: Spatial smooths of joint model output
#      - 3_All_Figures.qmd        : Generate all manuscript figures
#
# Prerequisites:
#   - R packages: here, jsonlite, R.utils (auto-installed if missing)
#   - Python 3 with internet access (for SRA download scripts)
#   - ~1 hour timeout is set for large file downloads
#
# Output directory structure:
#   project_root/
#   ├── code/            Analysis scripts and Stan models (from Zenodo)
#   ├── data/            Raw qPCR, metabarcoding, and metadata (from Zenodo)
#   ├── Intermediate_data/  Model outputs and processed data (from Zenodo)
#   └── SRA/             Raw sequencing data (from NCBI SRA)
#       ├── fastq/           Per-run FASTQ files
#       ├── metadata/        SRA run metadata
#       ├── combined_R2.fastq.gz  Concatenated reverse reads (compressed)
#       └── combined_R2.fastq     Concatenated reverse reads (decompressed)
#
# =============================================================================
library(here)


# --- Download files from Zenodo --------------------------------------------------------------

options(timeout = 3600) 
# record_id <- "18603204"
record_id <- "20753379"

meta <- jsonlite::fromJSON(paste0("https://zenodo.org/api/records/", record_id))

files <- meta$files

print(files[, c("key", "size", "links")])

# This will download the files into the project directory
download.file(
  url = files$links$self[1],   # first file; adjust index as needed
  destfile = files$key[1],
  mode = "wb")


# --- Unzip files from Zenodo -----------------------------------------------------------------
tmp <- tempfile()
unzip("Code_and_raw_data.zip", exdir = tmp, unzip = "unzip")

inner <- file.path(tmp, "Code_and_raw_data")
files <- list.files(inner, all.files = TRUE, no.. = TRUE, full.names = TRUE)
file.copy(files, ".", recursive = TRUE)

unlink(tmp, recursive = TRUE)   # clean up the temp copy


# --- Open one of the analysis notebooks -------------------------------------
# file.edit(here("Code", "1_Run_QM_qPCR.qmd"))
# file.edit(here("Code", "2_sdmTMB_smooths_13sp.qmd"))
file.edit(here("Code", "3_All_Figures.qmd"))


# --- Download raw sequencing data from the SRA (optional) ------------------------------------
# Download all SRA data
system2("python3", here("code", "download_sra.py"))

# Concatenate all SRA fastq data
system2("python3", here("code", "concatenate_fastq.py"))

# Unzipt the SRA fastq concatenated data
if (!requireNamespace("R.utils", quietly = TRUE)) install.packages("R.utils")
R.utils::gunzip(here('SRA','combined_R2.fastq.gz'), remove = FALSE)

