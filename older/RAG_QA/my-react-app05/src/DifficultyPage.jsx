// DifficultyPage.jsx
import React from 'react';
import { useNavigate } from 'react-router-dom';
import { Card, CardContent, Typography, Grid } from '@mui/material';
import './DifficultyPage.css';

const difficultyLevels = [
  { id: 1, name: '随机', color: '#4CAF50' },
  { id: 2, name: '基础', color: '#8BC34A' },
  { id: 3, name: '中等', color: '#FFC107' },
  { id: 4, name: '困难', color: '#FF9800' },
  { id: 5, name: '专家', color: '#F44336' },
];

const DifficultyPage = () => {
  const navigate = useNavigate();

  const handleDifficultySelect = (level) => {
    // 导航到答题页面并传递难度参数
    navigate(`/home/quiz/questions?difficulty=${level}`);
  };

  return (
    <div className="difficulty-page-container">
      <Typography variant="h4" component="h2" className="page-title">
        选择难度级别
      </Typography>
      <Grid container spacing={3} className="difficulty-grid">
        {difficultyLevels.map((level) => (
          <Grid item xs={12} sm={6} md={4} key={level.id}>
            <Card 
              className="difficulty-card"
              style={{ backgroundColor: level.color }}
              onClick={() => handleDifficultySelect(level.id)}
            >
              <CardContent className="difficulty-card-content">
                <Typography variant="h5" component="div" className="difficulty-name">
                  {level.name}
                </Typography>
                <Typography variant="body2" className="difficulty-desc">
                  点击开始 {level.name} 难度挑战
                </Typography>
              </CardContent>
            </Card>
          </Grid>
        ))}
      </Grid>
    </div>
  );
};

export default DifficultyPage;    