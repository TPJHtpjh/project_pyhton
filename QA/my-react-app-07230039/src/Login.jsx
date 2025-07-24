import React, { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom'; 
import './Login.css';
import { login, profile } from './request.jsx';

const Login = () => {
  const [form, setForm] = useState({
    username: '',
    password: ''
  });

  const [errors, setErrors] = useState({});
  const [isLoading, setIsLoading] = useState(false);
  const navigate = useNavigate();

  // 验证函数
  const validate = () => {
    const newErrors = {};

    // 用户名验证
    if (!form.username.trim()) {
      newErrors.username = '用户名不能为空';
    } else if (form.username.length < 3 || form.username.length > 20) {
      newErrors.username = '用户名必须为3-20个字符';
    }

    // 密码验证
    if (!form.password) {
      newErrors.password = '密码不能为空';
    } else if (form.password.length < 8) {
      newErrors.password = '密码至少8个字符';
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleChange = (e) => {
    const { name, value } = e.target;
    setForm({
      ...form,
      [name]: value
    });

    // 实时清除错误提示
    if (errors[name]) {
      setErrors({
        ...errors,
        [name]: ''
      });
    }
  };

  const handleSubmit = (e) => {
    e.preventDefault();

    if (validate()) {
      setIsLoading(true);
      login(form.username, form.password)
        .then((response) => {
          console.log('登录成功', response.data);
          const token = response.data.access_token;
          localStorage.setItem('token', token);

          // 获取用户信息
          profile(token)
            .then((response) => {
              console.log(response);
            })
            .catch((error) => {
              console.error(error);
            });

          navigate('/');
        })
        .catch((error) => {
          console.error('登录失败', error.response?.data || error.message);
          setErrors({ submit: error.response?.data?.message || '登录失败，请检查用户名或密码' });
        })
        .finally(() => {
          setIsLoading(false);
        });
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
              name="username"
              value={form.username}
              onChange={handleChange}
              placeholder="请输入用户名"
              className={errors.username ? 'error' : ''}
            />
            {errors.username && <span className="error-message">{errors.username}</span>}
          </div>

          <div className="form-group">
            <label htmlFor="password">密码</label>
            <input
              type="password"
              id="password"
              name="password"
              value={form.password}
              onChange={handleChange}
              placeholder="请输入密码"
              className={errors.password ? 'error' : ''}
            />
            {errors.password && <span className="error-message">{errors.password}</span>}
          </div>

          {errors.submit && <span className="error-message submit-error">{errors.submit}</span>}

          <button type="submit" disabled={isLoading} className="login-btn">
            {isLoading ? '登录中...' : '登录'}
          </button>
        </form>

        <div className="register-link">
          还没有账号? <Link to="/register">立即注册</Link>
        </div>
    </div>
  );
};

export default Login;