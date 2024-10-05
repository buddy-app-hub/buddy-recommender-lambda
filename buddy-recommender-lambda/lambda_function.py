import os
import requests
import dns.resolver

def lambda_handler(event, context):
    api_key = os.getenv('BACKEND_API_KEY_FOR_LAMBDA')

    if not api_key:
        return {
            'statusCode': 500,
            'body': 'Falta la clave API en las variables de entorno'
        }
    
    # Realizamos una consulta DNS de tipo SRV para obtener la direccion del microservicio backend
    answers = dns.resolver.resolve('buddy-service.buddy-namespace', 'SRV')

    # Extraemos el host y puerto del primer resultado
    # TODO: evaluar de hacer random para distribuir carga
    srv_record = answers[0]
    target = str(srv_record.target).rstrip('.')  # Nombre del host
    port = srv_record.port  # Puerto asociado
    
    records = event['Records']
    results = []
    
    for record in records:
        elder_id = record['body']
        print(f'Procesando elder_id: {elder_id}')
        
        api_url = f"http://{target}:{port}/elders/{elder_id}/buddies"
                
        try:
            response = requests.get(api_url, headers={"Authorization": f"{api_key}"})

            if response.status_code == 200:
                data = response.json()
                results.append({
                    'elder_id': elder_id,
                    'statusCode': 200,
                    'body': data
                })
            else:
                results.append({
                    'elder_id': elder_id,
                    'statusCode': response.status_code,
                    'body': f'Error al llamar la API: {response.text}'
                })
            print("finished item")
        except requests.exceptions.RequestException as e:
            results.append({
                'elder_id': elder_id,
                'statusCode': 500,
                'body': f'Error en la solicitud: {str(e)}'
            })
        except Exception as e:
            print(f'Unexpected error: {e}')
            results.append({
                'elder_id': elder_id,
                'statusCode': 500,
                'body': f'Unexpected error: {str(e)}'
            })
    
    return {
        'statusCode': 200,
        'body': results
    }
