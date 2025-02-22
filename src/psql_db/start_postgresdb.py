import subprocess
import os
import logging
import time
import argparse
import sys
import platform
import json

parser = argparse.ArgumentParser()

logging.basicConfig(
    level=logging.INFO, 
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers = [
        logging.FileHandler('../../logs/start_postgresdb.log', mode = 'w'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

parser.add_argument('--db_dump_dir', type=str, required=True, help='directory containing dump files')
parser.add_argument('--n_sql', type = int, required = False, help = 'number of SQL files to restore')

def get_creds():
    with open('postgres_cred.json', 'r') as f:
        cred = json.load(f)
    return cred

def is_postgres_running():
    try:
        subprocess.check_output(['pg_isready'])
        logging.info('Postgres is already running')
        return True
    except subprocess.CalledProcessError:
        logging.error('Postgres is not running')
        return False

def start_postgres():
    if not is_postgres_running():
        logging.info('Starting Postgres')
        
        if not check_postgresql_installed():
            logging.error('PostgreSQL is not installed.')
            sys.exit(1)  
        
        os_type = platform.system().lower()
        
        if os_type == 'darwin':
            os.system('brew services start postgresql')
        elif os_type == 'linux':
            try:
                os.system('sudo systemctl start postgresql')
            except Exception as e:
                logging.error(f"Error starting PostgreSQL on Linux: {e}")
                sys.exit(1)
        else:
            logging.error(f"Unsupported OS type for {os_type}")
            sys.exit(1)
        
        time.sleep(5)

def check_postgresql_installed():
    try:
        result = subprocess.run(['psql', '--version'], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        return result.returncode == 0
    except FileNotFoundError:
        return False

def database_exists(db_name, super_user):
    try:
        output = subprocess.check_output(['psql', '-U', f'{super_user}', '-lqt'])
        if db_name in output.decode():
            logging.info(f'Database {db_name} already exists')
            return True
        else:
            logging.info(f'Database {db_name} does not exist')
            return False
    except subprocess.CalledProcessError:
        logging.error('Error checking database existence')
        return False


def restore_database(db_name, db_dump_dir, db_user, password, args):
    logging.info('Restoring database')
    db_dump_dir = os.path.join('../../', db_dump_dir)
  
    os.environ['PGPASSWORD'] = password
   
    i = 0
    
    for filename in os.listdir(db_dump_dir):
        
        if filename.endswith('.sql'):
            
            sql_file_path = os.path.join(db_dump_dir, filename)
            
            logging.info(f'Processing {filename}')
            try:
                with open(sql_file_path, 'r') as file:
                    file_contents = file.read()

                file_contents = file_contents.replace('root', db_user)

                with open(sql_file_path, 'w') as file:
                    file.write(file_contents)

                logging.info(f'Successfully modified roles in {filename}')

                subprocess.check_call(
                    ['psql', '-U', db_user, '-d', db_name, '-f', sql_file_path],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE 
                    )
                logging.info(f'Successfully restored {filename}')
                
                i += 1
                
            except subprocess.CalledProcessError as e:
                logging.error(f'Error restoring {filename}: {e}')
                sys.exit(1)

    if args.n_sql:
        if i != args.n_sql:
            logging.error(f'Expected to restore {args.n_sql} SQL files, but restored {i} SQL files')
            sys.exit(1)   
        else:
            logging.info(f'Successfully restored {i} / {args.n_sql} SQL files')
    else:
        logging.info(f'Successfully restored {i} SQL files')

def warnings():
    cont_bool = input("WARNING: This script will restore the database with the dump file(s). Continue? [Y / N]: ")
    if cont_bool.lower() == 'n':
        logging.info("User opted to exit.")
        sys.exit() 
    elif cont_bool.lower() != 'y':
        logging.error("Invalid input. Please enter 'Y' or 'N'.")
        sys.exit(1)

def main():
    args = parser.parse_args()
    creds = get_creds()
    superuser = creds['super_user']
    password = creds['password']
    db_name = creds['db_name']

    warnings()
    
    start_postgres()
    
    if not database_exists(creds['db_name'], creds['super_user']):
        logging.error(f"Database {creds['db_name']} does not exist. Exiting.")
        sys.exit(1)  # if the DB does not exist, exit the script
    
    restore_database(db_name, args.db_dump_dir, superuser, password, args) 

if __name__ == "__main__":
    main()