from contextlib import asynccontextmanager
import random
import re
import traceback
import uuid
from pathlib import Path
from fastapi import FastAPI, File, HTTPException, UploadFile
from langchain_chroma import Chroma
from RAG import CHROMA_DB_DIR,embedding
from QAsystem import DocumentQA
from questionRAG import questions,QUESTION_DB_DIR
from rand_questions import Judge,random_question
from question_seek import LLMseek, personal_sum,question
import os
app = FastAPI(
    title="qa",
    version="1.0.0",
)

UPLOAD_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "uploads")
os.makedirs(UPLOAD_DIR, exist_ok=True)
ALLOWED_EXTENSIONS = ["txt", "png", "jpg", "jpeg", "pdf", "docx", "xlsx"]

@asynccontextmanager
async def lifespan(app: FastAPI):
    # --- 启动时执行 ---
    if (not os.path.exists(QUESTION_DB_DIR)) or (not os.path.exists(CHROMA_DB_DIR)):
        print(f"错误: 向量数据库目录 '{QUESTION_DB_DIR}/{CHROMA_DB_DIR}' 不存在。")
        print("请确保您已经成功运行了 RAG.py 来创建数据库。")
        exit()
    
    vectorstore = Chroma(
        persist_directory=CHROMA_DB_DIR,
        embedding_function=embedding
    )
    global dqa
    dqa = DocumentQA("")
    dqa.init_with_vectorstore(vectorstore)
    question_vectorstore=Chroma(
        persist_directory=QUESTION_DB_DIR,
        embedding_function=embedding
    )
    global qs
    qs=LLMseek('',question_vectorstore)
    qs.init_chain()
    yield
    dqa.clear()

app = FastAPI(
    title="qa",
    version="1.0.0",
    lifespan=lifespan
)

@app.post("/upload", summary="上传文件", description="最大限制50MB")
async def upload_file(file: UploadFile = File(...)):
    try:
        MAX_SIZE = 50 * 1024 * 1024  # 50MB
        if not file.filename:
            raise HTTPException(status_code=400, detail="文件名不能为空")
        file_path = Path(file.filename)
        file_ext = file_path.suffix.lower()[1:]
        if not file_ext or file_ext not in ALLOWED_EXTENSIONS:
            allowed = ", ".join(ALLOWED_EXTENSIONS)
            raise HTTPException(status_code=400, detail=f"不支持的文件类型，仅支持: {allowed}")

        contents = await file.read()
        if len(contents) > MAX_SIZE:
            raise HTTPException(status_code=413, detail=f"文件大小超过限制 ({len(contents)} > {MAX_SIZE} bytes)")

        new_filename = f"{uuid.uuid4()}{file_path.suffix}"
        save_path = os.path.join(UPLOAD_DIR, new_filename)
        with open(save_path, "wb") as f:
            f.write(contents)

        dqa.add_file(save_path)
        return {
            "status": "success",
            "message": "文件上传成功",
            "filename": file.filename
        }
    except HTTPException:
        raise
    except Exception as e:
        error_detail = f"Error: {str(e)}\nTraceback:\n{traceback.format_exc()}"
        raise HTTPException(status_code=500, detail=error_detail)

@app.get('/ask',description='问答')
def ask(question: str):
    return dqa.ask(question)

@app.get('/history',description='查看历史')
def history():
    return dqa.show_history()

@app.post('/clear',description='清空历史')
def clear():
    dqa.clear()
    return "清空成功"

@app.get('/random_question',description='随机生成十道题,有输入则按照输入关键字和难度返回十道题,题型不固定')
def random_questions(word:str|None,difficulty:str|None):
    if word and difficulty:
        ques=[]
        for i,q in enumerate(questions):
          que=q.page_content
          if que.find(word)!=-1 and que.find(difficulty)!=-1:
            ques.append(q)
        #random.shuffle(ques)
        if len(ques)>10:
            #ques=ques[:10]
            ques=random.sample(ques,10)
        for questio in ques:
          ques=re.split(r'题目:|答案:|难度:',re.sub(r'\s','',questio))
          content=ques[1]
          answer=ques[2]
          difficulty=ques[3]
          random_questions.append({'content':content,'answer':answer,'difficulty':difficulty})
        return random_questions
    else:
      return random_question(questions)

@app.get('/judge',description='判断问题')
def judge(question:list[question],answer:list):
    ass=Judge(question,answer)
    return ass.score

@app.get('/seek',description='搜索问题，大模型返回一个最相关的题目')
def seek(word:str):
    QS=qs.seek_question(word)
    return {QS.content,QS.answer,QS.difficulty}

@app.get('/sum',description='根据答题情况总结不足')
def sum(que:list,respond:list):
    ass=Judge(que,respond)
    sum=personal_sum(ass.responds)
    return sum

if __name__== "__main__":
    # print(dqa.ask("第二周的作业是什么？"))

    #--- 以下为问答示例 ---
    # asks=["第二周作业的选择题答案是什么？","其中选项A出现了多少次？"]
    # for a in asks:
    #     result=dqa.ask(a)
    #     print(result)

    # print("\n--- 对话历史 ---")
    # print(dqa.show_history())
    
    # dqa.clear()
    # print("\n--- 清空历史后 ---")
    # print(dqa.show_history())
    # print("*"*90)
    import uvicorn
    uvicorn.run(app, host='127.0.0.1', port=8000)