import math

# Deben sumar 1
CHEMISTRY_WEIGHT = 0.30
LOCATION_WEIGHT = 0.30
AVAILABILITY_WEIGHT = 0.40

TOTAL_WEEK_HOURS_FOR_MEETINGS = 119  # Total de horas de 7 am a 12 am en la semana

MAX_RATING = 5
DEFAULT_RATING = 4 # Si no hay rating todavia

DAYS_OF_WEEK = ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado", "Domingo"]

# La cantidad de horas que permitimos para considerar horas cercanas como parcialmente coincidentes, incluso si no se superponen
# Ej. dia lunes: buddy puede de 2 a 4 y el elder de 5 a 8. No se superponen por 1 hora, que como es menor al TOLERANCE_HOURS, suma TOLERANCE_HOURS - desfasaje al score
TOLERANCE_HOURS = 2 


# Calcula un matching score de 0 a 100 entre el buddy y el elder, ponderando distintos aspectos. El rating afecta el score general (es decir, el score final es el producto del score con rating/MAX_RATING)
def calculate_matching_score(elder, buddy):
    chemistry_score = calculate_score_by_chemistry(elder, buddy)

    location_score = calculate_score_by_location(elder, buddy)

    availability_score = calculate_score_by_availability(elder, buddy)

    rating_score = calculate_score_by_rating(buddy)

    final_score = (CHEMISTRY_WEIGHT * chemistry_score + LOCATION_WEIGHT * location_score + AVAILABILITY_WEIGHT * availability_score) * rating_score

    print(f"Final score: {final_score}")

    return final_score


# Chemistry define cuan bien ambas personas se podrian llevar en base a sus personalidades. Por el momento, solo se toman en cuenta los intereses en comun
def calculate_score_by_chemistry(elder, buddy):
    elder_interests = elder.interests
    buddy_interests = buddy.interests

    common_interests = [interest for interest in elder_interests if interest in buddy_interests]

    # Calculamos el score como la cantidad de intereses en comun sobre la cantidad total de intereses del elder
    if len(elder_interests) == 0:
        return 0

    score = (len(common_interests) / len(elder_interests)) * 100

    print(f"Interests in common: {common_interests}")
    print(f"Score by chemistry: {score}")

    return score


# Calculamos el score en funcion de cuan lejos esta el buddy del elder en cuanto a la distancia maxima que seteo como parametro el elder
def calculate_score_by_location(elder, buddy):
    score = (elder.max_distance_km - buddy.distance_to_elder) / elder.max_distance_km * 100

    print(f"Elder's max distanance: {elder.max_distance_km}. Buddy distance to elder: {buddy.distance_to_elder}")
    print(f"Score by location: {score}")

    return score


# Calcula un score para la disponibilidad horaria en base a cuantas horas tienen en comun en la semana sus tiempos libres. Si no coinciden por menos de 2 horas, igual se da un score bajo para ser menos estrictos
def calculate_score_by_availability(elder, buddy):
    total_score = 0
    
    elder_schedule = {day: [] for day in DAYS_OF_WEEK}
    buddy_schedule = {day: [] for day in DAYS_OF_WEEK}

    for slot in elder.availability:
        elder_schedule[slot['dayOfWeek']].append((slot['from'], slot['to']))

    for slot in buddy.availability:
        buddy_schedule[slot['dayOfWeek']].append((slot['from'], slot['to']))

    print(elder_schedule)
    print(buddy_schedule)

    # Evaluamos la disponibilidad por día
    for day in DAYS_OF_WEEK:
        elder_times = elder_schedule[day]
        buddy_times = buddy_schedule[day]
        daily_score = 0

        for e_from, e_to in elder_times:
            for b_from, b_to in buddy_times:
                # Calculamos la superposicion
                overlap_start = max(e_from, b_from)
                overlap_end = min(e_to, b_to)

                overlap = (overlap_end - overlap_start) / 100 # Normalizamos a la escala de horas
                if overlap >= - TOLERANCE_HOURS:
                    daily_score += overlap + TOLERANCE_HOURS

        total_score += daily_score

    
    score = fast_growth_score_exponential(total_score)

    print(f"Total score: {total_score}")
    print(f"Score by availability: {score}")

    return score


def calculate_score_by_rating(buddy):
    if (buddy.global_rating):
        rating = buddy.global_rating
    else:
        rating = DEFAULT_RATING

    score = rating / MAX_RATING * 100

    print(f"Score by rating: {score}")

    return score


# Calcula el score entre 0 y 100 basado en una funcion exponencial controlada. Crece rapido al principio y luego se desacelera
# La idea es que no necesiten tener muchisimas horas en comun para tener un score alto
def fast_growth_score_exponential(total_hours_in_common):
    L=100 # limite superior para el score
    k=15 # controla la velocidad de crecimiento.

    if total_hours_in_common == 0:
        return 0

    # Normalizamos las horas totales entre 0 y 1 y aplicamos la funcion exponencial
    normalized_hours = total_hours_in_common / TOTAL_WEEK_HOURS_FOR_MEETINGS
    score = L * (1 - math.exp(-k * normalized_hours))
    
    return score