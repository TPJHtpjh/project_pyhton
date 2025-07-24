import React,{ useState, useRef, useEffect } from 'react';
import AttachFileIcon from '@mui/icons-material/AttachFile';
import SendIcon from '@mui/icons-material/Send';
import AddIcon from '@mui/icons-material/Add'; 
import ClearIcon from '@mui/icons-material/Clear';
import './HomeDashboard.css'; 

const HomeDashboard = () => {
  const [inputText, setInputText] = useState('');
  const [selectedFile, setSelectedFile] = useState(null);
  const [isFocused, setIsFocused] = useState(false);
  const fileInputRef = useRef(null);
  const [messages, setMessages] = useState([]);
  const [isChatStarted, setIsChatStarted] = useState(false);
  const messagesEndRef = useRef(null);

  //滑动到底部
  const scrollToBottom = () => {
    window.scrollTo({
      top: document.documentElement.scrollHeight,
      behavior: 'smooth'
    });
  };
  useEffect(() => {
    if (isChatStarted) {
      scrollToBottom();
    }
  }, [messages, isChatStarted]);


  const handleInputChange = (e) => {
    setInputText(e.target.value);
  };

  const handleFileChange = (e) => {
    if (e.target.files && e.target.files[0]) {
      setSelectedFile(e.target.files[0]);
    }
  };

  const triggerFileInput = () => {
    fileInputRef.current.click();
  };

  const removeFile = () => {
    setSelectedFile(null);
    if (fileInputRef.current) {
      fileInputRef.current.value = '';
    }
  };

  const handleSubmit = () => {
    if (!inputText.trim() && !selectedFile) return;
    // 如果是第一次提交，开始对话，下面均为新增
    if (!isChatStarted) {
      setIsChatStarted(true);
    }
    //用户消息
  const userMessage = {
      id: Date.now(),
      text: inputText,
      sender: 'user',
    };
    setMessages(prev => [...prev, userMessage]);
    // 清空输入
    setInputText('');
    setSelectedFile(null);
    if (fileInputRef.current) {
      fileInputRef.current.value = '';
    }
    
    // 模拟AI回复（在实际应用中应替换为API调用）
    setTimeout(() => {
      const aiMessage = {
        id: Date.now() + 1,
        text: `这是关于"${inputText}"的模拟回复。在实际应用中，这里会显示真实的AI回复内容。`,
        sender: 'ai',
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
      };
      setMessages(prev => [...prev, aiMessage]);
    }, 1000);
  };
  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && e.ctrlKey) {
      handleSubmit();
    }
  };
  
  const handleNewChat = () => {
    setInputText('');
    setSelectedFile(null);
    setMessages([]);
    setIsChatStarted(false);
    if (fileInputRef.current) {
      fileInputRef.current.value = '';
    }
    //console.log('新建对话');
  };


  return (
    <div className={`home-dashboard ${isChatStarted ? 'chat-started' : ''}`}>
      {isChatStarted && (
      <div className="new-chat-container">
        <button className="new-chat-button" onClick={handleNewChat}>
          <AddIcon fontSize="medium" />
        </button>
      </div>
    )}
      
      {!isChatStarted && (
        <div className="dashboard-header">
          <h1>天文AI助手</h1>
          <p className="subtitle">您的AI助手，随时为您解答问题</p>
        </div>
      )}
      {/* 消息显示区域 */}
      {isChatStarted && (
        <div className="messages-container">
          {messages.map((message) => (
            <div 
              key={message.id} 
              className={`message ${message.sender}`}
            >
              <div className="message-content">
                {message.text}
              </div>
            </div>
          ))}
          <div ref={messagesEndRef} />
        </div>
      )}

      <div className={`input-container-vertical ${isFocused ? 'focused' : ''} ${isChatStarted ? 'chat-mode' : ''}`}>
        {/* 输入内容区域 */}
        <div className="input-content">
            {selectedFile && (
            <div className="file-preview">
              <div className="file-info">
                <div className="file-details">
                  <span className="file-name">{selectedFile.name}</span>
                  <span className="file-size">
                    {Math.round(selectedFile.size / 1024)} KB
                  </span>
                </div>
              </div>
              <button className="remove-file" onClick={removeFile}>
                <ClearIcon fontSize="small" />
              </button>
            </div>
          )}
            <textarea
              value={inputText}
              onChange={handleInputChange}
              onKeyDown={handleKeyDown}
              onFocus={() => setIsFocused(true)}
              onBlur={() => setIsFocused(false)}
              placeholder="输入您的问题或上传文件..."
              rows={1}
              className="deepseek-textarea"
            />
          </div>

          <div className="button-row"> 
            {/* 上传按钮移动到此处 */}
            <button 
            className="tool-button file-upload-btn"
            onClick={triggerFileInput}
            title="上传文件"
          >
            <AttachFileIcon />
            <span>上传文件</span>
          </button>
          
          {/* 提交按钮移动到此处 */}
          <button 
            className={`submit-button ${(inputText.trim() || selectedFile) ? 'active' : ''}`}
            onClick={handleSubmit}
          >
            <SendIcon />
          </button>
        </div>
          
          <input
            type="file"
            ref={fileInputRef}
            onChange={handleFileChange}
            style={{ display: 'none' }}
            accept=".pdf,.doc,.docx,.txt,.jpg,.jpeg,.png"
          />
        </div>
        
        {!isChatStarted && (
        <div className="input-tips">
          <p>支持上传 PDF、Word、图片等文件类型</p>
          <p>按 Ctrl+Enter 快速提交</p>
        </div>
      )}
    </div>
  );
};


export default HomeDashboard;