## Notes on Dataset

`GTsql_original.jsonl` are the ground truth solution SQLs for the queries contained in `input_original.jsonl`. These extracted from the bird-critic dataset. 

`GTsql_filtered.jsonl` are the ground truth solution SQLs for the queries contained in `input_filtered.jsonl`. These extracted from the bird-critic dataset but are filtered to the queries which are meant to interact with databases.

`query_ids.json` is the file which holds a list of `instance_ids` which correspond to the queries which are meant to interact with the DB.

Under `postgresDB/`, we have the raw `.sql` files that are to be compiled into a PostgreSQL DB by running the `src/init_psql_db/startpostgresdb.py` script, where the DB is defined by the `postgres_cred.json`

Under `gtout` we have the outputs to the queries in `GTsql_filtered.jsonl` which were extracted by running those queries in their respective databases.