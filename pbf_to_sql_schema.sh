export PGPASSWORD=Support@123;

createdb -U postgres miami_osmclip_sql_20221010;
psql -U postgres -d miami_osmclip_sql_20221010 -c 'CREATE EXTENSION postgis; CREATE EXTENSION hstore;'

psql -U postgres -d miami_osmclip_sql_20221010 -f /home/lohitd@nextbillion.ai/Documents/pendrive_backup/code/sql/NBqueries/postgresqldb_schema.sql

osmosis --read-xml /home/lohitd@nextbillion.ai/Downloads/Miami_POI_bnd.osm --write-apidb database=miami_osmclip_sql_20221010 user=postgres password=Support@123 validateSchemaVersion=no populateCurrentTables=no
