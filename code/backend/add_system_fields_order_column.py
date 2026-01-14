"""
数据库迁移脚本：为 process_sys_form_config 表添加 system_fields_order 字段
"""

from app import app, db
from sqlalchemy import text

def add_system_fields_order_column():
    """为表单配置表添加 system_fields_order 字段"""
    with app.app_context():
        try:
            # 检查字段是否已存在
            inspector = db.inspect(db.engine)
            columns = [col['name'] for col in inspector.get_columns('process_sys_form_config')]
            
            if 'system_fields_order' in columns:
                print("字段 system_fields_order 已存在，无需添加")
                return
            
            # 添加字段
            print("正在添加 system_fields_order 字段...")
            with db.engine.connect() as conn:
                # SQL Server 语法
                conn.execute(text("""
                    ALTER TABLE process_sys_form_config 
                    ADD system_fields_order NVARCHAR(MAX) NULL
                """))
                conn.commit()
            
            print("字段 system_fields_order 添加成功！")
        except Exception as e:
            print(f"添加字段失败: {e}")
            print("如果字段已存在，可以忽略此错误")

if __name__ == '__main__':
    print("开始数据库迁移...")
    add_system_fields_order_column()
    print("数据库迁移完成！")

