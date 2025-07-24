import React, { createContext, useContext, useReducer, useEffect } from 'react';
import './MessageContext.css'

const MessageContext = createContext();

// 从 localStorage 中恢复数据
const loadMessages = () => {
  try {
    const saved = localStorage.getItem('chatMessages');
    return saved ? JSON.parse(saved) : [];
  } catch {
    return [];
  }
};

const initialState = {
  messages: loadMessages(),
};

function messageReducer(state, action) {
  switch (action.type) {
    case 'ADD_MESSAGE':
      return {
        ...state,
        messages: [...state.messages, action.payload],
      };
    default:
      return state;
  }
}

export const MessageProvider = ({ children }) => {
  const [state, dispatch] = useReducer(messageReducer, initialState);

  // 每当 messages 变化，保存到 localStorage
  useEffect(() => {
    localStorage.setItem('chatMessages', JSON.stringify(state.messages));
  }, [state.messages]);

  const addMessage = (content, file = null, conversationId = null) => {
    const newMessage = {
      id: Date.now(),
      content,
      file,
      conversation_id: conversationId,
      timestamp: new Date().toISOString(),
    };
    dispatch({ type: 'ADD_MESSAGE', payload: newMessage });
  };

  return (
    <MessageContext.Provider value={{ messages: state.messages, addMessage }}>
      {children}
    </MessageContext.Provider>
  );
};

export const useMessages = () => useContext(MessageContext);

export default MessageContext;
