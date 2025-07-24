import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import './Profile.css';
import { profile } from './request.jsx';

const Profile = () => {
  const navigate = useNavigate();
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);

  // 获取当前用户信息
  const fetchUser = async () => {
    try {
      const token = localStorage.getItem('token');
      const { data } = await profile(token);
      setUser(data);
    } catch (err) {
      console.error(err);
      navigate('/login');
    } finally {
      setLoading(false);
    }
  };

  // 退出登录
  const handleLogout = () => {
    try {
      localStorage.removeItem('token');
      navigate('/login');
    } catch (err) {
      console.error('登出失败', err);
    }
  };

  useEffect(() => {
    fetchUser();
  }, []);

  if (loading) return <div className="loading">加载中…</div>;

  if (!user) return <div className="error">获取用户信息失败</div>;

  return (
    <div className="profile-container">
      <div className="profile-card">
        <h2>个人信息</h2>
        
        <div className="profile-info">
          <div className="info-row">
            <span className="info-label">用户 ID:</span>
            <span className="info-value">{user.id}</span>
          </div>

          <div className="info-row">
            <span className="info-label">用户名:</span>
            <span className="info-value">{user.username}</span>
          </div>
          
          <div className="info-row">
            <span className="info-label">邮箱:</span>
            <span className="info-value">{user.email}</span>
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