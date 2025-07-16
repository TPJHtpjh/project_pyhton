import gradio as gr
from langchain_community.llms import Ollama  # 使用正确的导入
from langchain.memory import ConversationBufferMemory
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain.chains import ConversationChain

# 全局内存对象 - 确保对话历史持久化
memory = ConversationBufferMemory(
    return_messages=True,
    memory_key="chat_history",
    ai_prefix="AI助手",
    human_prefix="用户"
)

def create_chain(temperature, max_length, personality):
    """创建带参数的对话链"""
    # 1. 创建模型实例
    llm = Ollama(
        model='deepseek-r1:7b',
        base_url='http://localhost:8080',
        temperature=temperature,
        num_predict=max_length  # 使用正确的参数名
    )
    
    # 2. 创建提示模板
    prompt = ChatPromptTemplate.from_messages([
        ("system", f"你现在的人物设定：{personality}。"),
        MessagesPlaceholder(variable_name="chat_history"),
        ("human", "{input}")
    ])
    
    # 3. 创建对话链
    return ConversationChain(
        llm=llm,
        memory=memory,
        prompt=prompt,
        verbose=True
    )
def clean_response(response):
    if r"<think>" in response:
        response=response.split(r"<think>")[-1]
        response=response.split(r"</think>")[-1]
    # # 移除特殊字符
    # cleaned = response.replace('\n', '').replace('\r', '')
    return response
def respond(message, chat_history, temperature, max_length, personality):
    """处理用户消息并返回响应"""
    # 创建带参数的对话链
    chain = create_chain(temperature, max_length, personality)
    
    # 调用对话链 - 使用正确的输入格式
    response = chain.invoke({"input": message})["response"]
    response=clean_response(response)
    # 更新聊天历史
    chat_history.append((message, response))
    
    return "", chat_history

def clear_memory():
    """清除内存并返回空聊天历史"""
    memory.clear()
    return []
def process_voice(audio_data):
    """处理语音输入并返回文本"""
    if audio_data is None:
        return ""
    try:
        import speech_recognition as sr
        recognizer = sr.Recognizer()
        audio = sr.AudioData(voice.tobytes(), sample_rate=44100, frame_width=2)
        text = recognizer.recognize_google(audio, language='zh-CN')
        return text
    except Exception as e:
        return f"语音识别错误: {str(e)}"
def save_chat(chat_history):
    if not chat_history:
        return "尚未对话"
    try:
        with open("chat_history.txt", "w", encoding="utf-8") as file:
            for human, ai in chat_history:
                file.write(f"用户: {human}\nAI助手: {ai}\n\n")
        return "对话已保存"
    except Exception as e:
        return f"保存对话时出错: {str(e)}"

with gr.Blocks(theme=gr.themes.Soft()) as demo:
    gr.Markdown("# 🤖 AI 聊天机器人")
    
    # 聊天界面
    chatbot = gr.Chatbot(label="对话历史", height=400)
    msg = gr.Textbox(label="输入消息", placeholder="在这里输入您的问题...")
    
    # 设置面板
    with gr.Accordion("高级设置", open=False):
        temperature = gr.Slider(0.1, 1.0, value=0.7, label="创意度", interactive=True)
        max_length = gr.Slider(250, 1000, value=100, step=10, label="回复长度", interactive=True)
        personality = gr.Dropdown(
            ["温柔知性", "热血中二", "阴阳怪气", "积极向上", "忧郁悲伤", "正常"],
            value="正常",
            label="人格选择"
        )
        clear_btn = gr.Button("清空对话")
        voice=gr.Audio(label="语音输入",type="numpy")
        save=gr.Button("导出对话")

    
    # 事件处理
    msg.submit(
        respond,
        inputs=[msg, chatbot, temperature, max_length, personality],
        outputs=[msg, chatbot]
    )
    save.click(
        save_chat,
        inputs=chatbot,
        outputs=gr.Textbox(label="导出结果"),
        queue=False
    )
    clear_btn.click(
        clear_memory,
        inputs=None,
        outputs=chatbot,
        queue=False
    )
    voice.change(
        inputs=process_voice(voice),
        outputs=msg,
        queue=False
    )

demo.launch(inbrowser=True)