// QuizPage.jsx
import React, { useState } from 'react';
import { useSearchParams } from 'react-router-dom';
import ArrowBackIosIcon from '@mui/icons-material/ArrowBackIos';
import ArrowForwardIosIcon from '@mui/icons-material/ArrowForwardIos';
import './QuizPage.css';

const QuizPage = () => {
  const [currentPage, setCurrentPage] = useState(1);
  const totalPages = 10;

  const handlePrevious = () => {
    if (currentPage > 1) setCurrentPage(currentPage - 1);
  };

  const handleNext = () => {
    if (currentPage < totalPages) setCurrentPage(currentPage + 1);
  };

  const QuizPage = () => {
  const [searchParams] = useSearchParams();
  const difficulty = searchParams.get('difficulty');
  
  // 根据难度加载题目逻辑
  // ...
  }
  return (
    <div className="quiz-container">
      <div className="quiz-header">
        <h1>答题页面</h1>
        <p>第 {currentPage} 题 / 共 {totalPages} 题</p>
      </div>

      <div className="quiz-content">
        {/* 文本框区域，包含左右切换按钮 */}
        <div className="question-box-wrapper">
          <button 
            className="nav-button prev-button" 
            onClick={handlePrevious}
            disabled={currentPage === 1}
          >
            <ArrowBackIosIcon />
          </button>

          {/* 文本框内容区 */}
          <div className="question-box-content">
            <p>这是第 {currentPage} 题的题目内容：</p>
            <p>请阅读以下材料并回答问题：</p>
            <p>测试测试测试</p>
          </div>

          <button 
            className="nav-button next-button" 
            onClick={handleNext}
            disabled={currentPage === totalPages}
          >
            <ArrowForwardIosIcon />
          </button>
        </div>

        {/* 输入框和提交按钮 */}
        <form className="answer-form">
          <textarea 
            placeholder="请在此输入你的答案..." 
            className="answer-input"
          ></textarea>
          <button type="submit" className="submit-button">
            提交答案
          </button>
        </form>
      </div>

      {/* 底部预留区域 */}
      <div className="quiz-footer-spacer"></div>
    </div>
  );
};

export default QuizPage;