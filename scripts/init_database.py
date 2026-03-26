"""数据库初始化脚本

功能:
1. 连接 PostgreSQL (管理员账号)
2. 创建数据库
3. 创建用户
4. 授予权限
5. 初始化表结构
"""
import sys
import psycopg2
from psycopg2 import sql
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


# 数据库配置
import urllib.parse
admin_password = urllib.parse.quote_plus("1437@2026")
ADMIN_DB_URL = f"postgresql://postgres:{admin_password}@localhost:5432/postgres"
DB_NAME = "wellinfo"
DB_USER = "wellinfo"
DB_PASSWORD = "wellinfo2026"
DB_HOST = "localhost"
DB_PORT = "5432"


def create_database():
    """创建数据库和用户"""

    logger.info("=" * 60)
    logger.info("开始初始化数据库")
    logger.info("=" * 60)

    # 连接到 PostgreSQL (管理员账号)
    logger.info(f"连接到 PostgreSQL (管理员)...")
    try:
        conn = psycopg2.connect(ADMIN_DB_URL)
        conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        cursor = conn.cursor()
        logger.info("✅ 连接成功")
    except Exception as e:
        logger.error(f"❌ 连接失败: {e}")
        logger.error("请检查:")
        logger.error("  1. PostgreSQL 服务是否启动")
        logger.error("  2. 管理员密码是否正确")
        logger.error("  3. postgres/1437@2026@localhost:5432/postgres 是否可访问")
        sys.exit(1)

    try:
        # ========== 第1步: 创建数据库 ==========
        logger.info(f"\n[第1步] 创建数据库: {DB_NAME}")

        # 检查数据库是否已存在
        cursor.execute(
            sql.SQL("SELECT 1 FROM pg_database WHERE datname = %s"),
            [DB_NAME]
        )
        exists = cursor.fetchone()

        if exists:
            logger.info(f"⚠️  数据库 '{DB_NAME}' 已存在")
            confirm = input(f"是否删除并重新创建? (yes/no): ")
            if confirm.lower() == 'yes':
                cursor.execute(
                    sql.SQL("DROP DATABASE {}").format(sql.Identifier(DB_NAME))
                )
                logger.info(f"✅ 已删除旧数据库")
            else:
                logger.info(f"保留现有数据库")
        else:
            logger.info(f"✅ 数据库不存在,将创建新数据库")

        # 创建数据库
        cursor.execute(
            sql.SQL("CREATE DATABASE {}").format(sql.Identifier(DB_NAME))
        )
        logger.info(f"✅ 数据库 '{DB_NAME}' 创建成功")

        # ========== 第2步: 创建用户 ==========
        logger.info(f"\n[第2步] 创建用户: {DB_USER}")

        # 检查用户是否已存在
        cursor.execute(
            sql.SQL("SELECT 1 FROM pg_user WHERE usename = %s"),
            [DB_USER]
        )
        user_exists = cursor.fetchone()

        if user_exists:
            logger.info(f"⚠️  用户 '{DB_USER}' 已存在")
            confirm = input(f"是否修改密码? (yes/no): ")
            if confirm.lower() == 'yes':
                cursor.execute(
                    sql.SQL("ALTER USER {} WITH PASSWORD %s").format(
                        sql.Identifier(DB_USER)
                    ),
                    [DB_PASSWORD]
                )
                logger.info(f"✅ 用户密码已修改")
            else:
                logger.info(f"保留现有用户")
        else:
            # 创建用户
            cursor.execute(
                sql.SQL("CREATE USER {} WITH PASSWORD %s").format(
                    sql.Identifier(DB_USER)
                ),
                [DB_PASSWORD]
            )
            logger.info(f"✅ 用户 '{DB_USER}' 创建成功")

        # ========== 第3步: 授予权限 ==========
        logger.info(f"\n[第3步] 授予权限")

        # 授予数据库连接权限（在 postgres 数据库中）
        cursor.execute(
            sql.SQL("GRANT CONNECT ON DATABASE {} TO {}").format(
                sql.Identifier(DB_NAME),
                sql.Identifier(DB_USER)
            )
        )
        logger.info(f"✅ 授予连接权限")

        # 关闭管理员连接
        cursor.close()
        conn.close()

        # 连接到 wellinfo 数据库，使用管理员账号授予权限
        logger.info(f"连接到 {DB_NAME} 数据库授予模式权限...")
        conn = psycopg2.connect(f"postgresql://postgres:{admin_password}@{DB_HOST}:{DB_PORT}/{DB_NAME}")
        conn.autocommit = True
        cursor = conn.cursor()

        # 授予模式权限（在 wellinfo 数据库中）
        cursor.execute(
            sql.SQL("GRANT ALL ON SCHEMA public TO {}").format(
                sql.Identifier(DB_USER)
            )
        )
        logger.info(f"✅ 授予模式权限")

        # 授予未来表的权限
        cursor.execute(
            sql.SQL("ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON TABLES TO {}").format(
                sql.Identifier(DB_USER)
            )
        )
        logger.info(f"✅ 授予未来表权限")

        cursor.execute(
            sql.SQL("ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON SEQUENCES TO {}").format(
                sql.Identifier(DB_USER)
            )
        )
        logger.info(f"✅ 授予未来序列权限")

        # 关闭管理员连接
        cursor.close()
        conn.close()

        # ========== 第4步: 创建表结构 ==========
        logger.info(f"\n[第4步] 创建表结构")

        # 连接到新数据库（使用 wellinfo 用户）
        db_url = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
        logger.info(f"连接到数据库: {DB_NAME}")

        conn = psycopg2.connect(db_url)
        cursor = conn.cursor()
        logger.info("✅ 连接成功")

        # ✅ 关键：先创建表结构，再插入初始数据
        create_tables(cursor)
        
        # ✅ 关键：插入初始数据（此时表已经创建）
        insert_initial_data(cursor)

        # 提交事务
        conn.commit()
        logger.info("✅ 表结构和初始数据创建完成")

        # 关闭连接
        cursor.close()
        conn.close()

        # ========== 完成 ==========
        logger.info("\n" + "=" * 60)
        logger.info("✅ 数据库初始化完成!")
        logger.info("=" * 60)
        logger.info(f"\n数据库连接信息:")
        logger.info(f"  数据库: {DB_NAME}")
        logger.info(f"  用户: {DB_USER}")
        logger.info(f"  密码: {DB_PASSWORD}")
        logger.info(f"  主机: {DB_HOST}")
        logger.info(f"  端口: {DB_PORT}")
        logger.info(f"\n连接 URL:")
        logger.info(f"  {db_url}")
        logger.info("\n可以使用以下方式连接:")
        logger.info(f"  psql -U {DB_USER} -d {DB_NAME} -h {DB_HOST}")
        logger.info(f"  password: {DB_PASSWORD}")

    except Exception as e:
        logger.error(f"\n❌ 初始化失败: {e}", exc_info=True)
        sys.exit(1)


def create_tables(cursor):
    """创建表结构

    与 db/models.py 定义的9张表保持完全一致:
    1. wells - 井信息表
    2. documents - 文档表
    3. extracted_data - 提取数据表
    4. quality_reports - 质量评估表
    5. validation_results - 校验结果表
    6. users - 用户表 ✅ 移到 review_records 之前，确保外键约束有效
    7. review_records - 审核记录表 ✅ 可以引用 users 了
    8. processing_logs - 处理日志表
    9. statistics - 统计数据表
    """

    logger.info("创建表结构...")

    # ========== 1. 井信息表 ==========
    logger.info("  创建表: wells (井信息)")
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS wells (
            id SERIAL PRIMARY KEY,
            well_no VARCHAR(50) UNIQUE NOT NULL,
            well_name VARCHAR(200),
            oilfield VARCHAR(100),
            block VARCHAR(100),
            well_type VARCHAR(50),
            well_pattern VARCHAR(50),
            well_class VARCHAR(50),
            latitude NUMERIC(10, 6),
            longitude NUMERIC(10, 6),
            elevation NUMERIC(10, 2),
            ground_elevation NUMERIC(10, 2),
            drill_date DATE,
            completion_date DATE,
            status VARCHAR(20) DEFAULT 'active',
            created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # 创建索引
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_wells_well_no ON wells(well_no)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_wells_oilfield ON wells(oilfield)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_wells_block ON wells(block)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_wells_status ON wells(status)")

    # ========== 2. 文档表 ==========
    logger.info("  创建表: documents (文档)")
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS documents (
            id SERIAL PRIMARY KEY,
            well_no VARCHAR(50) NOT NULL,
            document_id VARCHAR(100) UNIQUE,
            filename VARCHAR(255) NOT NULL,
            file_path VARCHAR(500),
            file_size BIGINT,
            file_extension VARCHAR(10),
            mime_type VARCHAR(100),
            document_type VARCHAR(50),
            category VARCHAR(50),
            doc_category VARCHAR(100),
            upload_date DATE,
            uploaded_by VARCHAR(100),
            status VARCHAR(20) DEFAULT 'pending',
            created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (well_no) REFERENCES wells(well_no) ON DELETE CASCADE
        )
    """)

    # 创建索引
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_documents_well_no ON documents(well_no)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_documents_document_type ON documents(document_type)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_documents_category ON documents(category)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_documents_doc_category ON documents(doc_category)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_documents_status ON documents(status)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_documents_upload_date ON documents(upload_date)")

    # ========== 3. 提取数据表 ==========
    logger.info("  创建表: extracted_data (提取数据)")
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS extracted_data (
            id SERIAL PRIMARY KEY,
            document_id INTEGER NOT NULL,
            well_no VARCHAR(50) NOT NULL,
            field_name VARCHAR(100) NOT NULL,
            field_value TEXT,
            field_type VARCHAR(20),
            confidence NUMERIC(5, 2),
            is_valid BOOLEAN DEFAULT TRUE,
            validation_errors JSONB,
            source VARCHAR(20),
            created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (document_id) REFERENCES documents(id) ON DELETE CASCADE,
            FOREIGN KEY (well_no) REFERENCES wells(well_no) ON DELETE CASCADE,
            UNIQUE(document_id, field_name)
        )
    """)

    # 创建索引
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_extracted_data_document_id ON extracted_data(document_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_extracted_data_well_no ON extracted_data(well_no)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_extracted_data_field_name ON extracted_data(field_name)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_extracted_data_confidence ON extracted_data(confidence)")

    # ========== 4. 质量评估表 ==========
    logger.info("  创建表: quality_reports (质量评估)")
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS quality_reports (
            id SERIAL PRIMARY KEY,
            document_id INTEGER NOT NULL,
            well_no VARCHAR(50) NOT NULL,
            completeness NUMERIC(5, 2),
            accuracy NUMERIC(5, 2),
            consistency NUMERIC(5, 2),
            confidence NUMERIC(5, 2),
            overall_score NUMERIC(5, 2),
            quality_level VARCHAR(20),
            issues JSONB,
            suggestions JSONB,
            validated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (document_id) REFERENCES documents(id) ON DELETE CASCADE,
            FOREIGN KEY (well_no) REFERENCES wells(well_no) ON DELETE CASCADE,
            UNIQUE(document_id)
        )
    """)

    # 创建索引
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_quality_reports_document_id ON quality_reports(document_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_quality_reports_well_no ON quality_reports(well_no)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_quality_reports_overall_score ON quality_reports(overall_score)")

    # ========== 5. 校验结果表 ==========
    logger.info("  创建表: validation_results (校验结果)")
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS validation_results (
            id SERIAL PRIMARY KEY,
            document_id INTEGER NOT NULL,
            field_name VARCHAR(100) NOT NULL,
            passed BOOLEAN NOT NULL,
            error_type VARCHAR(20),
            error_message TEXT,
            suggestion TEXT,
            created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (document_id) REFERENCES documents(id) ON DELETE CASCADE
        )
    """)

    # 创建索引
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_validation_results_document_id ON validation_results(document_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_validation_results_passed ON validation_results(passed)")

    # ========== 6. 用户表 ==========  # ✅ 修复：将 users 表移到 review_records 之前
    logger.info("  创建表: users (用户)")
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id SERIAL PRIMARY KEY,
            username VARCHAR(50) UNIQUE NOT NULL,
            email VARCHAR(100) UNIQUE NOT NULL,
            hashed_password VARCHAR(255) NOT NULL,
            full_name VARCHAR(100),
            role VARCHAR(20) NOT NULL DEFAULT 'user',
            is_active BOOLEAN NOT NULL DEFAULT TRUE,
            created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
            last_login_at TIMESTAMP
        )
    """)

    # 创建索引
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_users_username ON users(username)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_users_email ON users(email)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_users_role ON users(role)")

    # ========== 7. 审核记录表 ==========  # ✅ 修复：现在 review_records 可以引用 users 了
    logger.info("  创建表: review_records (审核记录)")
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS review_records (
            id SERIAL PRIMARY KEY,
            document_id INTEGER NOT NULL,
            reviewer_id INTEGER NOT NULL,
            original_value TEXT,
            corrected_value TEXT,
            correction_type VARCHAR(20),
            comment TEXT,
            created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (document_id) REFERENCES documents(id) ON DELETE CASCADE,
            FOREIGN KEY (reviewer_id) REFERENCES users(id) ON DELETE CASCADE
        )
    """)

    # 创建索引
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_review_records_document_id ON review_records(document_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_review_records_reviewer_id ON review_records(reviewer_id)")

    # ========== 8. 处理日志表 ==========
    logger.info("  创建表: processing_logs (处理日志)")
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS processing_logs (
            id SERIAL PRIMARY KEY,
            document_id INTEGER,
            well_no VARCHAR(50),
            stage VARCHAR(50),
            status VARCHAR(20),
            duration_ms INTEGER,
            message TEXT,
            error_message TEXT,
            log_metadata JSONB,
            created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (document_id) REFERENCES documents(id) ON DELETE SET NULL
        )
    """)

    # 创建索引
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_processing_logs_document_id ON processing_logs(document_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_processing_logs_well_no ON processing_logs(well_no)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_processing_logs_stage ON processing_logs(stage)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_processing_logs_created_at ON processing_logs(created_at)")

    # ========== 9. 统计数据表 ==========
    logger.info("  创建表: statistics (统计数据)")
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS statistics (
            id SERIAL PRIMARY KEY,
            stat_date VARCHAR(10) UNIQUE NOT NULL,
            total_documents INTEGER NOT NULL DEFAULT 0,
            success_documents INTEGER NOT NULL DEFAULT 0,
            failed_documents INTEGER NOT NULL DEFAULT 0,
            avg_confidence NUMERIC(5, 3),
            avg_processing_time_ms INTEGER,
            total_fields_extracted INTEGER DEFAULT 0,
            manual_review_rate NUMERIC(5, 3),
            created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # 创建索引
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_statistics_stat_date ON statistics(stat_date)")

    logger.info("✅ 所有表创建完成")


def insert_initial_data(cursor):
    """插入初始数据

    注意：此函数必须在 create_tables(cursor) 之后调用！
    """

    logger.info("插入初始数据...")

    # 创建触发器: 自动更新 updated_at
    cursor.execute("""
        CREATE OR REPLACE FUNCTION update_updated_at_column()
        RETURNS TRIGGER AS $$
        BEGIN
            NEW.updated_at = CURRENT_TIMESTAMP;
            RETURN NEW;
        END;
        $$ language 'plpgsql';
    """)

    # 为需要更新时间戳的表添加触发器
    tables = ['wells', 'documents', 'extracted_data', 'users']
    for table in tables:
        cursor.execute(f"""
            DROP TRIGGER IF EXISTS update_{table}_updated_at ON {table};
            CREATE TRIGGER update_{table}_updated_at
            BEFORE UPDATE ON {table}
            FOR EACH ROW
            EXECUTE FUNCTION update_updated_at_column();
        """)
        logger.info(f"  ✅ 创建触发器: {table}")

    # 插入管理员用户（使用 hashlib 替代 bcrypt 避免依赖问题）
    import hashlib

    admin_password = "admin123"  # 默认密码,生产环境请修改
    # 使用 SHA-256 + salt 的简单哈希（生产环境建议使用 bcrypt）
    salt = "wellinfo_salt_2026"
    hashed_password = hashlib.sha256((admin_password + salt).encode()).hexdigest()

    # ✅ 关键：确保此时 users 表已经创建
    cursor.execute("""
        INSERT INTO users (username, email, hashed_password, full_name, role)
        VALUES (%s, %s, %s, %s, %s)
        ON CONFLICT (username) DO NOTHING
    """, ('admin', 'admin@wellinfo.com', hashed_password, '系统管理员', 'admin'))

    logger.info(f"  ✅ 创建管理员用户: admin / {admin_password}")

    logger.info("✅ 初始数据插入完成")


def test_connection():
    """测试数据库连接"""

    logger.info("\n测试数据库连接...")

    db_url = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

    try:
        conn = psycopg2.connect(db_url)
        cursor = conn.cursor()

        # 测试查询
        cursor.execute("SELECT version();")
        version = cursor.fetchone()[0]
        logger.info(f"✅ PostgreSQL 版本: {version.split(',')[0]}")

        # 查看表
        cursor.execute("""
            SELECT table_name
            FROM information_schema.tables
            WHERE table_schema = 'public'
            ORDER BY table_name;
        """)
        tables = cursor.fetchall()
        logger.info(f"✅ 已创建 {len(tables)} 个表:")
        for table in tables:
            logger.info(f"    - {table[0]}")

        # 查看数据
        cursor.execute("SELECT COUNT(*) FROM users;")
        user_count = cursor.fetchone()[0]
        logger.info(f"✅ 用户表中有 {user_count} 个用户")

        cursor.close()
        conn.close()

        logger.info("✅ 数据库连接测试成功")

    except Exception as e:
        logger.error(f"❌ 连接测试失败: {e}")
        sys.exit(1)


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="数据库初始化脚本")
    parser.add_argument("--test-only", action="store_true", help="仅测试连接,不创建数据库")
    args = parser.parse_args()

    if args.test_only:
        test_connection()
    else:
        create_database()
        test_connection()
