import logging
import os

import boto3
from botocore.exceptions import ClientError
from boto3.dynamodb.conditions import Key

logger = logging.getLogger(__name__)

# DynamoDB table name
QUERY_ENTITY_TABLE_NAME = 'NlqEntity'
DYNAMODB_AWS_REGION = os.environ.get('DYNAMODB_AWS_REGION')


class DynamoEntity:
    def __init__(self, entity, profile_name, entity_type, entity_count, entity_table_info, time_str):
        self.entity = entity
        self.profile_name = profile_name
        self.entity_type = entity_type
        self.entity_count = entity_count
        self.entity_table_info = entity_table_info
        self.time_str = time_str

    def to_dict(self):
        """Convert to DynamoDB item format"""
        return {
            'entity': self.entity,
            'profile_name': self.profile_name,
            'entity_type': self.entity_type,
            'entity_count': self.entity_count,
            'entity_table_info': self.entity_table_info,
            'time_str': self.time_str
        }


class DynamoEntityDao:

    def __init__(self, table_name_prefix=''):
        self.dynamodb = boto3.resource('dynamodb', region_name=DYNAMODB_AWS_REGION)
        self.table_name = table_name_prefix + QUERY_ENTITY_TABLE_NAME
        if not self.exists():
            self.create_table()
        self.table = self.dynamodb.Table(self.table_name)

    def exists(self):
        """
        Determines whether a table exists. As a side effect, stores the table in
        a member variable.

        :param table_name: The name of the table to check.
        :return: True when the table exists; otherwise, False.
        """
        try:
            table = self.dynamodb.Table(self.table_name)
            table.load()
            exists = True
        except ClientError as err:
            if err.response["Error"]["Code"] == "ResourceNotFoundException":
                exists = False
                logger.info("Table does not exist")
            else:
                logger.error(
                    "Couldn't check for existence of %s. Here's why: %s: %s",
                    self.table_name,
                    err.response["Error"]["Code"],
                    err.response["Error"]["Message"],
                )
                raise
        # else:
        #     self.table = table
        return exists

    def create_table(self):
        try:
            self.table = self.dynamodb.create_table(
                TableName=self.table_name,
                KeySchema=[
                    {"AttributeName": "profile_name", "KeyType": "HASH"},  # Partition key
                    {"AttributeName": "entity", "KeyType": "RANGE"},  # Sort key
                ],
                AttributeDefinitions=[
                    {"AttributeName": "profile_name", "AttributeType": "S"},
                    {"AttributeName": "entity", "AttributeType": "S"},
                ],
                BillingMode='PAY_PER_REQUEST',
            )
            self.table.wait_until_exists()
            logger.info(f"DynamoDB Table {self.table_name} created")
        except ClientError as err:
            print(type(err))
            logger.error(
                "Couldn't create table %s. Here's why: %s: %s",
                self.table_name,
                err.response["Error"]["Code"],
                err.response["Error"]["Message"],
            )
            raise

    def add(self, entity):
        try:
            self.table.put_item(Item=entity.to_dict())
        except Exception as e:
            logger.error("add log entity is error {}", e)

    def update(self, entity):
        self.table.put_item(Item=entity.to_dict())

    def get_entity(self, profile_name: str, entity: str):
        """Read an entity from the DynamoDB table"""
        try:
            response = self.table.get_item(Key={'profile_name': profile_name, 'entity': entity})
            item = response.get('Item')
            if item:
                return DynamoEntity(**item)
            else:
                logger.info(f"Entity not found: {entity}")
                return None
        except ClientError as e:
            logger.error(f"Couldn't read entity {entity}. Here's why: {e}")
            return None

    def update_entity(self, entity: DynamoEntity):
        """Update an existing entity in the DynamoDB table"""
        try:
            response = self.table.update_item(
                Key={'profile_name': entity.profile_name, 'entity': entity.entity},
                UpdateExpression="set entity_type=:t, entity_count=:c, entity_table_info=:i, time_str=:s",
                ExpressionAttributeValues={
                    ':t': entity.entity_type,
                    ':c': entity.entity_count,
                    ':i': entity.entity_table_info,
                    ':s': entity.time_str
                },
                ReturnValues="UPDATED_NEW"
            )
            logger.info(f"Updated entity: {entity.entity}")
            return True
        except ClientError as e:
            logger.error(f"Couldn't update entity {entity.entity}. Here's why: {e}")
            return False

    def delete_entity(self, profile_name: str, entity: str):
        """Delete an entity from the DynamoDB table"""
        try:
            self.table.delete_item(
                Key={'profile_name': profile_name, 'entity': entity}
            )
            logger.info(f"Deleted entity: {entity}")
            return True
        except ClientError as e:
            logger.error(f"Couldn't delete entity {entity}. Here's why: {e}")
            return False

