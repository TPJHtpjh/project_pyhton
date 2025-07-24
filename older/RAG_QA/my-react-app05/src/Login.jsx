import React, { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom'; 
import './Login.css';

const Login = () => {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [email, setEmail] = useState(''); 
  const [error, setError] = useState(''); // 添加错误状态
  const navigate = useNavigate(); 

  const handleSubmit = (e) => {
    e.preventDefault();
    
    // 表单验证
    if (!username.trim() || !password.trim() || !email.trim()) {
      setError('请填写所有必填字段');
      return;
    }

    // 示例登录逻辑
    if (username && password && email) {
      // 存储用户信息到localStorage
      const userData = {
        username,
        email
      };
      localStorage.setItem('user', JSON.stringify(userData));
      
      // 登录成功跳转到主页
      navigate('/home');
    } 
  };

  return (
    <div className="login-container">
        <h2>用户登录</h2>
        <form onSubmit={handleSubmit}>
          <div className="form-group">
            <label htmlFor="username">用户名</label>
            <input
              type="text"
              id="username"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              placeholder="请输入用户名"
              required
            />
          </div>
          <div className="form-group">
            <label htmlFor="password">密码</label>
            <input
              type="password"
              id="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder="请输入密码"
              required
            />
          </div>
          <div className="form-group">
            <label htmlFor="email">邮箱</label>
            <input
              type="email"
              id="email"  
              value={email} 
              onChange={(e) => setEmail(e.target.value)} 
              placeholder="请输入邮箱"
              required
            />
          </div>
          <button type="submit" className="login-btn">登录</button>
        </form>
        
        <div className="register-link">
          还没有账号? <Link to="/register">立即注册</Link>
        </div>
    </div>
  );
};

export default Login;