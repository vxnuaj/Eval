### INIT

1. `cd` into `src/psql_db`
2. Populate `postgres_cred.json` w proper credentials for postgres db.
3. Run `start_postgresdb.py` as:

    ```python
    python3 start_postgresdb.py --db_dump_dir data/bc-1-fexp/data/postgresDB --n_sql 86
    ```
4. Run `python3 collect_gt.py`
5. `cd` into `src/eval`
6. Run `eval.py`