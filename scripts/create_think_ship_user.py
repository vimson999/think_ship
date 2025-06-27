#!/usr/bin/env python3
"""
文件名: create_think_ship_user.py
描述: 为think_ship项目创建独立的数据库用户

本脚本负责：
1. 创建think_ship_rw用户
2. 设置独立的权限
3. 确保与其他项目完全隔离

作者: Think Ship Team
创建日期: 2024-12-27
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


def create_think_ship_user():
    """创建think_ship项目的独立用户"""
    
    logger.info("🚀 创建think_ship项目的独立用户...")
    
    # 配置信息
    admin_user = settings.POSTGRES_ADMIN_USER
    admin_password = settings.POSTGRES_ADMIN_PASSWORD
    app_user = settings.POSTGRES_USER  # think_ship_rw
    app_password = settings.POSTGRES_PASSWORD
    database_name = settings.POSTGRES_DB
    host = settings.POSTGRES_SERVER
    port = settings.POSTGRES_PORT
    
    logger.info(f"📋 配置信息:")
    logger.info(f"   服务器: {host}:{port}")
    logger.info(f"   管理用户: {admin_user}")
    logger.info(f"   新用户: {app_user}")
    logger.info(f"   数据库: {database_name}")
    
    try:
        # 连接到postgres数据库
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
        
        # 检查用户是否已存在
        cursor.execute(
            "SELECT 1 FROM pg_roles WHERE rolname = %s",
            (app_user,)
        )
        if cursor.fetchone():
            logger.warning(f"⚠️ 用户 {app_user} 已存在")
            choice = input("是否删除重建? (y/N): ").strip().lower()
            if choice == 'y':
                # 先撤销所有权限
                cursor.execute(f'REVOKE ALL PRIVILEGES ON DATABASE "{database_name}" FROM "{app_user}"')
                cursor.execute(f'DROP USER IF EXISTS "{app_user}"')
                logger.info(f"🗑️ 已删除用户 {app_user}")
            else:
                logger.info("取消操作")
                return False
        
        # 创建新用户
        logger.info(f"👤 创建用户: {app_user}")
        cursor.execute(f"""
            CREATE USER "{app_user}" WITH 
                PASSWORD '{app_password}'
                LOGIN
                NOSUPERUSER
                NOCREATEDB
                NOCREATEROLE
        """)
        logger.success(f"✅ 用户 {app_user} 创建成功")
        
        cursor.close()
        conn.close()
        
        # 连接到think_ship数据库设置权限
        logger.info("🔐 设置用户权限...")
        conn = psycopg2.connect(
            host=host,
            port=port,
            user=admin_user,
            password=admin_password,
            database=database_name
        )
        conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        cursor = conn.cursor()
        
        # 授予数据库权限
        cursor.execute(f'GRANT CONNECT ON DATABASE "{database_name}" TO "{app_user}"')
        cursor.execute(f'GRANT USAGE ON SCHEMA public TO "{app_user}"')
        cursor.execute(f'GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO "{app_user}"')
        cursor.execute(f'GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO "{app_user}"')
        cursor.execute(f'ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT SELECT, INSERT, UPDATE, DELETE ON TABLES TO "{app_user}"')
        cursor.execute(f'ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT USAGE, SELECT ON SEQUENCES TO "{app_user}"')
        
        cursor.close()
        conn.close()
        
        logger.success("🎉 think_ship独立用户创建完成！")
        logger.info("📋 用户信息:")
        logger.info(f"   用户名: {app_user}")
        logger.info(f"   数据库: {database_name}")
        logger.info(f"   权限: 仅限think_ship数据库的读写权限")
        logger.info(f"   连接URL: postgresql://{app_user}:***@{host}:{port}/{database_name}")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ 创建用户失败: {e}")
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
    
    success = create_think_ship_user()
    
    if success:
        logger.success("🎊 独立用户创建成功！")
        logger.info("现在think_ship项目完全独立，不会污染其他项目")
    else:
        logger.error("💥 用户创建失败")
        sys.exit(1)


if __name__ == "__main__":
    main()