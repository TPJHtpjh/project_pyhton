import React, { useState, useEffect } from 'react';
import { Outlet, useNavigate, useLocation } from 'react-router-dom';
import Sidebar from './Sidebar';
import './HomePage.css';
import StarBackground from './StarBackground';
import { all_conversations } from './request.jsx';

const HomePage = () => {
  const navigate = useNavigate();
  const location = useLocation();
  const [userData, setUserData] = useState(null);
  const [isClosed, setIsClosed] = useState(false);
  const [isDarkMode, setIsDarkMode] = useState(false);
  const [activeConversationId, setActiveConversationId] = useState(null);
  const [recentProjects, setRecentProjects] = useState([
      { conversation_id: 1, text: '最近项目 1' },
      { conversation_id: 2, text: '最近项目 2' },
      { conversation_id: 3, text: '最近项目 3' },
      { conversation_id: 4, text: '最近项目 4' },
      { conversation_id: 5, text: '最近项目 5' },
      { conversation_id: 6, text: '最近项目 6' },
      { conversation_id: 7, text: '最近项目 7' },
      { conversation_id: 8, text: '最近项目 8' },
      { conversation_id: 9, text: '最近项目 9' },
      { conversation_id: 10, text: '最近项目 10' }
  ]);

  // 检查用户登录状态
  useEffect(() => {
    const token = localStorage.getItem('token');
    const user = JSON.parse(localStorage.getItem('user'));
    if (!token) {
      navigate('/login');
    } else {
      setUserData(user);
      all_conversations(token).then((response) => {
          console.log(response);
          setRecentProjects(response.data);
      })
    }
  }, [navigate]);

  const handleProjectSelect = (conversationId) => {
      setActiveConversationId(conversationId);
      if (location.pathname !== '/home') {
          navigate('/home');
      }
  };

  // 菜单项配置
  const menuItems = [
    { icon: 'icon-shouye', text: '主页', path: '/home' },
    // { icon: 'icon-lishi', text: '历史记录', path: '/home/history' },
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
            recentItems={recentProjects}
            onProjectSelect={handleProjectSelect}
        />
        <div className={`content-area ${isClosed ? 'closed' : 'open'}`}>
            <Outlet context={{ activeConversationId }} />
        </div>
        {/*       <div className={`content-area ${isClosed ? 'closed' : 'open'}`}> */}
        {/*         <Outlet />  */}{/* 子路由渲染位置 */}
        {/*       </div> */}
      </div>
  );
};

export default HomePage;