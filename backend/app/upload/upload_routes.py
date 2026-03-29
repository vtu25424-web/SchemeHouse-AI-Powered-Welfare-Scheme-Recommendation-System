from fastapi import APIRouter, UploadFile, File
import json

router = APIRouter()

@router.post("/upload-schemes")
async def upload_schemes(file: UploadFile = File(...)):
    data = json.loads(await file.read())

    return {
        "message": "File uploaded successfully",
        "count": len(data)
    }