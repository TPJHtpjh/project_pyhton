import React from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import Login from './Login';
import Register from './Register';
import Profile from './Profile';
import HomePage from './HomePage';
import HomeDashboard from './HomeDashboard'; 
import HistoryPage from './HistoryPage';    
import QuizPage from './QuizPage';          
import EncyclopediaPage from './EncyclopediaPage'; 
import DifficultyPage  from'./DifficultyPage'
import StartPage from './StartPage';
import QuizFlow from './QuizFlow';

function App() {
  return (
    <Router>
        <Routes>
          <Route path="/login" element={<Login />} />
          <Route path="/register" element={<Register />} />
          <Route path="/home" element={<HomePage />}>
           <Route index element={<HomeDashboard />} />
           {/* 子路由 */}
           <Route path="history" element={<HistoryPage />} />
           <Route path="encyclopedia" element={<EncyclopediaPage />} />
           <Route path="profile" element={<Profile />} />
           {/* 答题流程的嵌套路由 */}
           <Route path="quiz" element={<QuizFlow />}>
             <Route index element={<StartPage />} /> {/* 默认显示开始页面 */}
             <Route path="difficulty" element={<DifficultyPage />} />
             <Route path="questions" element={<QuizPage />} />
           </Route>
        </Route>
        <Route path="/" element={<Navigate to="/login" replace />} />
        <Route path="*" element={<Navigate to="/login" replace />} />
        </Routes>
    </Router>
  );
}

export default App;