import os

print("\n👕 VIRTUAL TRY-ON SYSTEM\n")
print("1 → Use Camera")
print("2 → Upload Image\n")

choice = input("Select option (1/2): ").strip()

if choice == "1":
    os.system("python desktop/capture_image.py")
    os.system("python desktop/process_image.py captured")

elif choice == "2":
    os.system("python desktop/process_image.py uploaded")

else:
    print("❌ Invalid choice")
