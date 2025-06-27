#!/usr/bin/env python3
"""
文件名: detailed_table_analysis.py
描述: 详细分析cappadocia_v1数据库中表的结构

本脚本负责：
1. 详细检查每个表的字段结构
2. 分析主键类型和约束
3. 确定表的创建来源

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


def analyze_table_structure():
    """详细分析表结构"""
    
    logger.info("🔍 详细分析cappadocia_v1数据库中表的结构...")
    
    # 使用postgres超级用户
    admin_user = "postgres"
    admin_password = "psl#@!logIN4SS2000"
    host = "101.35.56.140"
    port = 5432
    database_name = "cappadocia_v1"
    
    # 疑似think_ship的表名
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
        
        # 首先列出所有表
        cursor.execute("""
            SELECT table_name FROM information_schema.tables 
            WHERE table_schema = 'public' 
            ORDER BY table_name
        """)
        all_tables = [row[0] for row in cursor.fetchall()]
        logger.info(f"📋 数据库中所有表 ({len(all_tables)}个): {', '.join(all_tables)}")
        
        print("\n" + "="*80)
        print("📊 详细表结构分析:")
        print("="*80)
        
        for table in suspect_tables:
            if table not in all_tables:
                continue
                
            print(f"\n🔍 表: {table}")
            print("-" * 60)
            
            # 获取表的详细结构
            cursor.execute("""
                SELECT 
                    column_name, 
                    data_type, 
                    column_default, 
                    is_nullable,
                    character_maximum_length
                FROM information_schema.columns 
                WHERE table_schema = 'public' AND table_name = %s
                ORDER BY ordinal_position
            """, (table,))
            
            columns = cursor.fetchall()
            
            print("字段信息:")
            for col in columns:
                col_name, data_type, default, nullable, max_len = col
                default_str = str(default) if default else "无"
                max_len_str = f"({max_len})" if max_len else ""
                print(f"  - {col_name}: {data_type}{max_len_str}, 默认值: {default_str}, 可空: {nullable}")
            
            # 检查主键
            cursor.execute("""
                SELECT a.attname
                FROM pg_index i
                JOIN pg_attribute a ON a.attrelid = i.indrelid AND a.attnum = ANY(i.indkey)
                WHERE i.indrelid = %s::regclass AND i.indisprimary
            """, (table,))
            
            primary_keys = [row[0] for row in cursor.fetchall()]
            print(f"主键: {', '.join(primary_keys) if primary_keys else '无'}")
            
            # 检查索引
            cursor.execute("""
                SELECT indexname, indexdef 
                FROM pg_indexes 
                WHERE tablename = %s AND schemaname = 'public'
            """, (table,))
            
            indexes = cursor.fetchall()
            if indexes:
                print("索引:")
                for idx_name, idx_def in indexes:
                    print(f"  - {idx_name}: {idx_def}")
            
            # 检查外键
            cursor.execute("""
                SELECT
                    tc.constraint_name,
                    kcu.column_name,
                    ccu.table_name AS foreign_table_name,
                    ccu.column_name AS foreign_column_name
                FROM
                    information_schema.table_constraints AS tc
                    JOIN information_schema.key_column_usage AS kcu
                      ON tc.constraint_name = kcu.constraint_name
                      AND tc.table_schema = kcu.table_schema
                    JOIN information_schema.constraint_column_usage AS ccu
                      ON ccu.constraint_name = tc.constraint_name
                      AND ccu.table_schema = tc.table_schema
                WHERE tc.constraint_type = 'FOREIGN KEY' AND tc.table_name = %s
            """, (table,))
            
            foreign_keys = cursor.fetchall()
            if foreign_keys:
                print("外键:")
                for fk in foreign_keys:
                    print(f"  - {fk[1]} -> {fk[2]}.{fk[3]}")
            
            # 检查数据行数
            cursor.execute(f'SELECT COUNT(*) FROM "{table}"')
            row_count = cursor.fetchone()[0]
            print(f"数据行数: {row_count}")
            
            # 特征分析
            column_names = [col[0] for col in columns]
            has_uuid_default = any('uuid_generate_v4()' in str(col[2]) for col in columns if col[0] == 'id')
            has_think_ship_pattern = (
                'created_at' in column_names and 
                'updated_at' in column_names and 
                'created_by' in column_names and 
                'updated_by' in column_names and 
                'remark' in column_names
            )
            
            print(f"UUID主键: {'是' if has_uuid_default else '否'}")
            print(f"Think Ship字段模式: {'是' if has_think_ship_pattern else '否'}")
            
            if has_uuid_default and has_think_ship_pattern:
                print("🎯 判断: Think Ship 表")
            else:
                print("❓ 判断: 原有表或未确定")
        
        cursor.close()
        conn.close()
        
        print("\n" + "="*80)
        print("📝 分析完成")
        print("="*80)
        
    except Exception as e:
        logger.error(f"❌ 分析失败: {e}")


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
    
    analyze_table_structure()


if __name__ == "__main__":
    main()