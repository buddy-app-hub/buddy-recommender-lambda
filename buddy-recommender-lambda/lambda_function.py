import os
import requests
import dns.resolver
import random

def lambda_handler(event, context):
    api_key = os.getenv('BACKEND_API_KEY_FOR_LAMBDA')

    if not api_key:
        return {
            'statusCode': 500,
            'body': 'Falta la clave API en las variables de entorno'
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
    
    records = event['Records']
    results = []
    
    for record in records:
        elder_id = record['body']
        print(f'Procesando elder_id: {elder_id}')

        try:
            # Obtengo la informacion del elder
            elder = make_api_request(f"http://{target}:{port}/elders/{elder_id}", api_key)
            
            # Extraemos los datos relevantes del elder
            get_relevant_elder_data(elder)
            
            # Obtengo los buddies dentro del radio de preferencia del elder (donde el elder tambien este dentro del radio de preferencia de los buddies)
            buddies = make_api_request(f"http://{target}:{port}/elders/{elder_id}/buddies", api_key)
            
            print(buddies)

            results.append({
                'elder_id': elder_id,
                'statusCode': 200,
                'buddies': buddies
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

def make_api_request(api_url, api_key):
    try:
        response = requests.get(api_url, headers={"Authorization": f"{api_key}"}, timeout=15)
        if response.status_code == 200:
            return response.json()
        else:
            raise Exception(f"API request failed: {response.status_code} - {response.text}")
    except requests.exceptions.RequestException as e:
        raise Exception(f"Request error: {str(e)}")

def get_relevant_elder_data(elder):
    elder_max_distance_km = elder['elderProfile']['connectionPreferences']['maxDistanceKM']

    # Intereses como diccionario (asignar valor True por defecto a cada interés para luego compararlos fácilmente)
    elder_interests = {interest['name']: True for interest in elder['elderProfile']['interests']}

    # Disponibilidad
    elder_availability = elder['elderProfile']['availability']

    # Mostrar lo extraído
    print(f'Max Distance (KM): {elder_max_distance_km}')
    print(f'Interests: {elder_interests}')
    print(f'Availability: {elder_availability}')

    return elder_max_distance_km, elder_interests, elder_availability

