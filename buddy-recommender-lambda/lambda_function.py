import os
import requests
import dns.resolver
import random

from models import Elder, Buddy

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
            elder_data = get_relevant_elder_data(elder)
            
            # Obtengo los buddies dentro del radio de preferencia del elder (donde el elder tambien este dentro del radio de preferencia de los buddies)
            buddies = make_api_request(f"http://{target}:{port}/elders/{elder_id}/buddies", api_key)
            
            for buddy in buddies:
                buddy_data = get_relevant_buddy_data(buddy)

                buddy_score = calculate_matching_score(elder_data, buddy_data)

            

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
    max_distance_km = elder['elderProfile']['connectionPreferences']['maxDistanceKM']
    interests = {interest['name']: True for interest in elder['elderProfile']['interests']}
    availability = elder['elderProfile']['availability']
    
    elder_instance = Elder(max_distance_km, interests, availability)
    
    print(elder_instance)
    
    return elder_instance


def get_relevant_buddy_data(buddy):
    max_distance_km = buddy['buddy']['buddyProfile']['connectionPreferences']['maxDistanceKM']
    interests = {interest['name']: True for interest in buddy['buddy']['buddyProfile']['interests']}
    availability = buddy['buddy']['buddyProfile']['availability']
    global_rating = buddy['buddy']['buddyProfile']['globalRating']
    distance_to_elder = buddy['distanceToKM']
    
    buddy_instance = Buddy(max_distance_km, interests, availability, global_rating, distance_to_elder)
    
    print(buddy_instance)
    
    return buddy_instance


def calculate_matching_score(elder, buddy):
    elder_interests = elder.interests
    buddy_interests = buddy.interests

    common_interests = [interest for interest in elder_interests if interest in buddy_interests]

    # Calculamos el score como la cantidad de intereses en comun sobre la cantidad total de intereses del elder
    if len(elder_interests) == 0:
        return 0

    matching_score = (len(common_interests) / len(elder_interests)) * 100

    print(f"Intereses en común: {common_interests}")
    print(f"Matching score: {matching_score}")

    return matching_score

