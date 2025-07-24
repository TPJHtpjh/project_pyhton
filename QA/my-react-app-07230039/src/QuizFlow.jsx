// QuizFlow.jsx
import { Outlet } from 'react-router-dom';

const QuizFlow = () => {
  return (
    <div className="quiz-flow-container">
      <h2 className="quiz-flow-title">知识挑战</h2>
      
      {/* 渲染子路由内容 */}
      <Outlet />
    </div>
  );
};

export default QuizFlow;