import math

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