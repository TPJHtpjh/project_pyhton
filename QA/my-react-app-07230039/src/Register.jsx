import React, { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { register } from './request.jsx';
import './Register.css';

const Register = () => {
  const [form, setForm] = useState({
    username: '',
    email: '',
    password: '',
    confirmPassword: ''
  });

  const [errors, setErrors] = useState({});
  const [backendError, setBackendError] = useState('');
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

    // 邮箱验证
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    if (!form.email.trim()) {
      newErrors.email = '邮箱不能为空';
    } else if (!emailRegex.test(form.email)) {
      newErrors.email = '请输入有效的邮箱格式';
    }

    // 密码验证
    const passwordRegex = /^(?=.*[A-Za-z])(?=.*\d)[A-Za-z\d]{8,}$/;
    if (!form.password) {
      newErrors.password = '密码不能为空';
    } else if (!passwordRegex.test(form.password)) {
      newErrors.password = '密码至少8个字符，且必须包含字母和数字';
    }

    // 确认密码验证
    if (!form.confirmPassword) {
      newErrors.confirmPassword = '请确认密码';
    } else if (form.password !== form.confirmPassword) {
      newErrors.confirmPassword = '两次输入的密码不一致';
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
    setBackendError('');

    if (validate()) {
      console.log('注册信息:', form);
      register(form.username, form.email, form.password)
        .then((response) => {
          console.log(response);
          navigate('/login');
        }).catch((error) => {
  const { status, data } = error.response || {};
  if (status === 409) {
    const msg = data?.detail || '用户名或邮箱已存在';
    setBackendError(msg);
  } else if (status === 500) {
    setBackendError('服务器异常，请稍后重试');
  } else {
    setBackendError('注册失败，请检查网络');
  }
  console.error('注册失败', data || error.message);
});
//         .catch((error) => {
//           console.error('注册失败', error.response?.data || error.message);
//         });
    }
  };

  return (
    <div className="register-container">
      <h2>用户注册</h2>
      {backendError && <div className="backend-error">{backendError}</div>}
      <form onSubmit={handleSubmit}>
        <div className="form-group">
          <label htmlFor="username">用户名</label>
          <input
            type="text"
            id="username"
            name="username"
            value={form.username}
            onChange={handleChange}
            className={errors.username ? 'error' : ''}
          />
          {errors.username && <span className="error-message">{errors.username}</span>}
        </div>

        <div className="form-group">
          <label htmlFor="email">邮箱</label>
          <input
            type="email"
            id="email"
            name="email"
            value={form.email}
            onChange={handleChange}
            className={errors.email ? 'error' : ''}
          />
          {errors.email && <span className="error-message">{errors.email}</span>}
        </div>

        <div className="form-group">
          <label htmlFor="password">密码</label>
          <input
            type="password"
            id="password"
            name="password"
            value={form.password}
            onChange={handleChange}
            className={errors.password ? 'error' : ''}
          />
          {errors.password && <span className="error-message">{errors.password}</span>}
        </div>

        <div className="form-group">
          <label htmlFor="confirmPassword">确认密码</label>
          <input
            type="password"
            id="confirmPassword"
            name="confirmPassword"
            value={form.confirmPassword}
            onChange={handleChange}
            className={errors.confirmPassword ? 'error' : ''}
          />
          {errors.confirmPassword && <span className="error-message">{errors.confirmPassword}</span>}
        </div>

        <button type="submit" disabled={Object.keys(errors).length > 0}>注册</button>
      </form>
      
      <div className="link-container">
        <p>已有账号？<Link to="/login">立即登录</Link></p>
      </div>
    </div>
  );
};

export default Register;