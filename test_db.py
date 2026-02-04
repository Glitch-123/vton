from db.models import create_tables
from db.database import get_connection

# 1️⃣ Create table
create_tables()

# 2️⃣ Connect to DB
conn = get_connection()
cursor = conn.cursor()

# 3️⃣ Insert dummy row
cursor.execute("""
INSERT INTO body_metrics 
(shoulder_width, torso_length, chest_waist_ratio, hip_waist_ratio)
VALUES (?, ?, ?, ?)
""", (8.0, 6.0, 0.5, 0.75))

conn.commit()

# 4️⃣ Fetch and print all rows
cursor.execute("SELECT * FROM body_metrics")
rows = cursor.fetchall()
print("📦 Stored Body Profiles:")
for row in rows:
    print(row)

conn.close()
