#!/usr/bin/env python3
"""
文件名: auto_cleanup_cappa_db.py
描述: 自动清理cappadocia_v1数据库中的think_ship相关表（无需用户确认）

本脚本负责：
1. 检查cappadocia_v1数据库中的think_ship相关表
2. 自动删除这些污染表
3. 恢复cappadocia_v1数据库的原始状态

注意事项:
   - 需要管理员权限
   - 会删除数据，请谨慎操作
   - 自动执行，无需用户确认

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


def auto_cleanup_cappa_database():
    """自动清理cappadocia_v1数据库中的think_ship表"""
    
    logger.info("🧹 自动清理cappadocia_v1数据库中的think_ship污染表...")
    
    # 使用postgres超级用户
    admin_user = "postgres"
    admin_password = "psl#@!logIN4SS2000"
    host = "101.35.56.140"
    port = 5432
    database_name = "cappadocia_v1"
    
    # think_ship相关的表名
    think_ship_tables = [
        'content_state_transitions',
        'content_metrics', 
        'publish_records',
        'contents',
        'content_templates',
        'hot_topics',
        'account_health',
        'accounts',
        'user_sessions',
        'user_roles',
        'users',
        'roles'
    ]
    
    logger.info(f"📋 配置信息:")
    logger.info(f"   服务器: {host}:{port}")
    logger.info(f"   数据库: {database_name}")
    logger.info(f"   需要清理的表: {len(think_ship_tables)}个")
    
    try:
        # 连接到cappadocia_v1数据库
        logger.info("🔗 连接cappadocia_v1数据库...")
        conn = psycopg2.connect(
            host=host,
            port=port,
            user=admin_user,
            password=admin_password,
            database=database_name
        )
        conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        cursor = conn.cursor()
        
        # 先检查哪些表确实存在
        logger.info("🔍 检查现有表...")
        cursor.execute("""
            SELECT table_name FROM information_schema.tables 
            WHERE table_schema = 'public' 
            ORDER BY table_name
        """)
        existing_tables = [row[0] for row in cursor.fetchall()]
        logger.info(f"📋 数据库中现有表 ({len(existing_tables)}个): {', '.join(existing_tables)}")
        
        # 找出需要删除的think_ship表
        tables_to_delete = []
        for table in think_ship_tables:
            if table in existing_tables:
                tables_to_delete.append(table)
        
        if not tables_to_delete:
            logger.info("✅ 没有发现think_ship相关的表，数据库是干净的")
            return True
        
        logger.warning(f"⚠️ 发现 {len(tables_to_delete)} 个think_ship相关表，即将自动删除:")
        for table in tables_to_delete:
            logger.warning(f"   - {table}")
        
        # 删除表（按依赖关系逆序）
        logger.info("🗑️ 开始删除think_ship相关表...")
        deleted_count = 0
        failed_count = 0
        
        for table in tables_to_delete:
            try:
                cursor.execute(f'DROP TABLE IF EXISTS "{table}" CASCADE')
                logger.info(f"   ✅ 删除表: {table}")
                deleted_count += 1
            except Exception as e:
                logger.error(f"   ❌ 删除表 {table} 失败: {e}")
                failed_count += 1
        
        # 再次检查结果
        cursor.execute("""
            SELECT table_name FROM information_schema.tables 
            WHERE table_schema = 'public' 
            ORDER BY table_name
        """)
        remaining_tables = [row[0] for row in cursor.fetchall()]
        
        # 检查是否还有think_ship表残留
        remaining_think_ship_tables = [t for t in remaining_tables if t in think_ship_tables]
        
        print("\n" + "="*80)
        print("📊 清理结果统计:")
        print("="*80)
        print(f"成功删除: {deleted_count} 个表")
        print(f"删除失败: {failed_count} 个表")
        print(f"剩余表数: {len(remaining_tables)} 个")
        
        if remaining_think_ship_tables:
            logger.warning(f"⚠️ 仍有 {len(remaining_think_ship_tables)} 个think_ship表未删除: {remaining_think_ship_tables}")
            return False
        else:
            logger.success("✅ 所有think_ship相关表已清理完成")
        
        logger.info(f"📋 清理后剩余表: {', '.join(remaining_tables)}")
        
        # 检查cappadocia原始表是否完整
        cappadocia_tables = [t for t in remaining_tables if t.startswith('meta_') or t.startswith('log_') or t.startswith('rel_') or t.startswith('statistics_')]
        logger.info(f"🏛️ Cappadocia原始表 ({len(cappadocia_tables)}个): {', '.join(cappadocia_tables)}")
        
        cursor.close()
        conn.close()
        
        logger.success("🎉 cappadocia_v1数据库清理完成！")
        return True
        
    except Exception as e:
        logger.error(f"❌ 清理失败: {e}")
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
    
    logger.warning("⚠️  这是自动清理脚本，将立即删除think_ship污染表！")
    logger.info("正在执行清理操作...")
    
    success = auto_cleanup_cappa_database()
    
    if success:
        logger.success("🎊 数据库清理成功！")
        logger.info("cappadocia_v1数据库已恢复干净状态")
        logger.info("think_ship项目现在完全独立，使用自己的数据库")
    else:
        logger.error("💥 数据库清理失败")
        sys.exit(1)


if __name__ == "__main__":
    main()