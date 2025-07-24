import React, { useState, useRef, useEffect } from 'react';
import AttachFileIcon from '@mui/icons-material/AttachFile';
import SendIcon from '@mui/icons-material/Send';
import InsertEmoticonIcon from '@mui/icons-material/InsertEmoticon';
import ClearIcon from '@mui/icons-material/Clear';
import AddIcon from '@mui/icons-material/Add';
import './HomeDashboard.css';
import { useMessages } from './MessageContext';
import { useOutletContext } from 'react-router-dom';
import { useNavigate } from 'react-router-dom';
import { aisk, get_conversations, updateTitle } from './request.jsx';
import {CircularProgress} from "@mui/material";
import usermanage from "./Usermanage.jsx";

const HomeDashboard = () => {
  const navigate = useNavigate();
  const [inputText, setInputText] = useState('');
  // const [selectedFile, setSelectedFile] = useState(null);
  const [selectedFiles, setSelectedFiles] = useState([]);
  const [isFocused, setIsFocused] = useState(false);
  const fileInputRef = useRef(null);
  const [messages, setMessages] = useState([]);
  const [isChatStarted, setIsChatStarted] = useState(false);
  const messagesEndRef = useRef(null);

  const { activeConversationId } = useOutletContext();
  const conversationIdRef = useRef(null);
  const [currentConversation, setCurrentConversation] = useState(null);

  const [currentConversationTitle, setCurrentConversationTitle] = useState(null)
  const conversationTitle = useRef(null);

  const [isUploading, setIsUploading] = useState(false);

  // 新增状态：编辑模式和编辑中的标题
  const [isEditingTitle, setIsEditingTitle] = useState(false);
  const [editingTitle, setEditingTitle] = useState('');

  // 修改标题的函数
  const handleTitleEdit = () => {
    setEditingTitle(currentConversationTitle || '');
    setIsEditingTitle(true);
  };

  // 保存标题的函数
  const handleTitleSave = async () => {
    if (!editingTitle.trim()) return;

    const token = localStorage.getItem('token');

      updateTitle(token, conversationIdRef.current, editingTitle).then((response) => {
        if (response.message === "标题更新成功") {
          conversationTitle.current = editingTitle;
          setCurrentConversationTitle(editingTitle);
          setIsEditingTitle(false);
        }
      });
    // try {
    //   // const response = await fetch(`/api/conversations/${conversationIdRef.current}/title`, {
    //   //   method: 'PUT',
    //   //   headers: {
    //   //     'Content-Type': 'application/x-www-form-urlencoded',
    //   //     'Authorization': `Bearer ${token}`
    //   //   },
    //   //   body: `new_title=${encodeURIComponent(editingTitle)}`
    //   // });
    //
    //   // const result = await response.json();
    //
    //   if (result.success) {
    //     // 更新本地状态
    //     conversationTitle.current = editingTitle;
    //     setCurrentConversationTitle(editingTitle);
    //     setIsEditingTitle(false);
    //   } else {
    //     alert('更新标题失败，请重试');
    //   }
    // } catch (error) {
    //   console.error('更新标题时出错:', error);
    //   alert('网络错误，请检查网络连接');
    // }
  };

  // 取消编辑
  const handleTitleCancel = () => {
    setIsEditingTitle(false);
    setEditingTitle('');
  };

  // 处理标题输入变化
  const handleTitleChange = (e) => {
    setEditingTitle(e.target.value);
  };

  // 处理键盘事件（回车保存，ESC取消）
  const handleTitleKeyDown = (e) => {
    if (e.key === 'Enter') {
      handleTitleSave();
    } else if (e.key === 'Escape') {
      handleTitleCancel();
    }
  };


  //滑动到底部
  const scrollToBottom = () => {
    window.scrollTo({
      top: document.documentElement.scrollHeight,
      behavior: 'smooth'
    });
  };

  const setTitle = (token) => {
    fetchConversation(token, conversationIdRef.current).then(response => {
      // const data = transformMessages(response.data.messages);
      // setCurrentConversation(response.data);
      // setMessages(data);
      // conversationIdRef.current = response.data.conversation_id;
      conversationTitle.current = response.data.title;
      setCurrentConversationTitle(response.data.title);
    });
  }

  useEffect(() => {
    const token = localStorage.getItem('token');
    // if (activeConversationId) {
    //   setIsChatStarted(true);
    //   get_conversations(token, activeConversationId).then((response) => {
    //     console.log(response);
    //     conversationTitle.current = response.data.title;
    //     console.log(conversationTitle.current);
    //     setCurrentConversationTitle(response.data.title);
    //     console.log(currentConversationTitle);
    //     console.log(response.data.title);
    //     // setMessages(response.data.messages);
    //   })
    // }
    if (isChatStarted) {
      scrollToBottom();
    }
    if (activeConversationId) {
      setIsChatStarted(true);
      fetchConversation(token, activeConversationId).then(response => {
        const data = transformMessages(response.data.messages);
        setCurrentConversation(response.data);
        setMessages(data);
        conversationIdRef.current = response.data.conversation_id;
        conversationTitle.current = response.data.title;
        setCurrentConversationTitle(response.data.title);

      // .then((response) => {
      //     console.log(response);
      //     conversationTitle.current = response.data.title;
      //     console.log(conversationTitle.current);
      //     setCurrentConversationTitle(response.data.title);
      //     console.log(currentConversationTitle);
      //     console.log(response.data.title);
      //     // setMessages(response.data.messages);
      //   })
      });
    } else {
      setCurrentConversation(null);
    }
  }, [activeConversationId]);
// }, [activeConversationId, messages, isChatStarted]);

  const fetchConversation = async (token, conversationId) => {
    // console.log('Fetching conversation:', conversationId);
    // // 实际项目中这里应该是API调用
    // return {
    //   id: conversationId,
    //   title: `对话 ${conversationId}`,
    //   messages: messages.filter(msg => msg.conversation_id === conversationId)
    // };

    return get_conversations(token, conversationId);
  };

  const transformMessages = (messagesArray) => {
    return messagesArray.map(message => {
      return {
        id: message.message_id,
        text: message.content,
        sender: message.is_user ? 'user' : 'ai',
        timestamp: new Date(message.created_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
        conversation_id: message.conversation_id
      };
    });
  };


  const handleInputChange = (e) => {
    setInputText(e.target.value);
  };

  const handleFileChange = (e) => {
    // if (e.target.files && e.target.files[0]) {
    //   setSelectedFile(e.target.files[0]);
    // }
    if (e.target.files) {
      const filesArray = Array.from(e.target.files);
      setSelectedFiles(prev => [...prev, ...filesArray]);
    }
  };

  const triggerFileInput = () => {
    fileInputRef.current.click();
  };

  const removeFile = (indexToRemove) => {
    // setSelectedFile(null);
    // if (fileInputRef.current) {
    //   fileInputRef.current.value = '';
    // }
    setSelectedFiles(prev => prev.filter((_, idx) => idx !== indexToRemove));
    // const removeFile = (indexToRemove) => {
    //   setSelectedFiles(prev => prev.filter((_, idx) => idx !== indexToRemove));
    // }
    // if (fileInputRef.current) {
    //   fileInputRef.current.value = '';
    // }
  };

  const handleSubmit = () => {
    if (!inputText.trim() && selectedFiles.length === 0) return;
    // 如果是第一次提交，开始对话，下面均为新增
    if (!isChatStarted) {
      setIsChatStarted(true);
    }
    setIsUploading(true);
    const token = localStorage.getItem('token');
    if (messages.length === 2 || messages.length === 6 || messages.length === 12) {
      setTitle(token);
    }
    //用户消息
    const userMessage = {
      id: Date.now(),
      text: inputText,
      sender: 'user',
    };
    setMessages(prev => [...prev, userMessage]);

    // 模拟AI回复（在实际应用中应替换为API调用）
    // setTimeout(() => {
    //   const aiMessage = {
    //     id: Date.now() + 1,
    //     text: `这是关于"${inputText}"的模拟回复。在实际应用中，这里会显示真实的AI回复内容。`,
    //     sender: 'ai',
    //     timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
    //   };
    //   setMessages(prev => [...prev, aiMessage]);
    // }, 1000);
    // console.log('before' + conversationIdRef.current);
    aisk(token, inputText, conversationIdRef.current, selectedFiles).then((response) => {
      console.log(response);
      const aiMessage = {
        id: Date.now() + 1,
        text: response.answer,
        sender: 'ai',
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
      };
      setMessages(prev => [...prev, aiMessage]);
      // console.log("inner " + response.conversation_id);
      conversationIdRef.current = response.conversation_id;
      // console.log('after ' + conversationIdRef.current);
    }).catch((error) => {
      console.log(error);
      navigate('/login');
    }).finally(() => {
      setIsUploading(false);
      // 清空输入
      setInputText('');
      setSelectedFiles([]);
      if (fileInputRef.current) {
        fileInputRef.current.value = '';
      }
    });
  };
  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && e.ctrlKey) {
      handleSubmit();
    }
  };

  const handleNewChat = () => {
    setInputText('');
    // setSelectedFile(null);
    setSelectedFiles([]);
    setMessages([]);
    setIsChatStarted(false);
    conversationIdRef.current = null;
    conversationTitle.current = "";
    if (fileInputRef.current) {
      fileInputRef.current.value = '';
    }
    //console.log('新建对话');
  };

  return (
      <div className={`home-dashboard ${isChatStarted ? 'chat-started' : ''}`}>
        {isChatStarted && (
            <div>
            <div className="new-chat-container">
              {/*<h1 className="conversation-title">{conversationTitle.current}</h1>*/}
              {isEditingTitle ? (
                  <div className="title-edit-container">
                    <input
                        type="text"
                        value={editingTitle}
                        onChange={handleTitleChange}
                        onKeyDown={handleTitleKeyDown}
                        className="title-edit-input"
                        autoFocus
                        maxLength={100}
                    />
                    <div className="title-edit-buttons">
                      <button onClick={handleTitleSave} className="title-save-btn">
                        ✓
                      </button>
                      <button onClick={handleTitleCancel} className="title-cancel-btn">
                        ✕
                      </button>
                    </div>
                  </div>
              ) : (
                  <h1
                      className="conversation-title editable"
                      onClick={handleTitleEdit}
                      title="点击编辑标题"
                  >
                    {conversationTitle.current || '对话标题'}
                  </h1>
              )}
              <button className="new-chat-button" onClick={handleNewChat}>
                <AddIcon fontSize="medium" />
              </button>
            </div>
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
            {/*{selectedFile && (*/}
            {/*    <div className="file-preview">*/}
            {/*      <div className="file-info">*/}
            {/*        <div className="file-details">*/}
            {/*          <span className="file-name">{selectedFile.name}</span>*/}
            {/*          <span className="file-size">*/}
            {/*        {Math.round(selectedFile.size / 1024)} KB*/}
            {/*      </span>*/}
            {/*        </div>*/}
            {/*      </div>*/}
            {/*      <button className="remove-file" onClick={removeFile}>*/}
            {/*        <ClearIcon fontSize="small" />*/}
            {/*      </button>*/}
            {/*    </div>*/}
            {/*)}*/}
            {selectedFiles.length > 0 && (
                <div className="file-preview-list">
                  {selectedFiles.map((file, idx) => (
                      <div key={idx} className="file-preview">
                        <div className="file-info">
                          <span className="file-name">{file.name}</span>
                          <span className="file-size">{Math.round(file.size / 1024)} KB</span>
                        </div>
                        <button className="remove-file" onClick={() => removeFile(idx)}>
                          <ClearIcon fontSize="small" />
                        </button>
                      </div>
                  ))}
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
            {/*<button*/}
            {/*    className={`submit-button ${(inputText.trim() || selectedFiles) ? 'active' : ''}`}*/}
            {/*    onClick={handleSubmit}*/}
            {/*>*/}
            {/*  <SendIcon />*/}
            {/*</button>*/}
            <button
                className={`submit-button ${(inputText.trim() || selectedFiles.length) ? 'active' : ''}`}
                onClick={handleSubmit}
                disabled={isUploading}
            >
              {isUploading ? <CircularProgress size={24} /> : <SendIcon />}
            </button>
          </div>

          <input
              type="file"
              ref={fileInputRef}
              onChange={handleFileChange}
              style={{ display: 'none' }}
              accept=".pdf,.doc,.docx,.txt,.jpg,.jpeg,.png"
              multiple
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