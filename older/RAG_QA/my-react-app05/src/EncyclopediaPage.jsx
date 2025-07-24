// src/EncyclopediaPage.jsx
import React from 'react';
import './EncyclopediaPage.css';

const EncyclopediaPage = () => {
  const buttons = [
    { id: 1, title: "宇航员知识", color: "#dde6f5ff" },
    { id: 2, title: "宇宙星体", color: "#ecd7e0ff"},
    { id: 3, title: "望远镜知识", color: "#ddd1edff"},
    { id: 4, title: "观星技巧", color: "#ffdcccff"}
  ];

  return (
    <div className="encyclopedia-container">
      <div className="header">
        <h1>太空探索百科</h1>
        <p>探索宇宙的奥秘，开启星际之旅</p>
      </div>
      
      <div className="grid-container">
        {buttons.map((button) => (
          <button 
            key={button.id}
            className="grid-button"
            style={{ 
              backgroundColor: button.color,
              '--hover-color': `${button.color}cc`
            }}
          >
            <div className="icon">{button.icon}</div>
            <div className="title">{button.title}</div>
          </button>
        ))}
      </div>
      
      <div className="footer">
        <p>选择类别开始探索宇宙的奥秘</p>
      </div>
    </div>
  );
};

export default EncyclopediaPage;