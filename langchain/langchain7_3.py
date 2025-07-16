import gradio as gr
from langchain_community.document_loaders import PyPDFLoader, WebBaseLoader, DirectoryLoader, TextLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import Chroma
from langchain_community.llms import Ollama
from langchain_ollama import OllamaEmbeddings
from langchain.chains import RetrievalQA
from langchain.memory import ConversationBufferMemory
from langchain_experimental.text_splitter import SemanticChunker
import atexit
import os
import pytesseract
import shutil


CHROMA_DB_DIR = "./chroma_db"

def cleanup_chroma_db():
    if os.path.exists(CHROMA_DB_DIR):
        shutil.rmtree(CHROMA_DB_DIR)
        print("已清理向量数据库目录：", CHROMA_DB_DIR)

cleanup_chroma_db()
# 手动指定 Tesseract 路径
pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

d = None  # 全局 DocumentQA 实例

def load_documents(file_path, url=''):
    docs = []
    if os.path.isfile(file_path):
        # 单文件，判断类型
        ext = os.path.splitext(file_path)[1].lower()
        if ext == ".txt":
            docs = TextLoader(file_path, encoding="utf-8").load()
        elif ext == ".pdf":
            docs = PyPDFLoader(file_path).load()
        # 你可以继续扩展其他类型
    else:
        # 文件夹，批量加载
        pdf_loader = DirectoryLoader(file_path, glob="**/*.pdf", loader_cls=PyPDFLoader)
        txt_loader = DirectoryLoader(file_path, glob="**/*.txt", loader_cls=TextLoader, loader_kwargs={"encoding": "utf-8"})
        docs = pdf_loader.load() + txt_loader.load()
    if url:
        web_loader = WebBaseLoader(url)
        docs += web_loader.load()
    return docs

def init_vectorstore(doc):
    embedding = OllamaEmbeddings(model="nomic-embed-text", base_url="http://localhost:8080")
    doc_spliter = SemanticChunker(embeddings=embedding, add_start_index=True)
    chunks = doc_spliter.split_documents(doc)
    vectorstore = Chroma.from_documents(chunks, embedding, persist_directory="./chroma_db")
    return vectorstore

class ChatMemory:
    def init_memory(self):
        self.memory = ConversationBufferMemory(
            memory_key="chat_history",
            return_messages=True,
            input_key="query",
            output_key="result"
        )
    def get_history(self):
        history = []
        messages = self.memory.chat_memory.messages
        for i, msg in enumerate(messages):
            if i + 6 >= len(messages):  # 取最后6条
                if hasattr(msg, "content"):
                    msg_type = type(msg).__name__
                    history.append({msg_type: msg.content})
        return history
    def clear(self):
        self.memory.clear()
        return []

class DocumentQA:
    def __init__(self, vectorstore):
        self.memory = ChatMemory()
        self.memory.init_memory()
        self.qa_chain = RetrievalQA.from_chain_type(
            llm=Ollama(model="deepseek-r1:7b", base_url="http://localhost:8080", num_gpu=1, num_predict=4096),
            chain_type="stuff",
            retriever=vectorstore.as_retriever(),
            memory=self.memory.memory,
            return_source_documents=True
        )
        atexit.register(self.cleanup)
    def ask(self, question):
        response = self.qa_chain.invoke({"query": question})
        return response
    def cleanup(self):
        if hasattr(self, 'memory'):
            self.memory.clear()

def respond(file_path, url, msg, chatbox, page_state):
    global d
    # 只初始化一次 DocumentQA
    if d is None:
        docx = load_documents(file_path, url)
        vectorstore = init_vectorstore(docx)
        d = DocumentQA(vectorstore)
    response_full = d.ask(msg)
    response = response_full["result"]
    response = response.split("<think>")[-1].split("</think>")[-1]
    d.memory.memory.save_context({"query": msg}, {"result": response})
    source = []
    source_text = []
    processed_sources_text = set()
    for i, doc in enumerate(response_full.get("source_documents", [])):
        if i >= 3:
            break
        page = f"//{doc.metadata.get('source', '未知来源')} (第{doc.metadata.get('page', '0')}页)\n"
        text = f"{doc.page_content}"
        if text not in processed_sources_text:
            source.append(page)
            source_text.append(text)
            processed_sources_text.add(text)
    source_str = "\n".join(source) if source else "无来源信息"
    chatbox.append((msg, f"{response}:{source_str}"))
    # 分页状态
    current_page = 0
    page_content = source_text[0] if source_text else "无内容"
    page_info = f"{current_page+1}/{len(source_text)}" if source_text else "0/0"
    return '', chatbox, page_content, [current_page, source_text], page_info

def turn_page(page_state, direction):
    current_page, source_text = page_state
    total_page = len(source_text)
    if total_page == 0:
        return "无内容", [0, source_text], "0/0"
    if direction == "next":
        current_page = min(current_page + 1, total_page - 1)
    else:
        current_page = max(current_page - 1, 0)
    page_content = source_text[current_page]
    page_info = f"{current_page+1}/{total_page}"
    return page_content, [current_page, source_text], page_info

def show_history():
    global d
    if d is None or not hasattr(d, "memory"):
        return "暂无历史"
    history = d.memory.get_history()
    if not history:
        return "暂无历史"
    lines = []
    for item in history:
        for k, v in item.items():
            lines.append(f"{k}: {v}")
    return "\n".join(lines)

def clear_(chatbox):
    global d
    if d is not None:
        d.memory.clear()
    return [], [0, []], "无内容"

with gr.Blocks(theme=gr.themes.Soft()) as demo:
    gr.Markdown("构建增强版文档问答系统")
    chatbox = gr.Chatbot(label='对话历史', height=400)
    page_state = gr.State([0, []])
    with gr.Row():
        last_bt = gr.Button("上一页")
        next_bt = gr.Button("下一页")
        page_text = gr.Textbox(label="参考文档")
        page_info = gr.Textbox(label="页码", interactive=False)
    history = gr.Button("查看历史对话")
    clear = gr.Button("清空对话")
    msg = gr.Textbox(label='输入消息', placeholder='请输入您的问题')
    with gr.Accordion("设置", open=False):
        file_path = gr.Textbox(label="文档路径")
        url = gr.Textbox(label="URL")
    chathistory = gr.Textbox("", label='最近的三条对话记录')

    msg.submit(
        respond,
        inputs=[file_path, url, msg, chatbox, page_state],
        outputs=[msg, chatbox, page_text, page_state, page_info]
    )
    last_bt.click(
        turn_page,
        inputs=[page_state, gr.State("prev")],
        outputs=[page_text, page_state, page_info]
    )
    next_bt.click(
        turn_page,
        inputs=[page_state, gr.State("next")],
        outputs=[page_text, page_state, page_info]
    )
    history.click(
        fn=show_history,
        inputs=None,
        outputs=chathistory,
        queue=False
    )
    clear.click(
        fn=clear_,
        inputs=[chatbox],
        outputs=[chatbox, page_state, page_text],
        queue=False
    )

demo.launch(inbrowser=True)