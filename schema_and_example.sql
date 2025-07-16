-- MySQL 表结构定义
CREATE TABLE IF NOT EXISTS folders (
    id INT AUTO_INCREMENT PRIMARY KEY,
    path VARCHAR(512) NOT NULL UNIQUE,
    parent_id INT NULL,
    FOREIGN KEY (parent_id) REFERENCES folders(id)
);

CREATE TABLE IF NOT EXISTS files (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    folder_id INT NOT NULL,
    file_type VARCHAR(50),
    FOREIGN KEY (folder_id) REFERENCES folders(id)
);

-- 手动插入目录结构示例（需按层级顺序插入）
INSERT IGNORE INTO folders (path, parent_id) VALUES 
    ('root_folder', NULL),
    ('root_folder/sub1', (SELECT id FROM folders WHERE path = 'root_folder')),
    ('root_folder/sub2', (SELECT id FROM folders WHERE path = 'root_folder'));

-- 路径转换函数示例
DELIMITER //
CREATE FUNCTION normalize_path(input_path VARCHAR(512))
RETURNS VARCHAR(512) DETERMINISTIC
BEGIN
    RETURN REPLACE(input_path, '\\', '/');
END//
DELIMITER ;

-- 递归查询示例
WITH RECURSIVE folder_tree AS (
    SELECT id, path, parent_id
    FROM folders
    WHERE path = 'root_folder'
    UNION ALL
    SELECT f.id, f.path, f.parent_id
    FROM folders f
    INNER JOIN folder_tree ft ON ft.id = f.parent_id
)
SELECT * FROM folder_tree;