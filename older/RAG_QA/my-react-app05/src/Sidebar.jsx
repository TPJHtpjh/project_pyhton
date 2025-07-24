import React, { useState, useEffect } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import './Sidebar.css';

const Sidebar = ({ 
  menuItems = [], 
  userData, 
  isClosed, 
  setIsClosed,
  isDarkMode,
  setIsDarkMode
}) => {
  const navigate = useNavigate();

  // 处理主题切换的逻辑
  useEffect(() => {
    if (isDarkMode) {
      document.body.classList.add('dark');
    } else {
      document.body.classList.remove('dark');
    }
  }, [isDarkMode]);
  
  return (
    <nav className={`shell ${isClosed ? 'close' : ''}`}>
      <header>
        <div className="image-text">
          <div className="text logo-text">
            <span className="name">待取名</span>
          </div>
        </div>
        <i 
          className="iconfont icon-xiangyoujiantou toggle" 
          onClick={() => setIsClosed(!isClosed)}
        ></i>
      </header>
      
      <div className="menu-bar">
        <div className="menu">
          <ul className="menu-links">
            {menuItems.map((item, index) => (
              <li className="nav-link" key={index}>
                <Link to={item.path}>
                  <i className={`iconfont ${item.icon} icon`}></i>
                  <span className="text nac-text">{item.text}</span>
                </Link>
              </li>
            ))}
          </ul>
        </div>
        
        <div className="bottom-content">
          
          <li 
            className="mode" 
            onClick={() => setIsDarkMode(!isDarkMode)}
          >
            <div className="sun-moon">
              <i className="iconfont icon-rijian icon sun"></i>
              <i className="iconfont icon-yejian icon moon"></i>
            </div>
            <span className="mode-text text">
              {isDarkMode ? '白日模式' : '夜间模式'}
            </span>
            <div className="toggle-switch">
              <span className="switch"></span>
            </div>
          </li>
        </div>
      </div>
    </nav>
  );
};

export default Sidebar;