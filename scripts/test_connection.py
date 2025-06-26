#!/usr/bin/env python3
"""
测试数据库连接脚本
"""

import sys
import urllib.parse
from pathlib import Path

import psycopg2
from loguru import logger

# 添加项目根目录到Python路径
sys.path.append(str(Path(__file__).parent.parent))

from src.core.config import settings


def test_connections():
    """测试各种数据库连接"""
    
    logger.info("📋 当前配置:")
    logger.info(f"   服务器: {settings.POSTGRES_SERVER}:{settings.POSTGRES_PORT}")
    logger.info(f"   应用用户: {settings.POSTGRES_USER}")
    logger.info(f"   应用密码: {settings.POSTGRES_PASSWORD}")
    logger.info(f"   管理用户: {settings.POSTGRES_ADMIN_USER}")
    logger.info(f"   管理密码: {settings.POSTGRES_ADMIN_PASSWORD}")
    logger.info(f"   数据库: {settings.POSTGRES_DB}")
    
    # 测试连接到 cappadocia_v1 数据库 (使用应用用户)
    logger.info("\n🔗 测试连接到 cappadocia_v1 (应用用户)...")
    try:
        conn = psycopg2.connect(
            host=settings.POSTGRES_SERVER,
            port=settings.POSTGRES_PORT,
            user=settings.POSTGRES_USER,
            password=settings.POSTGRES_PASSWORD,
            database="cappadocia_v1"
        )
        cursor = conn.cursor()
        cursor.execute("SELECT version()")
        version = cursor.fetchone()[0]
        logger.success(f"✅ 连接成功: {version}")
        
        # 查看现有表
        cursor.execute("""
            SELECT table_name FROM information_schema.tables 
            WHERE table_schema = 'public' ORDER BY table_name
        """)
        tables = [row[0] for row in cursor.fetchall()]
        logger.info(f"📋 现有表 ({len(tables)}个): {', '.join(tables) if tables else '无'}")
        
        cursor.close()
        conn.close()
        
    except Exception as e:
        logger.error(f"❌ 连接失败: {e}")
    
    # 测试连接到 postgres 数据库 (使用管理用户)
    logger.info("\n🔗 测试连接到 postgres (管理用户)...")
    try:
        conn = psycopg2.connect(
            host=settings.POSTGRES_SERVER,
            port=settings.POSTGRES_PORT,
            user=settings.POSTGRES_ADMIN_USER,
            password=settings.POSTGRES_ADMIN_PASSWORD,
            database="postgres"
        )
        cursor = conn.cursor()
        
        # 检查用户权限
        cursor.execute(
            "SELECT rolname, rolcreatedb, rolsuper, rolcreaterole FROM pg_roles WHERE rolname = %s",
            (settings.POSTGRES_ADMIN_USER,)
        )
        result = cursor.fetchone()
        if result:
            logger.success(f"✅ 管理用户连接成功")
            logger.info(f"🔑 权限: 创建数据库={result[1]}, 超级用户={result[2]}, 创建角色={result[3]}")
        
        # 查看所有数据库
        cursor.execute("SELECT datname FROM pg_database WHERE datistemplate = false")
        databases = [row[0] for row in cursor.fetchall()]
        logger.info(f"📊 现有数据库: {', '.join(databases)}")
        
        cursor.close()
        conn.close()
        
    except Exception as e:
        logger.error(f"❌ 管理用户连接失败: {e}")


if __name__ == "__main__":
    # 配置日志
    logger.remove()
    logger.add(
        sys.stdout,
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <level>{message}</level>",
        level="INFO",
        colorize=True
    )
    
    test_connections()