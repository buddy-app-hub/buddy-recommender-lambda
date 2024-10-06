import os
import requests
import dns.resolver
import random
import math

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
    interests_score = calculate_score_by_interests(elder, buddy)

    location_score = calculate_score_by_location(elder, buddy)

    availability_score = calculate_score_by_availability(elder, buddy)

    rating_score = calculate_score_by_rating(buddy)

    final_score = 0.25 * interests_score + 0.15 * location_score + 0.45 * availability_score + 0.15 * rating_score

    print(f"Final score: {final_score}")

    return final_score



def calculate_score_by_interests(elder, buddy):
    elder_interests = elder.interests
    buddy_interests = buddy.interests

    common_interests = [interest for interest in elder_interests if interest in buddy_interests]

    # Calculamos el score como la cantidad de intereses en comun sobre la cantidad total de intereses del elder
    if len(elder_interests) == 0:
        return 0

    score = (len(common_interests) / len(elder_interests)) * 100

    print(f"Interests in common: {common_interests}")
    print(f"Score by interests: {score}")

    return score


def calculate_score_by_location(elder, buddy):
    # Calculamos el score en funcion de cuan lejos esta el buddy del elder en cuanto a la distancia maxima que seteo como parametro el elder
    score = (elder.max_distance_km - buddy.distance_to_elder) / elder.max_distance_km * 100

    print(f"Elder's max distanance: {elder.max_distance_km}. Buddy distance to elder: {buddy.distance_to_elder}")
    print(f"Score by location: {score}")

    return score


def calculate_score_by_availability(elder, buddy):
    elder_availability = elder.availability
    buddy_availability = buddy.availability

    print(elder_availability)
    print(buddy_availability)

    days_of_week = ["Lunes", "Martes", "Miercoles", "Jueves", "Viernes", "Sabado", "Domingo"]
    
    total_hours = 119  # Total de horas de 7 am a 12 am en la semana
    total_score = 0  # Score total de disponibilidad
    
    # Convertimos las disponibilidades en diccionarios por día para facilitar el acceso
    elder_schedule = {day: [] for day in days_of_week}
    buddy_schedule = {day: [] for day in days_of_week}

    for slot in elder_availability:
        elder_schedule[slot['dayOfWeek']].append((slot['from'], slot['to']))

    for slot in buddy_availability:
        buddy_schedule[slot['dayOfWeek']].append((slot['from'], slot['to']))

    print(elder_schedule)
    print(buddy_schedule)

    # Evaluamos la disponibilidad por día
    for day in days_of_week:
        elder_times = elder_schedule[day]
        buddy_times = buddy_schedule[day]
        daily_score = 0  # Score diario para el día actual

        print(day)

        for e_from, e_to in elder_times:
            for b_from, b_to in buddy_times:
                # Calculamos la superposición
                overlap_start = max(e_from, b_from)
                overlap_end = min(e_to, b_to)

                overlap = (overlap_end - overlap_start) / 100 # Normalizamos a la escala de horas
                if overlap >= -2:
                    daily_score += overlap + 2

        total_score += daily_score

    
    score = fast_growth_score_exponential(total_score)

    print(f"Total score: {total_score}")
    print(f"Score by availability: {score}")

    return score


def calculate_score_by_rating(buddy):
    MAX_RATING = 5
    DEFAULT_RATING = 4 # Si no hay rating todavia

    if (buddy.global_rating):
        rating = buddy.global_rating
    else:
        rating = DEFAULT_RATING

    score = rating / MAX_RATING * 100

    print(f"Score by rating: {score}")

    return score


def fast_growth_score_exponential(total_hours_in_common, max_hours=119, L=100, k=15):
    """
    Calcula el score basado en una funcion exponencial controlada.
    Crece rapido al principio y luego se desacelera.
    
    Args:
        total_hours_in_common: El total de horas en comun entre elder y buddy.
        max_hours: La cantidad maxima de horas posibles (119).
        L: El valor limite superior para el score.
        k: controla la velocidad de crecimiento.
    
    Returns:
        Un score calculado entre 0 y 100.
    """
    if total_hours_in_common == 0:
        return 0

    # # Normalizamos las horas totales entre 0 y 1 y aplicamos la funcion exponencial
    normalized_hours = total_hours_in_common / max_hours
    score = L * (1 - math.exp(-k * normalized_hours))
    
    return score