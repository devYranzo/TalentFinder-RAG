import os
import shutil
from fastapi import UploadFile, HTTPException
from config import settings

class FileManager:
    def __init__(self):
        self.storage_path = settings.PDF_PATH

    def save_upload_file(self, upload_file: UploadFile, folder: str = "General") -> str:
        """Guarda un archivo subido en la carpeta especificada."""

        filename = upload_file.filename

        if not filename:
            raise HTTPException(status_code=400, detail="El archivo no tiene nombre.")

        if not filename.lower().endswith(".pdf"):
            raise HTTPException(status_code=400, detail="Solo se permiten archivos PDF.")

        try:
            # Crear la ruta segura de la carpeta
            if folder and folder != "General":
                folder_path = os.path.join(self.storage_path, folder)
            else:
                folder_path = self.storage_path

            os.makedirs(folder_path, exist_ok=True)
            file_path = os.path.join(folder_path, filename)

            with open(file_path, "wb") as buffer:
                shutil.copyfileobj(upload_file.file, buffer)

            return filename
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error al guardar archivo: {str(e)}")

    def create_folder(self, folder_name: str) -> dict:
        """Crea una nueva carpeta en el almacenamiento."""
        if not folder_name or folder_name == "General":
            raise HTTPException(status_code=400, detail="Nombre de carpeta inválido.")

        try:
            folder_path = os.path.join(self.storage_path, folder_name)
            os.makedirs(folder_path, exist_ok=True)
            return {"success": True, "message": f"Carpeta '{folder_name}' creada."}
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error al crear carpeta: {str(e)}")

    def get_folders(self) -> list:
        """Devuelve una lista de todas las carpetas (incluso vacías)."""
        folders = set(["General"])
        target_path = self.storage_path

        try:
            if os.path.exists(target_path):
                for item in os.listdir(target_path):
                    item_path = os.path.join(target_path, item)
                    if os.path.isdir(item_path):
                        folders.add(item)
            return sorted(list(folders))
        except Exception as e:
            return ["General"]

    def get_file_tree(self) -> dict:
        tree = {}
        target_path = self.storage_path

        try:
            for root, dirs, files in os.walk(target_path):
                pdfs = [f for f in files if f.lower().endswith('.pdf')]
                if pdfs:
                    rel_path = os.path.relpath(root, target_path)
                    folder_key = "General" if rel_path == "." else rel_path
                    tree[folder_key] = sorted(pdfs)
            return tree
        except Exception as e:
            return {}

file_manager = FileManager()
