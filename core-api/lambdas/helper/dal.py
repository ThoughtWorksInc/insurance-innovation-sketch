import json
import os
import boto3
from .logger import get_logger

logger = get_logger(__name__)

is_lambda_environment = (os.getenv('AWS_LAMBDA_FUNCTION_NAME') != None)

# AWS X-Ray support
from aws_xray_sdk.core import xray_recorder, patch_all
if is_lambda_environment:
    patch_all()

customer_table_name = 'customer'
product_table_name = 'product'

class DataAccessLayerException(Exception):

    def __init__(self, original_exception):
        self.original_exception = original_exception

# dev setup can lead to RDS "cold starts". That's an expected approach and can be turned off on production https://dev.to/dvddpl/how-to-deal-with-aurora-serverless-coldstarts-ml0
class DataAccessLayer:

    def __init__(self, database_name, db_cluster_arn, db_credentials_secrets_store_arn):
        self._rdsdata_client = boto3.client('rds-data')
        self._database_name = database_name
        self._db_cluster_arn = db_cluster_arn
        self._db_credentials_secrets_store_arn = db_credentials_secrets_store_arn

    @staticmethod
    def _xray_start(segment_name):
        if is_lambda_environment and xray_recorder:
            xray_recorder.begin_subsegment(segment_name)

    @staticmethod
    def _xray_stop():
        if is_lambda_environment and xray_recorder:
            xray_recorder.end_subsegment()

    @staticmethod
    def _xray_add_metadata(name, value):
        if is_lambda_environment and xray_recorder and xray_recorder.current_subsegment():
            return xray_recorder.current_subsegment().put_metadata(name, value)

    def execute_statement(self, sql_stmt, sql_params=[], transaction_id=None):
        parameters = f' with parameters: {sql_params}' if len(sql_params) > 0 else ''
        logger.debug(f'Running SQL statement: {sql_stmt}{parameters}')
        DataAccessLayer._xray_start('execute_statement')
        try:
            DataAccessLayer._xray_add_metadata('sql_statement', sql_stmt)
            parameters = {
                'secretArn': self._db_credentials_secrets_store_arn,
                'database': self._database_name,
                'resourceArn': self._db_cluster_arn,
                'sql': sql_stmt,
                'parameters': sql_params
            }
            if transaction_id is not None:
                parameters['transactionId'] = transaction_id
            result = self._rdsdata_client.execute_statement(**parameters)
        except Exception as e:
            logger.debug(f'Error running SQL statement (error class: {e.__class__})')
            raise DataAccessLayerException(e) from e
        else:
            DataAccessLayer._xray_add_metadata('rdsdata_executesql_result', json.dumps(result))
            return result
        finally:
           DataAccessLayer._xray_stop()

    def batch_execute_statement(self, sql_stmt, sql_param_sets, batch_size, transaction_id=None):
        parameters = f' with parameters: {sql_param_sets}' if len(sql_param_sets) > 0 else ''
        logger.debug(f'Running SQL statement: {sql_stmt}{parameters}')
        DataAccessLayer._xray_start('batch_execute_statement')
        try:
            array_length = len(sql_param_sets)
            num_batches = 1 + len(sql_param_sets)//batch_size
            results = []
            for i in range(0, num_batches):
                start_idx = i*batch_size
                end_idx = min(start_idx + batch_size, array_length)
                batch_sql_param_sets = sql_param_sets[start_idx:end_idx]
                if len(batch_sql_param_sets) > 0:
                    print(f'Running SQL statement: [batch #{i+1}/{num_batches}, batch size {batch_size}, SQL: {sql_stmt}]')
                    DataAccessLayer._xray_add_metadata('sql_statement', sql_stmt)
                    parameters = {
                        'secretArn': self._db_credentials_secrets_store_arn,
                        'database': self._database_name,
                        'resourceArn': self._db_cluster_arn,
                        'sql': sql_stmt,
                        'parameterSets': batch_sql_param_sets
                    }
                    if transaction_id is not None:
                        parameters['transactionId'] = transaction_id
                    result = self._rdsdata_client.batch_execute_statement(**parameters)
                    results.append(result)
        except Exception as e:
            logger.debug(f'Error running SQL statement (error class: {e.__class__})')
            raise DataAccessLayerException(e) from e
        else:
            DataAccessLayer._xray_add_metadata('rdsdata_executesql_result', json.dumps(result))
            return results
        finally:
           DataAccessLayer._xray_stop()

    #-----------------------------------------------------------------------------------------------
    # Customer Functions
    #-----------------------------------------------------------------------------------------------
    def find_customers(self):
        DataAccessLayer._xray_start('find_customers')
        try:
            sql = f'select customer_id, first_name, last_name, email' \
                f' from {customer_table_name}'
            response = self.execute_statement(sql)
            logger.debug(f'response {response})')
            results = [
                {
                    'customer_id': record[0]['longValue'],
                    'first_name': record[1]['stringValue'],
                    'last_name': record[2]['stringValue'],
                    'email': record[3]['stringValue']
                }
                for record in response['records']
            ]
            return results
        except DataAccessLayerException as de:
            raise de
        except Exception as e:
            raise DataAccessLayerException(e) from e
        finally:
            DataAccessLayer._xray_stop()

    def _save_customer(self, first_name, last_name, email, ignore_key_conflict=True):
        DataAccessLayer._xray_start('save_package')
        try:
            ignore = 'ignore' if ignore_key_conflict else ''
            sql_parameters = [
                {'name':'first_name', 'value':{'stringValue': first_name}},
                {'name':'last_name', 'value':{'stringValue': last_name}},
                {'name':'email', 'value':{'stringValue': email}},
            ]
            sql = f'insert {ignore} into {customer_table_name} ' \
                f' (first_name, last_name, email)' \
                f' values (:first_name, :last_name, :email)'
            response = self.execute_statement(sql, sql_parameters)
            return response
        finally:
            DataAccessLayer._xray_stop()
