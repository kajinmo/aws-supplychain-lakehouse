1) mudar p pydantic v2
https://github.com/pydantic/pydantic/issues/6557

2) dynamodb: provisioned x on demand
provisioned
```python
def lambda_handler(event, context):
    client = boto3.client('dynamodb')
    
    # Mudar para PROVISIONED com alta capacidade
    response = client.update_table(
        TableName='seu-projeto-operational',
        BillingMode='PROVISIONED',
        ProvisionedThroughput={
            'ReadCapacityUnits': 10,
            'WriteCapacityUnits': 5000  # O "talo" para a carga
        }
    )
    
    return { 'status': 'Updating to Provisioned' }

    import boto3
```
on demand
```python
def lambda_handler(event, context):
    client = boto3.client('dynamodb')
    
    # Voltar para PAY_PER_REQUEST (On-Demand)
    response = client.update_table(
        TableName='seu-projeto-operational',
        BillingMode='PAY_PER_REQUEST'
    )
    
    return { 'status': 'Returning to On-Demand' }
```