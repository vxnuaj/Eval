import argparse
import logging
import json
import sys
import os
import csv

from model import Model
from data_utils import load_dataset

logging.basicConfig(
        level = logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers = [
            logging.FileHandler('../../logs/eval.log', mode = 'a'),
            logging.StreamHandler()
        ]    
        )

logger = logging.getLogger(__name__)

parser = argparse.ArgumentParser()

parser.add_argument('--model_name', type=str, required=True)
parser.add_argument('--tokenizer', type=str, required=True)
parser.add_argument('--temperature', type=float, default = .7)
parser.add_argument('--top_p', type=float, default = .9)
parser.add_argument('--max_tokens', type=int, default = 10000)

args = parser.parse_args()

data = load_dataset('../../data/bc-1-fexp/data/input_filtered.jsonl') # NOTE: this is a list of dictionaries

############## init model ################

sampling_params = {
    'temperature': args.temperature,
    'top_p': args.top_p,
    'max_tokens': args.max_tokens
}

model = Model(
    model_name = args.model_name,
    tokenizer = args.tokenizer,
    sampling_params = sampling_params,
    n = 15
)

model.load_model()

dataset = []

with open("../psql_db/postgres_cred.json", 'r') as file:
    cred = json.load(file) 


for sample in data:
    
    instance_id = sample['instance_id'] 
    
    status, response = model.generate(
        sample,
        db_name = cred['db_name'],
        user = cred['super_user'],
        password = cred['password']
        )

    output_filename = f"../../data/bc-1-fexp/data/responses/response_{instance_id}.csv"
    
    os.makedirs(os.path.dirname(output_filename), exist_ok=True)

    if status:
        try:
            with open(output_filename, 'w', newline='') as file:
                writer = csv.writer(file)
                writer.writerow(['instance_id', 'response']) 
                writer.writerow([instance_id, response])  
                
            logger.info(f"Response for instance {instance_id} saved to {output_filename}")
        except Exception as e:
            logger.error(f"Error saving response for instance {instance_id}: {e}")
            sys.exit(1)