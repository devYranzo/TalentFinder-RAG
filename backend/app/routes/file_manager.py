from fastapi import APIRouter, UploadFile, File, Form
from services.file_manager import file_manager

router = APIRouter(prefix="/filemanager", tags=["File Manager"])

@router.post("/upload")
async def upload_cv(file: UploadFile = File(...), folder: str = Form("General")):
    filename = file_manager.save_upload_file(file, folder)
    return {"message": "Éxito", "filename": filename, "folder": folder}

@router.post("/create-folder")
async def create_folder(folder_name: str = Form(...)):
    result = file_manager.create_folder(folder_name)
    return result

@router.get("/folders")
async def get_folders():
    folders = file_manager.get_folders()
    return {"folders": folders}

@router.get("/list")
async def list_cvs():
    files = file_manager.get_file_tree()
    return files
