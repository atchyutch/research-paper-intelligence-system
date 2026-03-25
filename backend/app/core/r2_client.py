import boto3
from botocore.exceptions import ClientError
from fastapi import HTTPException, status


def get_r2_client(r2_endpoint:  str, access_key:str, secret_key:str):
    try:
        client_retrieved = boto3.client(
            "s3",
            endpoint_url = r2_endpoint,
            aws_access_key_id = access_key,
            aws_secret_access_key = secret_key,
            region_name = "us-east-1"
        )
    except ClientError as e:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail = str(e))

    return client_retrieved