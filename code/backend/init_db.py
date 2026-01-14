"""
数据库初始化脚本
用于创建所有数据表
"""

from app import app, init_db

if __name__ == '__main__':
    print("开始初始化数据库...")
    init_db()
    print("数据库初始化完成！")

