
#!/bin/bash
set -a
. arango.env
set +a

echo "Import IMDB datasets to Arango."

##arangoimport --file $ARANGO_IMPORT_TEMP_DIR/name.basics.tsv --server.endpoint tcp://$ARANGO_SERVER --server.password $ARANGO_ROOTPASSWORD --server.database $MOVIES_DATABASE_NAME --collection=name_basics --create-collection=true --type=tsv  --translate "nconst=_key" 

##arangoimport --file $ARANGO_IMPORT_TEMP_DIR/title.akas.tsv --server.endpoint tcp://$ARANGO_SERVER --server.password $ARANGO_ROOTPASSWORD --server.database $MOVIES_DATABASE_NAME --collection=title_akas --create-collection=true --type=tsv --translate "tconst=_key" 

##arangoimport --file $ARANGO_IMPORT_TEMP_DIR/title.basics.tsv --server.endpoint tcp://$ARANGO_SERVER --server.password $ARANGO_ROOTPASSWORD --server.database $MOVIES_DATABASE_NAME --collection=title_basics --create-collection=true --type=tsv --translate "tconst=_key" 

##arangoimport --file $ARANGO_IMPORT_TEMP_DIR/title.crew.tsv --server.endpoint tcp://$ARANGO_SERVER --server.password $ARANGO_ROOTPASSWORD --server.database $MOVIES_DATABASE_NAME --collection=title_crew --create-collection=true --type=tsv --translate "tconst=_key" 

##arangoimport --file $ARANGO_IMPORT_TEMP_DIR/title.episode.tsv --server.endpoint tcp://$ARANGO_SERVER --server.password $ARANGO_ROOTPASSWORD --server.database $MOVIES_DATABASE_NAME --collection=title_episodes --create-collection=true --type=tsv  --translate "tconst=_key" 

##arangoimport --file $ARANGO_IMPORT_TEMP_DIR/title.ratings.tsv --server.endpoint tcp://$ARANGO_SERVER --server.password $ARANGO_ROOTPASSWORD  --server.database $MOVIES_DATABASE_NAME --collection=title_ratings --create-collection=true --type=tsv  --translate "tconst=_key" 

#In this Both tconst and nconst are repeated so need to import with unique ID
##arangoimport --file $ARANGO_IMPORT_TEMP_DIR/title.principals.tsv --server.endpoint tcp://$ARANGO_SERVER --server.password $ARANGO_ROOTPASSWORD --server.database $MOVIES_DATABASE_NAME --collection=title_principals --create-collection=true --type=tsv

##arangoimport --file professions_basics.csv --server.endpoint tcp://$ARANGO_SERVER --server.password $ARANGO_ROOTPASSWORD --server.database $MOVIES_DATABASE_NAME --collection=professions_basics --create-collection=true --type=csv --translate "Profession=_key" 

##arangoimport --file genres_basics.csv --server.endpoint tcp://$ARANGO_SERVER --server.password $ARANGO_ROOTPASSWORD --server.database $MOVIES_DATABASE_NAME --collection=genres_basics --create-collection=true --type=csv --translate "Genres=_key"

# Can do the Edges Now

echo "$(date)"

#First Create the edge collection

arangosh --server.endpoint tcp://$ARANGO_SERVER --server.username $MOVIES_DATABASE_USERNAME --server.password $MOVIES_PASSWORD --server.database $MOVIES_DATABASE_NAME --javascript.execute-string 'db._createEdgeCollection("movie_edges_direct");'

#Then Import to Edge File

echo "$(date)"
echo "Importing Principals to Edges"


awk -F'\t' 'BEGIN{OFS="\t"}
NR==1 {print "tconst", "nconst", "_key"; next}
      {print $1, $3, $1 $3}' \
  "$ARANGO_IMPORT_TEMP_DIR/title.principals.tsv" \
  > "$ARANGO_IMPORT_TEMP_DIR/title.principals.withkey.tsv"

echo "Creating Deduped Pricipals"

sort -t$'\t' -k3,3 -u \
  "$ARANGO_IMPORT_TEMP_DIR/title.principals.withkey.tsv" \
  > "$ARANGO_IMPORT_TEMP_DIR/title.principals.deduped.tsv"

arangoimport \
  --file "$ARANGO_IMPORT_TEMP_DIR/title.principals.deduped.tsv" \
  --server.endpoint tcp://$ARANGO_SERVER \
  --server.password "$ARANGO_ROOTPASSWORD" \
  --server.database "$MOVIES_DATABASE_NAME" \
  --collection movie_edges_direct \
  --type tsv \
  --translate tconst=_from \
  --translate nconst=_to \
  --from-collection-prefix title_basics \
  --to-collection-prefix name_basics \
  --create-collection-type edge \
  --on-duplicate ignore

#Maybe can do One Hit Wonders by building temp file 

echo "$(date)"

echo -e "knownForTitles\tnconst\t_key" \
  > "$ARANGO_IMPORT_TEMP_DIR/one_hit_edges.withkey.tsv"

echo "Importing One Hit Wonders to Edges"

awk -F'\t' 'BEGIN{OFS="\t"; print "knownForTitles", "nconst", "_key"}
$6 != "\\N" && index($6, ",") == 0 {
    print $6, $1, $6 $1
}' "$ARANGO_IMPORT_TEMP_DIR/name.basics.tsv" \
  > "$ARANGO_IMPORT_TEMP_DIR/one_hit_edges.withkey.tsv"

echo "Creating Deduped One Hit"


sort -t$'\t' -k3,3 -u \
  "$ARANGO_IMPORT_TEMP_DIR/one_hit_edges.withkey.tsv" \
  > "$ARANGO_IMPORT_TEMP_DIR/one_hit_edges.deduped.tsv"

arangoimport \
  --file "$ARANGO_IMPORT_TEMP_DIR/one_hit_edges.deduped.tsv" \
  --server.endpoint tcp://$ARANGO_SERVER \
  --server.password "$ARANGO_ROOTPASSWORD" \
  --server.database "$MOVIES_DATABASE_NAME" \
  --collection movie_edges_direct \
  --type tsv \
  --translate knownForTitles=_from \
  --translate nconst=_to \
  --from-collection-prefix title_basics \
  --to-collection-prefix name_basics \
  --create-collection-type edge \
  --on-duplicate ignore


echo "$(date)"