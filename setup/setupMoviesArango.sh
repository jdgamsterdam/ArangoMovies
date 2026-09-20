#!/bin/bash
set -a
. arango.env
set +a

# Make sure Arango Script tools and any requirements are installed
##sudo apt-get -y update
##sudo apt-get -y install wget gzip
##sudo ./setupclienttools.sh

#Download newest IMDB files and extract from Gzip
sudo ./get_all_imdb_from_web.sh

# Create Movies Database and Database Admin-Done through Javascript

arangosh --server.endpoint tcp://$ARANGO_SERVER --server.username root --server.password $ARANGO_ROOTPASSWORD --javascript.execute createmoviedatabases.js


#Use ArangoImport to import 
./import_imdb.sh

#Create additional collections for Database
python create_Movie_Collections.py


# Final Indexes and views done with ArangoSh. NOTE The Following can take about 30 minutes. 
echo "Starting Indexing May take 20-30 min"

arangosh --server.endpoint tcp://$ARANGO_SERVER --server.password $ARANGO_ROOTPASSWORD --server.database $MOVIES_DATABASE_NAME --javascript.execute title_principals_index.js
#arangosh --server.endpoint tcp://$ARANGO_SERVER --server.password $ARANGO_ROOTPASSWORD --server.database $MOVIES_DATABASE_NAME --javascript.execute createmovieindexes.js
#arangosh --server.endpoint tcp://$ARANGO_SERVER --server.password $ARANGO_ROOTPASSWORD --server.database $MOVIES_DATABASE_NAME --javascript.execute create_graph.js