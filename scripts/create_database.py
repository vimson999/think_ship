#!/usr/bin/env python3
"""
文件名: create_database.py
描述: 创建数据库脚本

本脚本负责：
1. 连接到PostgreSQL服务器
2. 创建think_ship数据库
3. 创建必要的扩展

前提条件:
   - PostgreSQL服务已启动
   - 管理员用户有创建数据库权限

使用示例:
   >>> python scripts/create_database.py

注意事项:
   - 确保数据库服务已启动
   - 需要管理员权限

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


class DatabaseCreator:
    """数据库创建器"""
    
    def __init__(self):
        """初始化数据库连接配置"""
        # 从环境变量读取数据库配置
        self.admin_user = settings.POSTGRES_ADMIN_USER
        self.admin_password = settings.POSTGRES_ADMIN_PASSWORD
        self.app_user = settings.POSTGRES_USER
        self.app_password = settings.POSTGRES_PASSWORD
        self.database_name = settings.POSTGRES_DB
        self.host = settings.POSTGRES_SERVER
        self.port = settings.POSTGRES_PORT
    
    def test_connection(self) -> bool:
        """
        测试PostgreSQL服务器连接
        
        Returns:
            bool: 连接是否成功
        """
        try:
            logger.info("🔗 测试PostgreSQL服务器连接...")
            
            # 连接到postgres默认数据库
            conn = psycopg2.connect(
                host=self.host,
                port=self.port,
                user=self.admin_user,
                password=self.admin_password,
                database="postgres"
            )
            cursor = conn.cursor()
            cursor.execute("SELECT version()")
            version = cursor.fetchone()[0]
            logger.info(f"📊 PostgreSQL版本: {version}")
            cursor.close()
            conn.close()
            
            logger.success("✅ PostgreSQL服务器连接成功")
            return True
            
        except Exception as e:
            logger.error(f"❌ PostgreSQL服务器连接失败: {e}")
            return False
    
    def check_database_exists(self) -> bool:
        """
        检查数据库是否存在
        
        Returns:
            bool: 数据库是否存在
        """
        try:
            conn = psycopg2.connect(
                host=self.host,
                port=self.port,
                user=self.admin_user,
                password=self.admin_password,
                database="postgres"
            )
            cursor = conn.cursor()
            
            cursor.execute(
                "SELECT 1 FROM pg_database WHERE datname = %s",
                (self.database_name,)
            )
            exists = cursor.fetchone() is not None
            
            cursor.close()
            conn.close()
            
            return exists
            
        except Exception as e:
            logger.error(f"❌ 检查数据库存在性失败: {e}")
            return False
    
    def create_database(self) -> bool:
        """
        创建数据库
        
        Returns:
            bool: 是否成功
        """
        try:
            logger.info(f"📊 创建数据库: {self.database_name}")
            
            conn = psycopg2.connect(
                host=self.host,
                port=self.port,
                user=self.admin_user,
                password=self.admin_password,
                database="postgres"
            )
            conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
            cursor = conn.cursor()
            
            # 创建数据库
            cursor.execute(f'''
                CREATE DATABASE "{self.database_name}"
                WITH 
                    ENCODING = 'UTF8'
                    TEMPLATE = template0
                    OWNER = "{self.admin_user}"
            ''')
            
            cursor.close()
            conn.close()
            
            logger.success(f"✅ 数据库 {self.database_name} 创建成功")
            return True
            
        except Exception as e:
            logger.error(f"❌ 创建数据库失败: {e}")
            return False
    
    def create_extensions(self) -> bool:
        """
        创建数据库扩展
        
        Returns:
            bool: 是否成功
        """
        try:
            logger.info("🔧 创建数据库扩展...")
            
            conn = psycopg2.connect(
                host=self.host,
                port=self.port,
                user=self.admin_user,
                password=self.admin_password,
                database=self.database_name
            )
            conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
            cursor = conn.cursor()
            
            # 创建UUID扩展
            cursor.execute('CREATE EXTENSION IF NOT EXISTS "uuid-ossp"')
            logger.info("✅ UUID扩展创建完成")
            
            cursor.close()
            conn.close()
            
            return True
            
        except Exception as e:
            logger.error(f"❌ 创建扩展失败: {e}")
            return False
    
    def check_user_exists(self) -> bool:
        """
        检查应用用户是否存在
        
        Returns:
            bool: 用户是否存在
        """
        try:
            conn = psycopg2.connect(
                host=self.host,
                port=self.port,
                user=self.admin_user,
                password=self.admin_password,
                database="postgres"
            )
            cursor = conn.cursor()
            
            cursor.execute(
                "SELECT 1 FROM pg_roles WHERE rolname = %s",
                (self.app_user,)
            )
            exists = cursor.fetchone() is not None
            
            cursor.close()
            conn.close()
            
            return exists
            
        except Exception as e:
            logger.error(f"❌ 检查用户存在性失败: {e}")
            return False
    
    def create_user(self) -> bool:
        """
        创建应用用户
        
        Returns:
            bool: 是否成功
        """
        try:
            logger.info(f"👤 创建应用用户: {self.app_user}")
            
            conn = psycopg2.connect(
                host=self.host,
                port=self.port,
                user=self.admin_user,
                password=self.admin_password,
                database="postgres"
            )
            conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
            cursor = conn.cursor()
            
            # 创建用户
            cursor.execute(f"""
                CREATE USER "{self.app_user}" WITH 
                    PASSWORD '{self.app_password}'
                    LOGIN
            """)
            
            cursor.close()
            conn.close()
            
            logger.success(f"✅ 用户 {self.app_user} 创建成功")
            return True
            
        except Exception as e:
            logger.error(f"❌ 创建用户失败: {e}")
            return False
    
    def grant_permissions(self) -> bool:
        """
        授予用户权限
        
        Returns:
            bool: 是否成功
        """
        try:
            logger.info("🔐 设置用户权限...")
            
            conn = psycopg2.connect(
                host=self.host,
                port=self.port,
                user=self.admin_user,
                password=self.admin_password,
                database=self.database_name
            )
            conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
            cursor = conn.cursor()
            
            # 授予数据库权限
            cursor.execute(f'GRANT ALL PRIVILEGES ON DATABASE "{self.database_name}" TO "{self.app_user}"')
            cursor.execute(f'GRANT ALL PRIVILEGES ON SCHEMA public TO "{self.app_user}"')
            cursor.execute(f'ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON TABLES TO "{self.app_user}"')
            cursor.execute(f'ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON SEQUENCES TO "{self.app_user}"')
            
            cursor.close()
            conn.close()
            
            logger.success("✅ 用户权限设置完成")
            return True
            
        except Exception as e:
            logger.error(f"❌ 设置权限失败: {e}")
            return False
    
    def run_creation(self) -> bool:
        """
        运行完整的数据库创建流程
        
        Returns:
            bool: 是否成功
        """
        logger.info("🚀 开始创建数据库...")
        
        # 1. 测试连接
        if not self.test_connection():
            return False
        
        # 2. 检查数据库是否已存在
        if self.check_database_exists():
            logger.info(f"📊 数据库 {self.database_name} 已存在")
        else:
            # 3. 创建数据库
            if not self.create_database():
                return False
        
        # 4. 创建扩展
        if not self.create_extensions():
            return False
        
        # 5. 检查用户是否存在
        if self.check_user_exists():
            logger.info(f"👤 用户 {self.app_user} 已存在")
        else:
            # 6. 创建用户
            if not self.create_user():
                return False
        
        # 7. 授予权限
        if not self.grant_permissions():
            return False
        
        logger.success("🎉 数据库创建完成！")
        logger.info("📋 数据库信息:")
        logger.info(f"   数据库: {self.database_name}")
        logger.info(f"   主机: {self.host}:{self.port}")
        logger.info(f"   管理用户: {self.admin_user}")
        logger.info(f"   应用用户: {self.app_user}")
        
        return True


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
    
    # 运行创建
    creator = DatabaseCreator()
    success = creator.run_creation()
    
    if not success:
        logger.error("💥 数据库创建失败")
        sys.exit(1)
    
    logger.success("🎊 数据库创建成功！")


if __name__ == "__main__":
    main()