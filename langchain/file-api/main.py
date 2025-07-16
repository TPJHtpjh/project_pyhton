import json
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import FileResponse
import os
import uuid
from pathlib import Path
import datetime
import traceback  # 添加traceback用于详细错误日志

app = FastAPI(
    title="文档处理API",
    version="1.0.0",
    description="文档处理API",
)

UPLOAD_DIR = "uploads"
META_DIR = os.path.join(UPLOAD_DIR, "_meta")  # 确保元数据目录在uploads下

# 确保目录存在
os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(META_DIR, exist_ok=True)

# 允许的文件扩展名
ALLOWED_EXTENSIONS = ["png", "jpg", "jpeg", "pdf", "docx", "xlsx"]

@app.post("/upload", summary="上传文件", description="最大限制10MB")
async def upload_file(
    file: UploadFile = File(...),
    description: str | None = None,
    uploader: str | None = None
):
    try:
        MAX_SIZE = 10 * 1024 * 1024  # 10MB
        
        # 检查文件大小
        file_size = file.size
        if file_size > MAX_SIZE:
            raise HTTPException(
                status_code=413, 
                detail=f"文件大小超过限制 ({file_size} > {MAX_SIZE} bytes)"
            )
        # 获取文件路径对象
        file_path = Path(file.filename)
        
        # 获取文件扩展名（安全方式）
        file_ext = file_path.suffix.lower()
        if not file_ext or len(file_ext) < 2:
            raise HTTPException(status_code=400, detail="文件缺少扩展名")
        
        # 去掉点号，只保留扩展名
        file_ext = file_ext[1:]
        
        # 检查文件类型
        if file_ext not in ALLOWED_EXTENSIONS:
            allowed = ", ".join(ALLOWED_EXTENSIONS)
            raise HTTPException(
                status_code=400, 
                detail=f"不支持的文件类型，仅支持: {allowed}"
            )
        
        # 生成唯一文件名
        new_filename = f"{uuid.uuid4()}{file_path.suffix}"
        save_path = os.path.join(UPLOAD_DIR, new_filename)
        
        # 保存文件
        contents = await file.read()
        with open(save_path, "wb") as f:
            f.write(contents)
        
        # 保存元数据
        meta_data = {
            "original_name": file.filename,
            "saved_name": new_filename,
            "description": description,
            "uploader": uploader,
            "size": len(contents),
            "content_type": file.content_type,
            "upload_time": datetime.datetime.now().isoformat()
        }
        
        meta_file_path = os.path.join(META_DIR, f"{new_filename}.json")
        
        # 确保元数据目录存在
        os.makedirs(META_DIR, exist_ok=True)
        
        with open(meta_file_path, "w", encoding="utf-8") as f:
            json.dump(meta_data, f, ensure_ascii=False, indent=2)
        
        return {
            "status": "success",
            "message": "文件上传成功",
            "metadata": meta_data,
            "download_url": f"/download/{new_filename}",
            "metadata_url": f"/files/{new_filename}/meta"
        }
    
    except HTTPException:
        raise  # 重新抛出已知的HTTP异常
    
    except Exception as e:
        # 获取详细的错误信息
        error_detail = f"Error: {str(e)}\nTraceback:\n{traceback.format_exc()}"
        raise HTTPException(status_code=500, detail=error_detail)

@app.get("/download/{filename}", summary="下载文件")
async def down_file(filename:str):
    file_path=os.path.join(UPLOAD_DIR,filename)
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404,detail="文件不存在")
    return FileResponse(
        file_path,
        media_type='application/octet-stream',
        filename=filename
    )

@app.get("/files",summary="获取文件列表")
async def list_files():
    files=[]
    for filename in os.listdir(UPLOAD_DIR):
        file_path=os.path.join(UPLOAD_DIR,filename)
        if os.path.isfile(file_path):
            files.append({
                "name":filename,
                "size":os.path.getsize(file_path),
                "modified":os.path.getmtime(file_path)
            })
    return files

@app.delete("/files/{file_name}", summary="删除文件")
async def delete_file(file_name: str):
    file_path = Path(UPLOAD_DIR) / file_name
    meta_path = Path(META_DIR) / f"{file_name}.json"
    
    if not file_path.exists():
        raise HTTPException(404, detail="文件不存在")
    
    # 删除文件
    file_path.unlink()
    
    # 删除元数据
    if meta_path.exists():
        meta_path.unlink()
    
    return {
        "status": "success",
        "message": f"文件 {file_name} 及其元数据已删除",
        "deleted_at": datetime.datetime.now().isoformat()
    }

@app.get("/files/{file_name}/meta")
async def get_meta_data(file_name:str,summary="获得元数据"):
    meta_path =os.path.join(META_DIR,f"{file_name}.json")
    if not os.path.exists(meta_path):
        raise HTTPException(status_code=404,detail="元数据不存在")
    with open(meta_path,"r",encoding="utf-8") as f:#"r"表示以只读的模式打开元数据
        return json.load(f)

if __name__=="__main__":
    import uvicorn
    uvicorn.run(app, host='127.0.0.1', port=8000)


