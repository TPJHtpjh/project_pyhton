import React from 'react';
import { useNavigate } from 'react-router-dom';
import './Profile.css';

const Profile = () => {
  const navigate = useNavigate();
  
  // 从本地存储获取用户信息
  const userData = JSON.parse(localStorage.getItem('user')) || {
    username: '示例用户',
    email: 'example@domain.com'
  };

  const handleLogout = () => {
    // 清除用户数据
    localStorage.removeItem('user');
    // 跳转到登录页面
    navigate('/login');
  };

  return (
    <div className="profile-container">
      <div className="profile-card">
        <h2>个人信息</h2>
        
        <div className="profile-info">
          <div className="info-row">
            <span className="info-label">用户名:</span>
            <span className="info-value">{userData.username}</span>
          </div>
          
          <div className="info-row">
            <span className="info-label">邮箱:</span>
            <span className="info-value">{userData.email}</span>
          </div>
        </div>
        
        <button 
          className="logout-button"
          onClick={handleLogout}
        >
          退出登录
        </button>
      </div>
    </div>
  );
};

export default Profile;