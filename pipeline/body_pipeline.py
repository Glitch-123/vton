from core.core_fit_logic import calculate_body_ratios
from db.database import get_connection
from db.models import create_tables

def process_and_store(joints):
    create_tables()  # 👈 VERY IMPORTANT

    ratios = calculate_body_ratios(joints)

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
    INSERT INTO body_metrics
    (shoulder_width, torso_length, chest_waist_ratio, hip_waist_ratio)
    VALUES (?, ?, ?, ?)
    """, (
        ratios["shoulder_width"],
        ratios["torso_length"],
        ratios["chest_to_waist_ratio"],
        ratios["hip_to_waist_ratio"]
    ))

    conn.commit()
    conn.close()

    return ratios
