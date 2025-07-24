import React from 'react';
import ReactDOM from 'react-dom/client';
import Login from './Login'; // 导入Login组件
import './index.css';       // 导入全局样式
import App from './App'
import './app.css';
ReactDOM.createRoot(document.getElementById('root')).render(
  <React.StrictMode>
    {/* <Login /> */}
    <App/>
  </React.StrictMode>
);