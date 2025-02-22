import json

def count_select(filename):
    count = 0

    sql_commands = [
        "SELECT", 
        "INSERT", 
        "UPDATE", 
        "DELETE", 
        "CREATE", 
        "ALTER", 
        "DROP", 
        "TRUNCATE", 
        "BEGIN", 
        "COMMIT", 
        "ROLLBACK", 
        "EXPLAIN", 
        "COPY", 
        "VACUUM"
    ]
   
    with open(filename, 'r') as file:
        for line in file:
            data = json.loads(line.strip())
            if data.get('sol_sql') and any(query.startswith(cmd) for cmd in sql_commands for query in data['sol_sql']):
                count += 1

    print(count)

if __name__ == "__main__":
    filename = '../../data/bc-1-fexp/data/GTsql_original.jsonl'
    count_select(filename)
