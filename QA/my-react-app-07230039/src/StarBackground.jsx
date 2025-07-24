import React, { useEffect, useRef } from 'react';
import './StarBackground.css';

const StarBackground = ({ isDarkMode }) => {
  const starContainerRef = useRef(null);

  // 创建星星
  const createStars = () => {
    if (!starContainerRef.current || !isDarkMode) return;
    
    // 清除现有星星（避免累积）
    while (starContainerRef.current.firstChild) {
      starContainerRef.current.removeChild(starContainerRef.current.firstChild);
    }
    
    // 一次生成20颗星星
    for (let i = 0; i < 20; i++) {
      const star = document.createElement('div');
      star.classList.add('star');
      
      // 随机大小（2-5px）
      const size = Math.random() * 3 + 2;
      star.style.width = `${size}px`;
      star.style.height = `${size}px`;
      
      // 随机位置
      star.style.left = `${Math.random() * 100}%`;
      star.style.top = `${Math.random() * 100}%`;
      
      // 随机动画延迟和持续时间
      star.style.animationDelay = `${Math.random() * 5}s`;
      star.style.animationDuration = `${Math.random() * 5 + 5}s`;
      
      starContainerRef.current.appendChild(star);
    }
  };

  // 创建流星
  const createMeteor = () => {
    if (!starContainerRef.current || !isDarkMode) return;
    
    const meteor = document.createElement('div');
    meteor.classList.add('meteor');
    
    // 随机长度（80-150px）
    const length = Math.random() * 70 + 80;
    meteor.style.width = `${length}px`;
    
    // 随机位置（右侧进入）
    meteor.style.right = `${Math.random() * 50 + 50}%`;
    meteor.style.top = `${Math.random() * 30}%`;
    
    // 随机动画持续时间
    meteor.style.animationDuration = `${Math.random() * 1 + 0.5}s`;
    
    starContainerRef.current.appendChild(meteor);
    
    // 流星消失后移除元素
    setTimeout(() => {
      if (meteor.parentNode === starContainerRef.current) {
        starContainerRef.current.removeChild(meteor);
      }
    }, 1500);
  };

  // 处理暗黑模式切换和组件生命周期
  useEffect(() => {
    if (isDarkMode) {
      // 初始创建星星
      createStars();
      // 定时生成新星星
      const starInterval = setInterval(createStars, 5000);
      // 定时生成流星
      const meteorInterval = setInterval(createMeteor, 3000);
      
      return () => {
        clearInterval(starInterval);
        clearInterval(meteorInterval);
      };
    }
  }, [isDarkMode]);

  return (
    <div 
      ref={starContainerRef} 
      className={`star-background ${isDarkMode ? 'active' : ''}`}
    />
  );
};

export default StarBackground;