import React, { useState, useEffect } from 'react';
import { Outlet, useNavigate, useLocation } from 'react-router-dom';
import Sidebar from './Sidebar';
import './HomePage.css';
import StarBackground from './StarBackground'; // 引入星空背景组件

const HomePage = () => {
  const navigate = useNavigate();
  const location = useLocation();
  const [userData, setUserData] = useState(null);
  const [isClosed, setIsClosed] = useState(true);
  const [isDarkMode, setIsDarkMode] = useState(false);

  // 检查用户登录状态
  useEffect(() => {
    const user = JSON.parse(localStorage.getItem('user'));
    if (!user) {
      navigate('/login');
    } else {
      setUserData(user);
    }
  }, [navigate]);

  // 菜单项配置
  const menuItems = [
    { icon: 'icon-shouye', text: '主页', path: '/home' },
    { icon: 'icon-lishi', text: '历史记录', path: '/home/history' },
    { icon: 'icon-dati', text: '答题', path: '/home/quiz' },
    { icon: 'icon-baike', text: '百科', path: '/home/encyclopedia' },
    { icon: 'icon-gerenziliao', text: '个人信息', path: '/home/profile' },
  ];

  return (
    <div className={`home-container ${isDarkMode ? 'dark' : ''}`}>
      {/* 星空背景组件 - 放在最底层 */}
      <StarBackground isDarkMode={isDarkMode} />
      
      <Sidebar 
        menuItems={menuItems} 
        userData={userData}
        isClosed={isClosed}
        setIsClosed={setIsClosed}
        isDarkMode={isDarkMode}
        setIsDarkMode={setIsDarkMode}
      />
      <div className={`content-area ${isClosed ? 'closed' : 'open'}`}>
        <Outlet /> {/* 子路由渲染位置 */}
      </div>
    </div>
  );
};

export default HomePage;