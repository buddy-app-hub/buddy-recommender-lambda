import os
import requests
import dns.resolver
import random

from models import Elder, Buddy, RecommendedBuddy
import scoring

def lambda_handler(event, context):
    batch_item_failures = []
    sqs_batch_response = {}

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
    
    records = event['Records'] # Cada mensaje de la cola viene en un record
    recommended_buddies = []
    
    for record in records:
        elder_id = record['body']
        print(f'Procesando elder_id: {elder_id}')

        try:
            # Obtengo la informacion del elder, del microservicio backend
            elder = make_get_api_request(f"http://{target}:{port}/elders/{elder_id}", api_key)
            
            # Extraemos los datos relevantes del elder
            elder_data = get_relevant_elder_data(elder)
            
            # Obtengo del backend los buddies dentro del radio de preferencia del elder (donde el elder tambien este dentro del radio de preferencia de los buddies)
            buddies = make_get_api_request(f"http://{target}:{port}/elders/{elder_id}/buddies", api_key)
            
            # Calculo los scores para cada buddy
            for buddy in buddies:
                buddy_data = get_relevant_buddy_data(buddy)

                buddy_score = scoring.calculate_matching_score(elder_data, buddy_data)

                recommended_buddy = RecommendedBuddy(buddy_data.buddyid, buddy_score, buddy_data.distance_to_elder)
                recommended_buddies.append(recommended_buddy)

            # Ordenamos la lista por el score de mayor a menor
            recommended_buddies.sort(key=lambda buddy: buddy.score, reverse=True)

            # Hacemos un PATCH para actualizar los buddies recomendados del elder
            patch_recommended_buddies(f"http://{target}:{port}/elders/{elder_id}/buddies/recommended", recommended_buddies, api_key)
            
        except Exception as e:
            print(f'Unexpected error: {e}')
            batch_item_failures.append({"itemIdentifier": record['messageId']}) # Indicamos cuales items fallaron para que queden en la cola SQS y se reintente el procesamiento

    sqs_batch_response["batchItemFailures"] = batch_item_failures
    print(sqs_batch_response)

    return sqs_batch_response


def make_get_api_request(api_url, api_key):
    try:
        response = requests.get(api_url, headers={"Authorization": f"{api_key}"}, timeout=15)
        if response.status_code == 200:
            return response.json()
        else:
            raise Exception(f"API request failed: {response.status_code} - {response.text}")
    except requests.exceptions.RequestException as e:
        raise Exception(f"Request error: {str(e)}")


def patch_recommended_buddies(api_url, recommended_buddies, api_key):
    # Convertimos la lista de RecommendedBuddy a una lista de diccionarios
    recommended_buddies_data = [
        {
            "buddyID": buddy.buddyid,
            "score": buddy.score,
            "distanceToKM": buddy.distance_to_elder
        } for buddy in recommended_buddies
    ]

    try:
        response = requests.patch(
            api_url,
            json=recommended_buddies_data,
            headers={"Authorization": f"{api_key}", "Content-Type": "application/json"},
            timeout=15
        )
        
        if response.status_code != 200:
            raise Exception(f"PATCH request failed: {response.status_code} - {response.text}")
        else:
            print(f"Recommended buddies patched successfully for elder: {api_url}")
    
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
    buddyid =buddy['buddy']['firebaseUID']
    max_distance_km = buddy['buddy']['buddyProfile']['connectionPreferences']['maxDistanceKM']
    interests = {interest['name']: True for interest in buddy['buddy']['buddyProfile']['interests']}
    availability = buddy['buddy']['buddyProfile']['availability']
    global_rating = buddy['buddy']['buddyProfile']['globalRating']
    distance_to_elder = buddy['distanceToKM']
    
    buddy_instance = Buddy(buddyid, max_distance_km, interests, availability, global_rating, distance_to_elder)
    
    print(buddy_instance)
    
    return buddy_instance
