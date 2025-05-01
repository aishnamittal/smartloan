# import os
# import shutil
# import uuid
# from fastapi import APIRouter

# router = APIRouter()

# UPLOAD_FOLDER = os.getenv("UPLOAD_FOLDER", "uploads")
# PROCESSED_FOLDER = os.getenv("PROCESSED_FOLDER", "processed")


# def generate_5_digit_uuid():
#     """Generate a unique 5-digit UUID."""
#     return str(uuid.uuid4().int)[:5]

# def move_images():
#     """Move images from uploads to a new processed folder with a 5-digit UUID."""
#     if not os.path.exists(UPLOAD_FOLDER):
#         return {"error": f"Uploads folder '{UPLOAD_FOLDER}' does not exist!"}

#     if not os.path.exists(PROCESSED_FOLDER):
#         os.makedirs(PROCESSED_FOLDER)

#     new_folder_name = generate_5_digit_uuid()
#     new_processed_folder = os.path.join(PROCESSED_FOLDER, new_folder_name)
#     os.makedirs(new_processed_folder)

#     moved_files = []
#     for file_name in os.listdir(UPLOAD_FOLDER):
#         file_path = os.path.join(UPLOAD_FOLDER, file_name)

#         if os.path.isfile(file_path) and file_name.lower().endswith((".png", ".jpg", ".jpeg", ".gif", ".bmp", ".tiff")):
#             try:
#                 new_file_path = os.path.join(new_processed_folder, file_name)
#                 shutil.move(file_path, new_file_path)
#                 moved_files.append(file_name)
#             except Exception as e:
#                 return {"error": f"Failed to move {file_name}: {e}"}

#     return {"message": "Images processed successfully!", "folder": new_folder_name, "moved_files": moved_files}

# @router.post("/process-images/")
# def process_images():
#     """API endpoint to process images from uploads to processed."""
#     result = move_images()
#     return result



# # from fastapi import APIRouter, HTTPException, Request
# # import os
# # import shutil
# # import random

# # router = APIRouter()

# # UPLOAD_FOLDER = os.getenv("UPLOAD_FOLDER", "uploads")
# # PROCESSED_FOLDER = os.getenv("PROCESSED_FOLDER", "processed")

# # # Temporary store for latest UUID
# # latest_uuid = None

# # @router.get("/generate-uuid/")
# # async def generate_uuid():
# #     """Generates a random 5-digit UUID and returns it."""
# #     global latest_uuid
# #     latest_uuid = str(random.randint(10000, 99999))  # Generate 5-digit UUID
# #     return {"uuid": latest_uuid}


# # @router.post("/store-files/")
# # async def store_files(request: Request):
# #     """Moves image files from UPLOAD_FOLDER to a subdirectory in PROCESSED_FOLDER using the provided UUID."""

# #     global latest_uuid

# #     # Read request body safely
# #     body = await request.body()
# #     if not body:
# #         raise HTTPException(status_code=400, detail="Request body is empty!")

# #     try:
# #         data = await request.json()
# #         user_uuid = data.get("uuid")

# #         if not user_uuid or not user_uuid.isdigit() or len(user_uuid) != 5:
# #             raise HTTPException(status_code=400, detail="UUID must be a 5-digit number.")

# #         # Ensure UUID matches latest generated one
# #         if latest_uuid is None or latest_uuid != user_uuid:
# #             raise HTTPException(status_code=400, detail="UUID mismatch. Please generate a valid UUID first.")

# #         # Create folder for processed images
# #         new_processed_folder = os.path.join(PROCESSED_FOLDER, user_uuid)
# #         os.makedirs(new_processed_folder, exist_ok=True)

# #         moved_files = []
# #         for file_name in os.listdir(UPLOAD_FOLDER):
# #             file_path = os.path.join(UPLOAD_FOLDER, file_name)

# #             if os.path.isfile(file_path) and file_name.lower().endswith((".png", ".jpg", ".jpeg")):
# #                 new_file_path = os.path.join(new_processed_folder, file_name)
# #                 shutil.move(file_path, new_file_path)
# #                 moved_files.append(file_name)

# #         return {"message": "Files stored successfully!", "uuid": user_uuid, "moved_files": moved_files}

# #     except Exception as e:
# #         raise HTTPException(status_code=500, detail=f"Error storing files: {str(e)}")

import os
import shutil
from fastapi import APIRouter, Query
from fastapi.middleware.cors import CORSMiddleware

router = APIRouter()

UPLOAD_FOLDER = os.getenv("UPLOAD_FOLDER", "uploads")
PROCESSED_FOLDER = os.getenv("PROCESSED_FOLDER", "processed")

@router.get("/finalize-process/")
def finalize_process(uuid: str = Query(...)):
    target_folder = os.path.join(PROCESSED_FOLDER, uuid)
    os.makedirs(target_folder, exist_ok=True)

    for filename in os.listdir(UPLOAD_FOLDER):
        source = os.path.join(UPLOAD_FOLDER, filename)
        if os.path.isfile(source):
            shutil.move(source, os.path.join(target_folder, filename))

    return {"status": "success", "message": f"Files moved to {target_folder}"}
