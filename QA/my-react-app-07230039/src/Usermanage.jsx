import React, { useEffect, useState } from 'react';
import './UserManage.css';
import { profile } from './request.jsx';
import { useNavigate } from 'react-router-dom';

const UserManage = () => {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);
  const navigate = useNavigate();

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
    <div className="user-manage-container">
      <h2>用户管理</h2>

      <table className="user-table">
        <thead>
          <tr>
            <th>用户 ID</th>
            <th>用户名</th>
            <th>邮箱</th>
            <th>操作</th>
          </tr>
        </thead>
        <tbody>
          <tr>
            <td>{user.id}</td>
            <td>{user.username}</td>
            <td>{user.email}</td>
            <td>
              <button className="logout-btn" onClick={handleLogout}>
                退出登录
              </button>
            </td>
          </tr>
        </tbody>
      </table>
    </div>
  );
};

export default UserManage;