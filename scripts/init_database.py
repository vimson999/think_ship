#!/usr/bin/env python3
"""
文件名: init_database.py
描述: 数据库初始化脚本

本脚本负责：
1. 创建数据库和用户
2. 设置用户权限
3. 创建数据库表结构
4. 初始化基础数据

依赖模块:
   - psycopg2: PostgreSQL适配器
   - sqlalchemy: ORM框架

使用示例:
   >>> python scripts/init_database.py
   >>> python scripts/init_database.py --drop-existing

注意事项:
   - 需要数据库管理员权限
   - 生产环境请谨慎使用 --drop-existing 参数
   - 确保数据库服务已启动

作者: Think Ship Team
创建日期: 2024-12-26
最后修改: 2024-12-26
版本: 1.0.0
"""

import sys
import argparse
import asyncio
from pathlib import Path
from typing import Optional

import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
from sqlalchemy import create_engine, text
from sqlalchemy.ext.asyncio import create_async_engine
from loguru import logger

# 添加项目根目录到Python路径
sys.path.append(str(Path(__file__).parent.parent))

from src.core.config import settings
from src.models.base import Base
from src.models.user import User, Role, UserSession
from src.models.content import HotTopic, Content, PublishRecord, ContentMetrics, ContentTemplate, ContentStateTransition
from src.models.account import Account, AccountHealth


class DatabaseInitializer:
    """数据库初始化器"""
    
    def __init__(self):
        """初始化数据库连接配置"""
        self.admin_user = "cappadocia_man"
        self.admin_password = "2025!!!MANcappaDb"
        self.app_user = "cappa_rw"
        self.app_password = "RWcappaDb!!!2025"
        self.database_name = "think_ship"  # 使用固定的数据库名
        self.host = settings.POSTGRES_SERVER
        self.port = settings.POSTGRES_PORT
        
        # 管理员连接URL（连接到postgres默认数据库）
        self.admin_url = f"postgresql://{self.admin_user}:{self.admin_password}@{self.host}:{self.port}/postgres"
        
        # 管理员连接到目标数据库的URL（用于创建表）
        self.admin_db_url = f"postgresql://{self.admin_user}:{self.admin_password}@{self.host}:{self.port}/{self.database_name}"
        
        # 应用数据库连接URL
        self.app_db_url = f"postgresql://{self.app_user}:{self.app_password}@{self.host}:{self.port}/{self.database_name}"
        self.async_app_db_url = f"postgresql+asyncpg://{self.app_user}:{self.app_password}@{self.host}:{self.port}/{self.database_name}"
    
    def create_database_and_users(self, drop_existing: bool = False) -> bool:
        """
        创建数据库和用户
        
        Args:
            drop_existing: 是否删除已存在的数据库
            
        Returns:
            bool: 是否成功
        """
        try:
            logger.info("🔧 连接到PostgreSQL服务器...")
            
            # 连接到PostgreSQL服务器
            conn = psycopg2.connect(
                host=self.host,
                port=self.port,
                user=self.admin_user,
                password=self.admin_password,
                database="postgres"
            )
            conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
            cursor = conn.cursor()
            
            # 检查数据库是否存在
            cursor.execute(
                "SELECT 1 FROM pg_database WHERE datname = %s",
                (self.database_name,)
            )
            db_exists = cursor.fetchone() is not None
            
            if db_exists and drop_existing:
                logger.warning(f"🗑️ 删除已存在的数据库: {self.database_name}")
                # 终止所有连接到该数据库的会话
                cursor.execute(f"""
                    SELECT pg_terminate_backend(pid)
                    FROM pg_stat_activity
                    WHERE datname = '{self.database_name}' AND pid <> pg_backend_pid()
                """)
                # 删除数据库
                cursor.execute(f'DROP DATABASE IF EXISTS "{self.database_name}"')
                db_exists = False
            
            # 创建数据库
            if not db_exists:
                logger.info(f"📊 创建数据库: {self.database_name}")
                cursor.execute(f'''
                    CREATE DATABASE "{self.database_name}"
                    WITH 
                        ENCODING = 'UTF8'
                        TEMPLATE = template0
                        OWNER = "{self.admin_user}"
                ''')
            else:
                logger.info(f"📊 数据库已存在: {self.database_name}")
            
            # 检查应用用户是否存在
            cursor.execute(
                "SELECT 1 FROM pg_roles WHERE rolname = %s",
                (self.app_user,)
            )
            user_exists = cursor.fetchone() is not None
            
            if not user_exists:
                logger.info(f"👤 创建应用用户: {self.app_user}")
                cursor.execute(f"""
                    CREATE USER "{self.app_user}" WITH 
                        PASSWORD '{self.app_password}'
                        CREATEDB
                        LOGIN
                """)
            else:
                logger.info(f"👤 应用用户已存在: {self.app_user}")
                # 只在必要时更新密码，避免权限问题
                try:
                    cursor.execute(f"""
                        ALTER USER "{self.app_user}" WITH PASSWORD '{self.app_password}'
                    """)
                except Exception as e:
                    logger.warning(f"⚠️ 无法更新用户密码: {e}")
                    logger.info("🔑 使用现有用户继续...")
            
            cursor.close()
            conn.close()
            
            # 连接到新创建的数据库设置权限
            logger.info("🔐 设置数据库权限...")
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
            
            # 授予权限
            cursor.execute(f'GRANT ALL PRIVILEGES ON DATABASE "{self.database_name}" TO "{self.app_user}"')
            cursor.execute(f'GRANT ALL PRIVILEGES ON SCHEMA public TO "{self.app_user}"')
            cursor.execute(f'GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO "{self.app_user}"')
            cursor.execute(f'GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO "{self.app_user}"')
            cursor.execute(f'ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON TABLES TO "{self.app_user}"')
            cursor.execute(f'ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON SEQUENCES TO "{self.app_user}"')
            
            cursor.close()
            conn.close()
            
            logger.success("✅ 数据库和用户创建完成")
            return True
            
        except Exception as e:
            logger.error(f"❌ 创建数据库失败: {e}")
            return False
    
    def create_tables(self) -> bool:
        """
        创建数据库表结构
        
        Returns:
            bool: 是否成功
        """
        try:
            logger.info("🏗️ 创建数据库表结构...")
            
            # 使用管理员权限创建表
            engine = create_engine(self.admin_db_url, echo=True)
            
            # 创建所有表
            Base.metadata.create_all(bind=engine)
            
            # 创建分区表（如果需要）
            with engine.connect() as conn:
                # 为内容表创建按月分区的示例
                conn.execute(text("""
                    -- 创建内容表的分区索引
                    CREATE INDEX IF NOT EXISTS idx_contents_created_month 
                    ON contents (date_trunc('month', created_at));
                    
                    -- 创建内容指标表的分区索引
                    CREATE INDEX IF NOT EXISTS idx_content_metrics_collected_month 
                    ON content_metrics (date_trunc('month', collected_at));
                """))
                
                conn.commit()
            
            engine.dispose()
            
            logger.success("✅ 数据库表创建完成")
            return True
            
        except Exception as e:
            logger.error(f"❌ 创建表失败: {e}")
            return False
    
    def init_basic_data(self) -> bool:
        """
        初始化基础数据
        
        Returns:
            bool: 是否成功
        """
        try:
            logger.info("📝 初始化基础数据...")
            
            # 使用管理员权限插入数据
            engine = create_engine(self.admin_db_url)
            
            with engine.connect() as conn:
                # 插入默认角色
                conn.execute(text("""
                    INSERT INTO roles (id, name, display_name, description, permissions, is_active, created_at, updated_at)
                    VALUES 
                        (uuid_generate_v4(), 'admin', '系统管理员', '拥有所有权限的系统管理员', 
                         '["*"]'::jsonb, true, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP),
                        (uuid_generate_v4(), 'operator', '运营人员', '负责内容运营和发布的人员', 
                         '["content:read", "content:write", "account:read", "publish:write"]'::jsonb, true, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP),
                        (uuid_generate_v4(), 'viewer', '观察者', '只能查看数据的用户', 
                         '["content:read", "account:read", "analytics:read"]'::jsonb, true, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
                    ON CONFLICT (name) DO NOTHING
                """))
                
                # 插入默认内容模板
                conn.execute(text("""
                    INSERT INTO content_templates (id, name, display_name, description, category, template_type, structure, prompt_template, is_active, created_at, updated_at)
                    VALUES 
                        (uuid_generate_v4(), 'tech_article', '科技文章模板', '用于生成科技类文章的模板', 'tech', 'article',
                         '{"sections": ["intro", "main", "conclusion"], "length": "1500-2000"}'::jsonb,
                         '请根据以下热点话题，写一篇{length}字的科技文章。标题：{title}，内容要点：{points}。文章应该包含引言、主体和结论三个部分。',
                         true, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP),
                        (uuid_generate_v4(), 'news_brief', '新闻简报模板', '用于生成新闻简报的模板', 'news', 'short_article',
                         '{"sections": ["headline", "summary", "details"], "length": "800-1200"}'::jsonb,
                         '请根据以下新闻热点，写一篇{length}字的新闻简报。事件：{title}，关键信息：{points}。',
                         true, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
                    ON CONFLICT (name) DO NOTHING
                """))
                
                conn.commit()
            
            engine.dispose()
            
            logger.success("✅ 基础数据初始化完成")
            return True
            
        except Exception as e:
            logger.error(f"❌ 初始化基础数据失败: {e}")
            return False
    
    async def test_connection(self) -> bool:
        """
        测试数据库连接
        
        Returns:
            bool: 连接是否成功
        """
        try:
            logger.info("🔗 测试数据库连接...")
            
            # 测试异步连接
            engine = create_async_engine(self.async_app_db_url)
            
            async with engine.begin() as conn:
                result = await conn.execute(text("SELECT version()"))
                version = result.scalar()
                logger.info(f"📊 PostgreSQL版本: {version}")
                
                # 测试表是否创建成功
                result = await conn.execute(text("""
                    SELECT table_name 
                    FROM information_schema.tables 
                    WHERE table_schema = 'public' 
                    ORDER BY table_name
                """))
                tables = [row[0] for row in result.fetchall()]
                logger.info(f"📋 创建的表: {', '.join(tables)}")
            
            await engine.dispose()
            
            logger.success("✅ 数据库连接测试成功")
            return True
            
        except Exception as e:
            logger.error(f"❌ 数据库连接测试失败: {e}")
            return False
    
    def run_initialization(self, drop_existing: bool = False) -> bool:
        """
        运行完整的初始化流程
        
        Args:
            drop_existing: 是否删除已存在的数据库
            
        Returns:
            bool: 是否成功
        """
        logger.info("🚀 开始数据库初始化...")
        
        # 1. 创建数据库和用户
        if not self.create_database_and_users(drop_existing):
            return False
        
        # 2. 创建表结构
        if not self.create_tables():
            return False
        
        # 3. 初始化基础数据
        if not self.init_basic_data():
            return False
        
        # 4. 测试连接
        success = asyncio.run(self.test_connection())
        
        if success:
            logger.success("🎉 数据库初始化完成！")
            logger.info("📋 连接信息:")
            logger.info(f"   数据库: {self.database_name}")
            logger.info(f"   主机: {self.host}:{self.port}")
            logger.info(f"   用户: {self.app_user}")
            logger.info(f"   连接URL: {self.app_db_url}")
        
        return success


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description="数据库初始化脚本")
    parser.add_argument(
        "--drop-existing",
        action="store_true",
        help="删除已存在的数据库（谨慎使用）"
    )
    parser.add_argument(
        "--log-level",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        default="INFO",
        help="日志级别"
    )
    
    args = parser.parse_args()
    
    # 配置日志
    logger.remove()
    logger.add(
        sys.stdout,
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <level>{message}</level>",
        level=args.log_level,
        colorize=True
    )
    
    # 运行初始化
    initializer = DatabaseInitializer()
    success = initializer.run_initialization(args.drop_existing)
    
    if not success:
        logger.error("💥 数据库初始化失败")
        sys.exit(1)
    
    logger.success("🎊 数据库初始化成功！")


if __name__ == "__main__":
    main()