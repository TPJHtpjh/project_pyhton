// StartPage.jsx
import React from 'react';
import { useNavigate } from 'react-router-dom';
import { Button } from '@mui/material';
import './StartPage.css';

const StartPage = () => {
  const navigate = useNavigate();
  
  return (
    <div className="start-page-container">
      <button 
        className="start-button" 
        onClick={() => navigate('difficulty')} // 关键：使用相对路径，而非绝对路径
      >
        开始答题
      </button>
    </div>
  );
};

export default StartPage;    