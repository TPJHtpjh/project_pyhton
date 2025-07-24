import React from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import Login from './Login';
import Register from './Register';
import UserManage from './Usermanage';
import Profile from './Profile';
import ProtectedRoute from './ProtectedRoute';
import HomePage from './HomePage';
import HomeDashboard from './HomeDashboard';
import HistoryPage from './HistoryPage';
import QuizPage from './QuizPage';
import EncyclopediaPage from './EncyclopediaPage';
// import QuizPage from './QuizPage';
// import EncyclopediaPage from './EncyclopediaPage';
import DifficultyPage  from'./DifficultyPage'
import StartPage from './StartPage';
import QuizFlow from './QuizFlow';

function App() {
    return (
        <Router>
            <Routes>
                <Route path="/" element={<Navigate to="/home" replace />} />
                <Route path="/login" element={<Login />} />
                <Route path="/register" element={<Register />} />
{/*                 <Route */}
{/*                     path="/user-manage" */}
{/*                     element={ */}
{/*                         <ProtectedRoute> */}
{/*                             <UserManage /> */}
{/*                         </ProtectedRoute> */}
{/*                     } */}
{/*                 /> */}
                <Route path="/home" element={<HomePage />}>
                    <Route index element={<HomeDashboard />} />
                    {/*//子路由*/}
                    <Route path="encyclopedia" element={<EncyclopediaPage />} />
                    <Route path="history" element={<HistoryPage />} />
                    {/*<Route path="quiz" element={<QuizPage />} />*/}
                    <Route path="encyclopedia" element={<EncyclopediaPage />} />
                    <Route path="profile" element={<ProtectedRoute><Profile /></ProtectedRoute>}/>
                    <Route path="quiz" element={<QuizFlow />}>
                        <Route index element={<StartPage />} /> {/* 默认显示开始页面 */}
                        <Route path="difficulty" element={<DifficultyPage />} />
                        <Route path="questions" element={<QuizPage />} />
                    </Route>
                </Route>
                {/* 其他需要保护的路由也可以这样使用 */}
            </Routes>
        </Router>
    );
}

export default App;