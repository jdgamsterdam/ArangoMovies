
#!/bin/bash
set -a
. arango.env
set +a

echo "Import add title_crew to title_pricipals"

arangoimport \
  --file "$ARANGO_IMPORT_TEMP_DIR/title_crew.tsv" \
  --server.endpoint tcp://$ARANGO_SERVER \
  --server.password "$ARANGO_ROOTPASSWORD" \
  --server.database "$MOVIES_DATABASE_NAME" \
  --collection all_crew \
  --type tsv \
  --create-collection=true \
  --on-duplicate ignore

echo "$(date)"