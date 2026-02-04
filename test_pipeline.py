from pipeline.body_pipeline import process_and_store

fake_joints = {
    "NECK": (0.5, 0.1),
    "LEFT_SHOULDER": (0.4, 0.2),
    "RIGHT_SHOULDER": (0.6, 0.2),
    "CHEST": (0.5, 0.3),
    "WAIST": (0.5, 0.5),
    "LEFT_HIP": (0.45, 0.6),
    "RIGHT_HIP": (0.55, 0.6)
}

ratios = process_and_store(fake_joints)
print("Stored ratios:", ratios)
