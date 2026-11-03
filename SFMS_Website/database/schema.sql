CREATE DATABASE IF NOT EXISTS sfms_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE sfms_db;
CREATE TABLE IF NOT EXISTS tbl_users (
 user_id INT AUTO_INCREMENT PRIMARY KEY,
 username VARCHAR(50) NOT NULL UNIQUE,
 password_hash VARCHAR(255) NOT NULL,
 created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE IF NOT EXISTS tbl_transactions (
 transaction_id INT AUTO_INCREMENT PRIMARY KEY,
 user_id INT NOT NULL,
 transaction_type ENUM('income','expenses') NOT NULL,
 amount DECIMAL(12,2) NOT NULL,
 category VARCHAR(100) NOT NULL DEFAULT '',
 transaction_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
 INDEX idx_transactions_user (user_id),
 CONSTRAINT fk_transactions_user FOREIGN KEY (user_id) REFERENCES tbl_users(user_id) ON DELETE CASCADE
);
CREATE TABLE IF NOT EXISTS tbl_savings_goals (
 goal_id INT AUTO_INCREMENT PRIMARY KEY,
 user_id INT NOT NULL UNIQUE,
 goal_amount DECIMAL(12,2) NOT NULL,
 updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
 CONSTRAINT fk_savings_user FOREIGN KEY (user_id) REFERENCES tbl_users(user_id) ON DELETE CASCADE
);
