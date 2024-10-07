import json
import os
import boto3
import requests
import dns.resolver
import random

sqs_client = boto3.client('sqs')

def lambda_handler(event, context):
    queue_url = os.getenv('SQS_QUEUE_URL')
    api_key = os.getenv('BACKEND_API_KEY_FOR_LAMBDA')

    if not api_key or not queue_url:
        return {
            'statusCode': 500,
            'body': 'Faltan variables de entorno'
        }

    # Realizamos una consulta DNS de tipo SRV para obtener la direccion del microservicio backend
    try:
        answers = dns.resolver.resolve('buddy-service.buddy-namespace', 'SRV')
    except dns.exception.DNSException as e:
        return {
            'statusCode': 500,
            'body': f'Error resolviendo el DNS SRV: {str(e)}'
        }

    # Extraemos el host y puerto del primer resultado
    srv_record = random.choice(answers) # Hacemos un random de todos los hosts devueltos para balancear la carga
    target = str(srv_record.target).rstrip('.')  # Nombre del host
    port = srv_record.port  # Puerto asociado
    
    try:
        # Obtengo todos los elders del microservicio backend
        elders = make_get_api_request(f"http://{target}:{port}/elders", api_key)
    
        if response.status_code != 200:
            return {
                'statusCode': response.status_code,
                'body': f"Error al consultar el microservicio: {response.text}"
            }
        
    except Exception as e:
        return {
            'statusCode': 500,
            'body': f"Error al hacer el request a backend: {str(e)}"
        }
    
    # Iteramos sobre los elders y encolamos el elder_id
    for elder in elders:
        elder_id = elder['firebaseUID']
        try:
            # Encolamos el elder_id en el SQS
            response = sqs_client.send_message(
                QueueUrl=queue_url,
                MessageBody=json.dumps(elder_id)
            )
            print(f"Elder encolado con elder_id: {elder_id}, MessageId: {response['MessageId']}")
            
        except Exception as e:
            print(f"Error al encolar elder_id {elder_id}: {str(e)}")
    
    return {
        'statusCode': 200,
        'body': 'Todos los elders fueron encolados en SQS'
    }


def make_get_api_request(api_url, api_key):
    try:
        response = requests.get(api_url, headers={"Authorization": f"{api_key}"}, timeout=15)
        if response.status_code == 200:
            return response.json()
        else:
            raise Exception(f"API request failed: {response.status_code} - {response.text}")
    except requests.exceptions.RequestException as e:
        raise Exception(f"Request error: {str(e)}")