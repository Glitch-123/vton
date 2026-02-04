# core_fit_logic.py

from math import sqrt

def distance(p1, p2):
    """Calculate distance between two points (x, y)"""
    return sqrt((p1[0]-p2[0])**2 + (p1[1]-p2[1])**2)

def calculate_body_ratios(joints):
    """
    joints: dict of 7 points: NECK, LEFT_SHOULDER, RIGHT_SHOULDER, CHEST, WAIST, LEFT_HIP, RIGHT_HIP
    returns body ratios as numbers
    """
    shoulder_width = distance(joints["LEFT_SHOULDER"], joints["RIGHT_SHOULDER"])
    torso_length = distance(joints["NECK"], joints["WAIST"])
    chest_to_waist_ratio = distance(joints["CHEST"], joints["WAIST"]) / torso_length
    hip_to_waist_ratio = distance(joints["LEFT_HIP"], joints["RIGHT_HIP"]) / shoulder_width
    
    return {
        "shoulder_width": shoulder_width,
        "torso_length": torso_length,
        "chest_to_waist_ratio": chest_to_waist_ratio,
        "hip_to_waist_ratio": hip_to_waist_ratio
    }

def fit_cloth(body_ratios, size_chart, selected_size, fit_type):
    """Scale cloth dimensions based on body ratios and fit type"""
    ease_multipliers = {'slim': 1.02, 'regular': 1.08, 'baggy': 1.18}
    ease = ease_multipliers.get(fit_type, 1.08)
    
    chest_target = size_chart[selected_size]['chest'] * ease
    waist_target = size_chart[selected_size]['waist'] * ease
    
    chest_scale = chest_target / body_ratios["chest_to_waist_ratio"]
    waist_scale = waist_target / body_ratios["hip_to_waist_ratio"]
    
    return {"chest_scale": chest_scale, "waist_scale": waist_scale}
