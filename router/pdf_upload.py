from fastapi import APIRouter, File, HTTPException, UploadFile

router= APIRouter()

@router.post('/upload')
async def upload_pdfs(files: list[UploadFile]= File(...)):
    if len(files)> 2:
        raise HTTPException(status_code= 400, details= "Lmit: 2 PDF's Only")
    pdf_path= []
    for f in files:
        path= f"/tmp/{f.filename}"
        with open(path, 'wb') as file_out:
            file_out.write(await f.read())
        pdf_path.append(path)
    return {"Uploaded_files": pdf_path}
