#!/usr/bin/env python3
"""
文件名: create_think_ship_db.py
描述: 创建think_ship独立数据库脚本

本脚本负责：
1. 创建独立的think_ship数据库
2. 设置用户权限
3. 创建必要的扩展

注意事项:
   - 需要数据库超级用户权限
   - 为think_ship项目创建独立数据库

作者: Think Ship Team
创建日期: 2024-12-26
最后修改: 2024-12-26
版本: 1.0.0
"""

import sys
from pathlib import Path

import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
from loguru import logger

# 添加项目根目录到Python路径
sys.path.append(str(Path(__file__).parent.parent))

from src.core.config import settings


def create_think_ship_database():
    """创建think_ship数据库的完整流程"""
    
    logger.info("🚀 开始创建think_ship独立数据库...")
    
    # 数据库配置
    admin_user = settings.POSTGRES_ADMIN_USER
    admin_password = settings.POSTGRES_ADMIN_PASSWORD
    app_user = settings.POSTGRES_USER
    app_password = settings.POSTGRES_PASSWORD
    database_name = "think_ship"
    host = settings.POSTGRES_SERVER
    port = settings.POSTGRES_PORT
    
    logger.info(f"📋 配置信息:")
    logger.info(f"   服务器: {host}:{port}")
    logger.info(f"   管理用户: {admin_user}")
    logger.info(f"   应用用户: {app_user}")
    logger.info(f"   目标数据库: {database_name}")
    
    try:
        # 1. 连接到postgres默认数据库
        logger.info("🔗 连接PostgreSQL服务器...")
        conn = psycopg2.connect(
            host=host,
            port=port,
            user=admin_user,
            password=admin_password,
            database="postgres"
        )
        conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        cursor = conn.cursor()
        
        # 检查用户权限
        cursor.execute(
            "SELECT rolname, rolcreatedb, rolsuper FROM pg_roles WHERE rolname = %s",
            (admin_user,)
        )
        result = cursor.fetchone()
        if result:
            logger.info(f"🔑 当前用户权限: 创建数据库={result[1]}, 超级用户={result[2]}")
            if not result[1] and not result[2]:
                logger.error("❌ 当前用户没有创建数据库权限")
                return False
        
        # 2. 检查数据库是否存在
        cursor.execute(
            "SELECT 1 FROM pg_database WHERE datname = %s",
            (database_name,)
        )
        if cursor.fetchone():
            logger.warning(f"⚠️ 数据库 {database_name} 已存在")
            choice = input("是否删除重建? (y/N): ").strip().lower()
            if choice == 'y':
                # 终止所有连接
                cursor.execute(f"""
                    SELECT pg_terminate_backend(pid)
                    FROM pg_stat_activity
                    WHERE datname = '{database_name}' AND pid <> pg_backend_pid()
                """)
                cursor.execute(f'DROP DATABASE IF EXISTS "{database_name}"')
                logger.info(f"🗑️ 已删除数据库 {database_name}")
            else:
                logger.info("取消操作")
                return False
        
        # 3. 创建数据库
        logger.info(f"📊 创建数据库: {database_name}")
        cursor.execute(f'''
            CREATE DATABASE "{database_name}"
            WITH 
                ENCODING = 'UTF8'
                TEMPLATE = template0
                OWNER = "{admin_user}"
        ''')
        logger.success(f"✅ 数据库 {database_name} 创建成功")
        
        cursor.close()
        conn.close()
        
        # 4. 连接到新数据库设置扩展
        logger.info("🔧 设置数据库扩展...")
        conn = psycopg2.connect(
            host=host,
            port=port,
            user=admin_user,
            password=admin_password,
            database=database_name
        )
        conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        cursor = conn.cursor()
        
        # 创建UUID扩展
        cursor.execute('CREATE EXTENSION IF NOT EXISTS "uuid-ossp"')
        logger.info("✅ UUID扩展创建完成")
        
        # 5. 设置应用用户权限
        logger.info("🔐 设置应用用户权限...")
        cursor.execute(f'GRANT ALL PRIVILEGES ON DATABASE "{database_name}" TO "{app_user}"')
        cursor.execute(f'GRANT ALL PRIVILEGES ON SCHEMA public TO "{app_user}"')
        cursor.execute(f'ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON TABLES TO "{app_user}"')
        cursor.execute(f'ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON SEQUENCES TO "{app_user}"')
        
        cursor.close()
        conn.close()
        
        logger.success("🎉 think_ship数据库创建完成！")
        logger.info("📋 数据库信息:")
        logger.info(f"   数据库: {database_name}")
        logger.info(f"   主机: {host}:{port}")
        logger.info(f"   应用用户: {app_user}")
        logger.info(f"   连接URL: postgresql://{app_user}:***@{host}:{port}/{database_name}")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ 创建数据库失败: {e}")
        return False


def main():
    """主函数"""
    # 配置日志
    logger.remove()
    logger.add(
        sys.stdout,
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <level>{message}</level>",
        level="INFO",
        colorize=True
    )
    
    success = create_think_ship_database()
    
    if success:
        logger.success("🎊 数据库创建成功！现在可以运行表创建脚本了")
        logger.info("下一步: python scripts/create_tables.py")
    else:
        logger.error("💥 数据库创建失败")
        logger.info("解决方案:")
        logger.info("1. 联系数据库管理员创建数据库")
        logger.info("2. 获取有CREATEDB权限的用户")
        logger.info("3. 使用postgres超级用户")
        sys.exit(1)


if __name__ == "__main__":
    main()