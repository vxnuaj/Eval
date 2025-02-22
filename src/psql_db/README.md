### INIT_DB

Running `start_postgresdb.py`  as:

```zsh
python start_postgresdb.py  --db_dump_dir <dir_of_sql_dump> --n_sql <total_sql_expected> 
```

Takes the `.sql` files listed under `<dir_of_sql_dump>` and puts them into the existing database `<name_of_existing_db>`.

The script expects the database to exist and it's credentials to be listed in the `postgres_cred.json` file, as `password`, `superuser`, 

The tag, `--n_sql` is optional. If `--n_sql`, the script will log how many files were successfully moved into the DB relative to the expected `<total_sql_expected>`

### OTHER

To see any postgresDB, run

```bash
psql -U <super_user> -d <db_name> 
```

replacing `super_user` and `db_name` with the proper super username and the database name respectively.