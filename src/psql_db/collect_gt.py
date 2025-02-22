import psycopg2
import csv
import sys
import json
import logging
import os

logging.basicConfig(
    level=logging.INFO, 
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers = [
        logging.FileHandler('../../logs/collect_gt.log', mode = 'w'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

def execute_sql(cursor, query, alter=False):
    """Execute SQL using an existing cursor."""
    try:
        cursor.execute(query)
        results = cursor.fetchall() if not alter else None  
        return True, results
    
    except Exception as e:
        if alter:
            return False, 'alter_error'
        logger.error(f"Error executing query: {e}")
        return False, None


def write_to_csv(results, output_filename):
    """Write query results to a CSV file."""
    try:
        with open(output_filename, mode='w', newline='') as file:
            writer = csv.writer(file)
            if results:
                for row in results:
                    writer.writerow(row)
        logger.info(f"Results written to {output_filename}")
    except Exception as e:
        logger.error(f"Error writing to CSV: {e}")


def process_queries(dataset, alter_dataset, db_name, user, password, output_dir):
    """Process queries in a batch while maintaining a single DB connection."""
    
    logger.info(f"Processing {len(dataset)} queries") 
    query_ids_list = []

    try:
        conn = psycopg2.connect(dbname=db_name, user=user, password=password)
        cursor = conn.cursor()

        for i, query_data in enumerate(dataset):
            instance_id = query_data.get('instance_id')
            sol_sql = query_data.get('sol_sql', [])
            alter_sql = alter_dataset[i].get('preprocess_sql', None)
            clean_sql = alter_dataset[i].get('clean_up_sql', None)
            results = None

            if alter_sql:
                for asql in alter_sql: 
                    logger.info(f"Processing SQL {instance_id}: {asql}")
                    status, _ = execute_sql(cursor, asql, alter=True)
                    if status:
                        logger.info(f"Successfully preprocessed SQL {instance_id}")
                    elif not status and 'alter_error':
                        conn.rollback()
                        pass
                    else:
                        logger.error(f"Did not successfully preprocess SQL {instance_id}")
                        conn.rollback()
            else:
                logger.info(f"No preprocess SQL for {instance_id}")

            for ssql in sol_sql:
                logger.info(f"Running SQL {instance_id}: {ssql}")
                status, results = execute_sql(cursor, ssql)
                if status:
                    logger.info(f"Ran SQL query {instance_id}")

            if clean_sql:
                for csql in clean_sql:
                    logger.info(f"Cleaning up SQL {instance_id}: {csql}")
                    status, _ = execute_sql(cursor, csql, alter=True)
                    if status:
                        logger.info(f"Successfully cleaned up SQL {instance_id}")
                    elif not status and 'alter_error':
                        pass
                    else:
                        logger.error(f"Did not successfully clean up SQL {instance_id}")
                        conn.rollback()
            else:
                logger.info(f"No clean up SQL for {instance_id}")

            if results:
                query_ids_list.append(instance_id) 
                output_filename = os.path.join(output_dir, f"query_{instance_id}_output.csv")
                write_to_csv(results, output_filename)

        conn.commit()
        cursor.close()
        conn.close()

        with open('../../data/bc-1-fexp/data/query_ids.json', 'w') as file:
            json.dump(query_ids_list, file)

    except Exception as e:
        logger.error(f"Database connection error: {e}")
        if conn:
            conn.close()
            sys.exit(1)

def load_dataset(filename):
    dataset = []
    with open(filename, 'r') as file:
        for line in file:
            dataset.append(json.loads(line)) 
    return dataset

def main():
    
    with open("postgres_cred.json", 'r') as file:
        cred = json.load(file)
   
    db_name = cred['db_name']
    user = cred['super_user']
    password = cred['password']
    output_dir = '../../data/bc-1-fexp/data/gtout'
    dataset_dir = '../../data/bc-1-fexp/data/GTsql_filtered.jsonl'
    alter_dataset_dir = '../../data/bc-1-fexp/data/input_filtered.jsonl'

    os.makedirs(output_dir, exist_ok=True)

    dataset = load_dataset(dataset_dir) 
    alter_dataset = load_dataset(alter_dataset_dir)
    
    process_queries(dataset, alter_dataset, db_name, user, password, output_dir)

if __name__ == "__main__":
    main()
