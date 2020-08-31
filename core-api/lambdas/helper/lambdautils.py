import json
import uuid
from .logger import get_logger
from .dal import DataAccessLayerException

logger = get_logger(__name__)

def key_missing_or_empty_value(d, key):
    return not key in d or not d[key]

def success(output):
    return {
        'statusCode': 200,
        'body': json.dumps(output)
}

def error(error_code, error):
    return {
        'statusCode': error_code,
        'body': json.dumps({
            'error_message': error
        })
    }

def handle_error(e):
    client_err_code = uuid.uuid4()
    client_error_msg = f'(error_code: {client_err_code})'
    if isinstance(e, ValueError):
        client_error_msg = f'{client_error_msg} - Error while validating input parameters: {e}'
        logger.error(f'[client error code: {client_err_code}, client error message: {client_error_msg}, internal error (ValueError)]')
        return error(400, client_error_msg)
    elif isinstance(e, DataAccessLayerException):
        client_error_msg = f'{client_error_msg} - Error while interacting with the database'
        logger.error(f'[client error code: {client_err_code}, client error message: {client_error_msg}, internal error (DataAccessLayerException): {e.original_exception}]')
        return error(400, client_error_msg)
    client_error_msg = f'{client_error_msg} - Unexpected error. Please contact the software vendor.'
    logger.error(f'[client error code: {client_err_code}, client error message: {client_error_msg}, internal error (Exception): {e}]')
    return error(400, client_error_msg)