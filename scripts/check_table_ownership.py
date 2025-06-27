#!/usr/bin/env python3
"""
文件名: check_table_ownership.py
描述: 检查cappadocia_v1数据库中表的归属

本脚本负责：
1. 检查表的创建时间
2. 分析表结构特征
3. 确定哪些表是think_ship创建的

作者: Think Ship Team
创建日期: 2024-12-27
版本: 1.0.0
"""

import sys
from pathlib import Path

import psycopg2
from loguru import logger

# 添加项目根目录到Python路径
sys.path.append(str(Path(__file__).parent.parent))


def check_table_ownership():
    """检查表的归属"""
    
    logger.info("🔍 检查cappadocia_v1数据库中表的归属...")
    
    # 使用postgres超级用户
    admin_user = "postgres"
    admin_password = "psl#@!logIN4SS2000"
    host = "101.35.56.140"
    port = 5432
    database_name = "cappadocia_v1"
    
    # think_ship相关的表名
    suspect_tables = [
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
    
    try:
        # 连接到cappadocia_v1数据库
        conn = psycopg2.connect(
            host=host,
            port=port,
            user=admin_user,
            password=admin_password,
            database=database_name
        )
        cursor = conn.cursor()
        
        logger.info("📋 分析可疑表的结构特征...")
        
        think_ship_tables = []
        cappadocia_tables = []
        
        for table in suspect_tables:
            # 检查表是否存在
            cursor.execute("""
                SELECT COUNT(*) FROM information_schema.tables 
                WHERE table_schema = 'public' AND table_name = %s
            """, (table,))
            
            if cursor.fetchone()[0] == 0:
                continue
                
            # 检查表结构，特别是think_ship特有的字段
            cursor.execute("""
                SELECT column_name, data_type, column_default, is_nullable
                FROM information_schema.columns 
                WHERE table_schema = 'public' AND table_name = %s
                ORDER BY ordinal_position
            """, (table,))
            
            columns = cursor.fetchall()
            column_names = [col[0] for col in columns]
            
            # think_ship特征：UUID主键 + created_at/updated_at + created_by/updated_by + remark
            has_uuid_id = any('uuid_generate_v4()' in str(col[2]) for col in columns if col[0] == 'id')
            has_think_ship_pattern = (
                'created_at' in column_names and 
                'updated_at' in column_names and 
                'created_by' in column_names and 
                'updated_by' in column_names and 
                'remark' in column_names
            )
            
            # 检查是否有数据
            cursor.execute(f'SELECT COUNT(*) FROM "{table}"')
            row_count = cursor.fetchone()[0]
            
            if has_uuid_id and has_think_ship_pattern:
                think_ship_tables.append((table, row_count, '具有think_ship特征字段'))
                logger.warning(f"   🎯 {table}: think_ship表 (数据行数: {row_count})")
            else:
                cappadocia_tables.append((table, row_count, '可能是cappadocia原有表'))
                logger.info(f"   ✅ {table}: 可能是cappadocia原有表 (数据行数: {row_count})")
        
        print("\n" + "="*60)
        print("📊 分析结果:")
        print("="*60)
        
        if think_ship_tables:
            print(f"\n🎯 确认为think_ship污染表 ({len(think_ship_tables)}个):")
            for table, count, reason in think_ship_tables:
                print(f"   - {table} (数据: {count}行) - {reason}")
        
        if cappadocia_tables:
            print(f"\n✅ 可能为cappadocia原有表 ({len(cappadocia_tables)}个):")
            for table, count, reason in cappadocia_tables:
                print(f"   - {table} (数据: {count}行) - {reason}")
        
        print("\n" + "="*60)
        
        # 如果有think_ship表，询问是否删除
        if think_ship_tables:
            print(f"\n⚠️  建议删除 {len(think_ship_tables)} 个think_ship污染表")
            print("这些表具有明显的think_ship特征，不是cappadocia项目的原始表")
            
            # 生成删除命令
            print("\n🔧 删除命令:")
            for table, _, _ in think_ship_tables:
                print(f"DROP TABLE IF EXISTS \"{table}\" CASCADE;")
        else:
            print("\n✅ 没有发现明确的think_ship污染表")
        
        cursor.close()
        conn.close()
        
        return think_ship_tables
        
    except Exception as e:
        logger.error(f"❌ 检查失败: {e}")
        return []


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
    
    think_ship_tables = check_table_ownership()
    
    if think_ship_tables:
        print(f"\n💡 建议：运行清理脚本删除这 {len(think_ship_tables)} 个污染表")
    else:
        print("\n✅ 数据库状态良好，无需清理")


if __name__ == "__main__":
    main()