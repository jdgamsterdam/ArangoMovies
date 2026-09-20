#!/bin/bash
set -a
. arango.env
set +a

# Ensure target directory exists
mkdir -p "$ARANGO_IMPORT_TEMP_DIR"

# List of IMDB dataset files to download
IMDB_FILES=(
  "name.basics.tsv.gz"
  "title.akas.tsv.gz"
  "title.basics.tsv.gz"
  "title.crew.tsv.gz"
  "title.episode.tsv.gz"
  "title.principals.tsv.gz"
  "title.ratings.tsv.gz"
)

# Loop through each file
for FILE in "${IMDB_FILES[@]}"; do
    echo "Processing $FILE ..."

    # Download into the directory
    wget -N -P "$ARANGO_IMPORT_TEMP_DIR" "https://datasets.imdbws.com/$FILE"

    # Extract in place
    gzip -df "$ARANGO_IMPORT_TEMP_DIR/$FILE"
done

echo "All IMDB datasets downloaded and extracted."