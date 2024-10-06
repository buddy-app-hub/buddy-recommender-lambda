class Elder:
    def __init__(self, max_distance_km, interests, availability):
        self.max_distance_km = max_distance_km
        self.interests = interests
        self.availability = availability
    
    def __repr__(self):
        return f"Elder(max_distance_km={self.max_distance_km}, interests={self.interests}, availability={self.availability})"


class Buddy:
    def __init__(self, buddyid, max_distance_km, interests, availability, global_rating, distance_to_elder):
        self.buddyid = buddyid
        self.max_distance_km = max_distance_km
        self.interests = interests
        self.availability = availability
        self.global_rating = global_rating
        self.distance_to_elder = distance_to_elder
    
    def __repr__(self):
        return f"Buddy(buddyid={self.buddyid}, max_distance_km={self.max_distance_km}, interests={self.interests}, availability={self.availability}, global_rating={self.global_rating}, distance_to_elder={self.distance_to_elder})"


class RecommendedBuddy:
    def __init__(self, buddyid, score, distance_to_elder):
        self.buddyid = buddyid
        self.score = score
        self.distance_to_elder = distance_to_elder
    
    def __repr__(self):
        return f"RecommendedBuddy(buddyid={self.buddyid}, score={self.score}, distance_to_elder={self.distance_to_elder})"
