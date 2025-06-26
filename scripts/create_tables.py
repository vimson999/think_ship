#!/usr/bin/env python3
"""
文件名: create_tables.py
描述: 数据库表结构创建脚本

本脚本负责：
1. 连接到已存在的数据库
2. 创建所有数据库表
3. 初始化基础数据

前提条件:
   - PostgreSQL服务已启动
   - 数据库 think_ship 已创建
   - 用户 cappadocia_man 有建表权限
   - 用户 cappa_rw 有读写权限

使用示例:
   >>> python scripts/create_tables.py

注意事项:
   - 确保数据库服务已启动
   - 确保数据库已手动创建

作者: Think Ship Team
创建日期: 2024-12-26
最后修改: 2024-12-26
版本: 1.0.0
"""

import sys
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


class TableCreator:
    """表结构创建器"""
    
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
        
        # 管理员连接到目标数据库的URL（用于创建表）
        self.admin_db_url = f"postgresql://{self.admin_user}:{self.admin_password}@{self.host}:{self.port}/{self.database_name}"
        
        # 应用数据库连接URL
        self.app_db_url = f"postgresql://{self.app_user}:{self.app_password}@{self.host}:{self.port}/{self.database_name}"
        self.async_app_db_url = f"postgresql+asyncpg://{self.app_user}:{self.app_password}@{self.host}:{self.port}/{self.database_name}"
    
    def test_connection(self) -> bool:
        """
        测试数据库连接
        
        Returns:
            bool: 连接是否成功
        """
        try:
            logger.info("🔗 测试数据库连接...")
            
            # 测试管理员连接
            conn = psycopg2.connect(
                host=self.host,
                port=self.port,
                user=self.admin_user,
                password=self.admin_password,
                database=self.database_name
            )
            cursor = conn.cursor()
            cursor.execute("SELECT version()")
            version = cursor.fetchone()[0]
            logger.info(f"📊 PostgreSQL版本: {version}")
            cursor.close()
            conn.close()
            
            logger.success("✅ 数据库连接测试成功")
            return True
            
        except Exception as e:
            logger.error(f"❌ 数据库连接测试失败: {e}")
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
    
    def create_tables(self) -> bool:
        """
        创建数据库表结构
        
        Returns:
            bool: 是否成功
        """
        try:
            logger.info("🏗️ 创建数据库表结构...")
            
            # 导入所有模型以确保它们被注册
            from src.models.user import User, Role, UserSession
            from src.models.content import (
                HotTopic, Content, PublishRecord, ContentMetrics, 
                ContentTemplate, ContentStateTransition
            )
            from src.models.account import Account, AccountHealth
            
            # 使用管理员权限创建表
            engine = create_engine(self.admin_db_url, echo=True)
            
            # 创建所有表
            Base.metadata.create_all(bind=engine)
            
            # 创建额外的索引
            with engine.connect() as conn:
                logger.info("📋 创建额外索引...")
                
                # 创建基础索引（避免使用函数索引）
                conn.execute(text("""
                    -- 创建账号健康度的日期索引
                    CREATE INDEX IF NOT EXISTS idx_account_health_date 
                    ON account_health (account_id, date);
                    
                    -- 创建内容表的时间索引
                    CREATE INDEX IF NOT EXISTS idx_contents_created_at 
                    ON contents (created_at);
                    
                    -- 创建内容指标表的时间索引
                    CREATE INDEX IF NOT EXISTS idx_content_metrics_collected_at 
                    ON content_metrics (collected_at);
                """))
                
                conn.commit()
            
            engine.dispose()
            
            logger.success("✅ 数据库表创建完成")
            return True
            
        except Exception as e:
            logger.error(f"❌ 创建表失败: {e}")
            return False
    
    def set_permissions(self) -> bool:
        """
        设置用户权限
        
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
            
            # 授予cappa_rw用户表权限
            cursor.execute(f'GRANT USAGE ON SCHEMA public TO "{self.app_user}"')
            cursor.execute(f'GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO "{self.app_user}"')
            cursor.execute(f'GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO "{self.app_user}"')
            cursor.execute(f'ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT SELECT, INSERT, UPDATE, DELETE ON TABLES TO "{self.app_user}"')
            cursor.execute(f'ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT USAGE, SELECT ON SEQUENCES TO "{self.app_user}"')
            
            cursor.close()
            conn.close()
            
            logger.success("✅ 用户权限设置完成")
            return True
            
        except Exception as e:
            logger.error(f"❌ 设置权限失败: {e}")
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
    
    async def test_app_connection(self) -> bool:
        """
        测试应用用户连接
        
        Returns:
            bool: 连接是否成功
        """
        try:
            logger.info("🔗 测试应用用户连接...")
            
            # 测试异步连接
            engine = create_async_engine(self.async_app_db_url)
            
            async with engine.begin() as conn:
                result = await conn.execute(text("SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = 'public'"))
                table_count = result.scalar()
                logger.info(f"📋 数据库表数量: {table_count}")
                
                # 测试表查询
                result = await conn.execute(text("SELECT COUNT(*) FROM roles"))
                role_count = result.scalar()
                logger.info(f"👥 默认角色数量: {role_count}")
            
            await engine.dispose()
            
            logger.success("✅ 应用用户连接测试成功")
            return True
            
        except Exception as e:
            logger.error(f"❌ 应用用户连接测试失败: {e}")
            return False
    
    def run_creation(self) -> bool:
        """
        运行完整的表创建流程
        
        Returns:
            bool: 是否成功
        """
        logger.info("🚀 开始创建数据库表...")
        
        # 1. 测试连接
        if not self.test_connection():
            return False
        
        # 2. 创建扩展
        if not self.create_extensions():
            return False
        
        # 3. 创建表结构
        if not self.create_tables():
            return False
        
        # 4. 设置权限
        if not self.set_permissions():
            return False
        
        # 5. 初始化基础数据
        if not self.init_basic_data():
            return False
        
        # 6. 测试应用连接
        success = asyncio.run(self.test_app_connection())
        
        if success:
            logger.success("🎉 数据库表创建完成！")
            logger.info("📋 连接信息:")
            logger.info(f"   数据库: {self.database_name}")
            logger.info(f"   主机: {self.host}:{self.port}")
            logger.info(f"   管理用户: {self.admin_user}")
            logger.info(f"   应用用户: {self.app_user}")
        
        return success


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
    creator = TableCreator()
    success = creator.run_creation()
    
    if not success:
        logger.error("💥 数据库表创建失败")
        sys.exit(1)
    
    logger.success("🎊 数据库表创建成功！")


if __name__ == "__main__":
    main()