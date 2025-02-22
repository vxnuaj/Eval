import logging
import re
import traceback
import psycopg2
import sys
from vllm import LLM, SamplingParams

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler('../../logs/eval.log', mode='a'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class ExecSQL:
    @classmethod
    def execute_sql(cls, cursor, query, alter=False):
        """execute SQL using an existing cursor."""
        try:
            cursor.execute(query)
            results = cursor.fetchall() if not alter else None
            return True, results
        except Exception as e:
            if alter:
                return False, 'alter_error'
            logger.error("SQL Execution Error: %s", e)
            logger.error(traceback.format_exc())
            return False, "None"

    @classmethod
    def model_execute_sql(cls, cursor, query):
        try:
            cursor.execute(query)
            results = cursor.fetchall()
            return True, results
        except Exception as e:
            error_message = str(e)
            match = re.search(r"SyntaxError.*?(LINE .*)", error_message, re.DOTALL)
            sql_error = match.group(1) if match else error_message
            logger.error("Model SQL Execution Error: %s", sql_error)
            logger.error(traceback.format_exc())
            return False, sql_error

    @classmethod
    def process_queries(cls, model, n, sample, db_name, user, password, sampling_params):
        """
        process queries in batch using a single db conn.

        :param n: Number of steps for the LLM.
        :param sample: Dictionary containing instance_id, query, etc.
        """
        try:
            conn = psycopg2.connect(dbname=db_name, user=user, password=password)
            cursor = conn.cursor()

            instance_id = sample['instance_id']
            selected_database = sample['selected_database']
            query = sample['query']
            error_sql = sample['error_sql']
            preprocess_sql = sample['preprocess_sql']
            clean_up_sql = sample['clean_up_sql']

            payload = (
                "Think step by step about how to correct the SQL query.\n\n"
                "Only output the corrected SQL query. Do not include any explanations, reasoning, or extra text.\n\n"
                "Database: {}\n\nQuery: {}\n\nErroneous PSQL Query:\n{}\n"
                .format(selected_database, query, "\n".join(error_sql))
            )

            if preprocess_sql:
                if not isinstance(preprocess_sql, list):
                    raise ValueError(f"Instance {instance_id}: 'preprocess_sql' is not a list.")
                for ppsql in preprocess_sql:
                    logger.info("Instance %s: Preprocessing SQL: %s", instance_id, ppsql)
                    status, _ = cls.execute_sql(cursor, ppsql, alter=True)
                    if status:
                        logger.info("Instance %s: Preprocessing succeeded.", instance_id)
                    else:
                        logger.error("Instance %s: Preprocessing failed. Rolling back.", instance_id)
                        conn.rollback()

            gt_file = f'../../data/bc-1-fexp/data/gtout/query_{instance_id}_output.csv'
            with open(gt_file, 'r') as f:
                gt_out = f.read()

            for step in range(n):
                logger.info(f"Input to LLM: {payload}")
                response = model.generate(prompts=payload, sampling_params=sampling_params)
                if not isinstance(response, str):
                    response = response[0].outputs[0].text
                    logger.info(f"Response from LLM: {response}")
                    if not isinstance(response, str):
                        raise ValueError(f"Instance {instance_id}: LLM response is not a string.")

                pattern = re.compile(r"(?s).*<\/think>\s*(SELECT\s+.*?)(?:\n\s*\n|$)", re.IGNORECASE)
                match = pattern.search(response)
                if match:
                    response_sql = match.group(1).strip()
                    logger.info("Instance %s: Extracted SQL: %s", instance_id, response_sql)
                else:
                    logger.error("Instance %s: No SQL query found in LLM response.", instance_id)
                    continue

                logger.info("Instance %s: Executing generated SQL.", instance_id)
                status, results = cls.model_execute_sql(cursor, response_sql)
                if status:
                    logger.info("Instance %s: SQL executed successfully.", instance_id)
                else:
                    logger.error("Instance %s: SQL execution failed.", instance_id)

                if results == gt_out:
                    logger.info("Instance %s: Correct output achieved.", instance_id)
                    return True, response
                else:
                    logger.info("Instance %s: Incorrect output at step %d.", instance_id, step)
                    payload += f"\nResults from previous correction attempt at step {step}:\n{results}"

            if clean_up_sql:
                for csql in clean_up_sql:
                    logger.info("Instance %s: Cleaning up SQL: %s", instance_id, csql)
                    status, _ = cls.execute_sql(cursor, csql, alter=True)
                    if status:
                        logger.info("Instance %s: Cleanup succeeded.", instance_id)
                    else:
                        logger.error("Instance %s: Cleanup failed. Rolling back.", instance_id)
                        conn.rollback()
            else:
                logger.info("Instance %s: No cleanup SQL provided.", instance_id)

            conn.commit()
            cursor.close()
            conn.close()
            return True, response

        except Exception as e:
            inst = sample.get('instance_id', 'unknown')
            logger.error("Instance %s: Database connection error: %s", inst, e)
            logger.error(traceback.format_exc())
            if 'conn' in locals() and conn:
                conn.close()
            sys.exit(1)


class Model:
    def __init__(self, model_name: str, tokenizer: str, sampling_params: dict, n=15):
        """
        n: max steps.
        """
        self.model_name = model_name
        self.tokenizer = tokenizer
        self.sampling_params = SamplingParams(**sampling_params)
        self.n = n

    def load_model(self):
        self.model = LLM(model=self.model_name, tokenizer=self.tokenizer)

    def generate(self, sample, db_name, user, password):
        success, response = ExecSQL.process_queries(
            model=self.model,
            n=self.n,
            sample=sample,
            db_name=db_name,
            user=user,
            password=password,
            sampling_params=self.sampling_params
        )
        return success, response
