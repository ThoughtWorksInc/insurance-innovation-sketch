from helper.dal import *
from helper.lambdautils import *
from helper.logger import get_logger

logger = get_logger(__name__)

database_name = os.getenv('DB_NAME')
db_cluster_arn = os.getenv('DB_CLUSTER_ARN')
db_credentials_secrets_store_arn = os.getenv('DB_CRED_SECRETS_STORE_ARN')

dal = DataAccessLayer(database_name, db_cluster_arn, db_credentials_secrets_store_arn)

#-----------------------------------------------------------------------------------------------
# Input Validation
#-----------------------------------------------------------------------------------------------
def validate_path_parameters(event):
    if key_missing_or_empty_value(event, 'pathParameters'):
        raise ValueError('Invalid input - missing aws_instance_id as part of path parameters')
    if key_missing_or_empty_value(event['pathParameters'], 'aws_instance_id'):
        raise ValueError('Invalid input - missing aws_instance_id as part of path parameters')
    return event['pathParameters']['aws_instance_id']

#-----------------------------------------------------------------------------------------------
# Lambda Entrypoint
#-----------------------------------------------------------------------------------------------
def handler(event, context):
    try:
        logger.info(f'Event received: {context}')
        results = dal._save_customer("first", "last", "email")
        output = {
            'record': results,
            'record_found': len(results) > 0
        }
        logger.debug(f'Output: {output}')
        return success(output)
    except Exception as e:
        return handle_error(e)