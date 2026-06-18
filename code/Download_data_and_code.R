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
unzip("Code_and_raw_data.zip", exdir = tmp)

inner <- file.path(tmp, "Code_and_raw_data")
files <- list.files(inner, all.files = TRUE, no.. = TRUE, full.names = TRUE)
file.copy(files, ".", recursive = TRUE)

unlink(tmp, recursive = TRUE)   # clean up the temp copy

# --- Open one of the analysis notebooks -------------------------------------
# file.edit(here("Code", "1_Run_QM_qPCR.qmd"))
# file.edit(here("Code", "2_sdmTMB_smooths_13sp.qmd"))
file.edit(here("Code", "3_All_Figures.qmd"))

# --- Download raw sequencing data from the SRA ------------------------------
system2("python3", here("Code", "download_sra.py"))
