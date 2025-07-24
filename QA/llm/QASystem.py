import json
import traceback
import datetime
import uuid
from pathlib import Path
from fastapi import FastAPI, File, HTTPException, UploadFile, Depends
from langchain.chains import ConversationalRetrievalChain
from langchain.prompts import PromptTemplate
from langchain_community.vectorstores import FAISS
from langchain_community.retrievers import BM25Retriever
from langchain.retrievers import BM25Retriever, EnsembleRetriever
from langchain.memory import ConversationSummaryMemory
from langchain_community.vectorstores import Chroma
from langchain_ollama import OllamaEmbeddings
from RAG import CHROMA_DB_DIR, chunks, add_to_vectorstore
import os
import sys
import requests
from typing import Dict
from pydantic import SecretStr
from contextlib import asynccontextmanager
from auth import get_current_user
from config import settings

class DeepSeekChat:
    def __init__(self, model_name: str, api_key: SecretStr):
        self.model_name = model_name
        self.api_key = api_key

    def invoke(self, input: Dict) -> Dict:
        messages = []
        if 'chat_history' in input:
            for msg in input['chat_history']:
                messages.append({
                    "role": "user" if msg.type == "human" else "assistant",
                    "content": msg.content
                })
        messages.append({"role": "user", "content": input["question"]})

        headers = {
            "Authorization": f"Bearer {self.api_key.get_secret_value()}",
            "Content-Type": "application/json"
        }
        data = {
            "model": self.model_name,
            "messages": messages,
            "temperature": 0.7
        }

        try:
            response = requests.post(
                "https://api.deepseek.com/v1/chat/completions",
                headers=headers,
                json=data
            )
            response.raise_for_status()
            return {"answer": response.json()["choices"][0]["message"]["content"]}
        except requests.exceptions.RequestException as e:
            raise RuntimeError(f"DeepSeek API调用失败: {str(e)}")

llm = DeepSeekChat(model_name="deepseek-chat", api_key=SecretStr(settings.DEEPSEEK_API_KEY))

class DocumentQA:
    def __init__(self, prompt_template):
        self.user_sessions = {}
        self.prompt_template = prompt_template or '''
        你是一名天文学家，你精通天文知识。
        请保持严谨性，在回答时不要出现任何错误。
        请根据以下已知信息，幽默地回答问题。
        历史对话：{chat_history}
        已知信息:
        {context}
        如果问题在已知信息中没有涉及，用你自己的知识库回答，不要编造。
        问题: {question}

        请优先使用中文回答。'''

    def get_user_session(self, user_id: str):
        if user_id not in self.user_sessions:
            self.user_sessions[user_id] = {
                'vectorstore': None,
                'memory': ConversationSummaryMemory(
                    llm=llm,
                    memory_key="chat_history",
                    return_messages=True,
                    input_key="question",
                    output_key="answer"
                ),
                'qa_chain': None
            }
        return self.user_sessions[user_id]

    def init_with_vectorstore(self, vectorstore, user_id: str):
        session = self.get_user_session(user_id)
        session['vectorstore'] = vectorstore
        session['qa_chain'] = self.init_qa_chain(user_id)

#     def add_file(self, file_path: str, user_id: str):
#         try:
#             session = self.get_user_session(user_id)
#             if not session['vectorstore']:
#                 embedding = OllamaEmbeddings(model="nomic-embed-text")
#                 session['vectorstore'] = Chroma(persist_directory=CHROMA_DB_DIR, embedding_function=embedding)
#
#             add_to_vectorstore(session['vectorstore'], file_path)
#             session['qa_chain'] = self.init_qa_chain(user_id)
#         except Exception as e:
#             print(f"向量化文件失败: {file_path}, 错误: {e}")

    def add_file(self, file_path: str, user_id: str):
        try:
            session = self.get_user_session(user_id)
            if not session['vectorstore']:
                embedding = OllamaEmbeddings(model="nomic-embed-text")
                # Clean up any existing ChromaDB with wrong dimensions
                if os.path.exists(CHROMA_DB_DIR):
                    shutil.rmtree(CHROMA_DB_DIR)
                # Create new vectorstore with correct dimensions
                session['vectorstore'] = Chroma(persist_directory=CHROMA_DB_DIR,
                                              embedding_function=embedding)

            add_to_vectorstore(session['vectorstore'], file_path)
            session['qa_chain'] = self.init_qa_chain(user_id)
        except Exception as e:
            print(f"向量化文件失败: {file_path}, 错误: {e}")
            raise  # Re-raise the exception to see the actual error

    def init_qa_chain(self, user_id: str):
        session = self.get_user_session(user_id)
        if not session['vectorstore']:
            raise ValueError("Vectorstore not initialized. Please call 'init_with_vectorstore' first.")

        prompt_template = PromptTemplate.from_template(self.prompt_template)
        vector_retriever = session['vectorstore'].as_retriever(
            search_type="mmr",
            search_kwargs={"k": 4}
        )

        bm25_retriever = BM25Retriever.from_documents(chunks or [], k=4)

        qa_chain = ConversationalRetrievalChain.from_llm(
            llm=llm,
            chain_type="stuff",
            retriever=EnsembleRetriever(
                retrievers=[vector_retriever, bm25_retriever],
                weights=[0.7, 0.3]
            ),
            memory=session['memory'],
            return_source_documents=True,
            combine_docs_chain_kwargs={"prompt": prompt_template},
            verbose=False
        )
        return qa_chain

    def ask(self, question: str, user_id: str):
        session = self.get_user_session(user_id)
        if session['qa_chain']:
            result = session['qa_chain'].invoke({"question": question})
            return result['answer']
        else:
            return "请先上传文档"

@asynccontextmanager
async def lifespan(app: FastAPI):
    global dqa
    dqa = DocumentQA("")
    yield
    # 清理工作

app = FastAPI(lifespan=lifespan)

UPLOAD_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "uploads")
os.makedirs(UPLOAD_DIR, exist_ok=True)
ALLOWED_EXTENSIONS = ["txt", "png", "jpg", "jpeg", "pdf", "docx", "xlsx"]

@app.post("/upload")
async def upload_file(
    file: UploadFile = File(...),
    username: str = Depends(get_current_user)
):
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

        dqa.add_file(save_path, username)
        return {
            "status": "success",
            "message": "文件上传成功",
            "filename": file.filename
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get('/ask')
def ask(
    question: str,
    username: str = Depends(get_current_user)
):
    return {"answer": dqa.ask(question, username)}
