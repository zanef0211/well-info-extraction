# 数据库初始化说明

## 数据库信息

- **数据库名**: `wellinfo`
- **用户名**: `wellinfo`
- **密码**: `wellinfo2026`
- **管理员账号**: `postgres` / `1437@2026`
- **连接URL**: `postgresql://wellinfo:wellinfo2026@localhost:5432/wellinfo`

## 使用方法

### 方法1: 使用简化脚本(推荐)

```bash
# 进入 scripts 目录
cd scripts

# 初始化数据库
python init_database_simple.py

# 仅测试连接
python init_database_simple.py --test-only
```

### 方法2: 使用完整脚本

```bash
# 进入 scripts 目录
cd scripts

# 初始化数据库(包含创建管理员用户)
python init_database.py

# 仅测试连接
python init_database.py --test-only
```

## 脚本功能

### init_database_simple.py (推荐)

这个脚本不依赖额外的密码库,仅创建:

1. ✅ 创建数据库 `wellinfo`
2. ✅ 创建用户 `wellinfo` / `wellinfo2026`
3. ✅ 授予权限
4. ✅ 创建表结构 (9个表)
5. ✅ 创建触发器 (自动更新 updated_at)

### init_database.py

这个脚本包含完整功能:

1. ✅ 创建数据库和用户
2. ✅ 创建表结构 (9个表)
3. ✅ 创建触发器 (自动更新 updated_at)
4. ✅ 插入初始数据 (管理员用户)

管理员账户:
- 用户名: `admin`
- 密码: `admin123` (生产环境请修改)

## 数据库表结构

### 1. wells (井信息表)
存储油气井的基本信息

| 字段 | 类型 | 说明 |
|------|------|------|
| id | SERIAL | 主键 |
| well_no | VARCHAR(50) | 井号(唯一) |
| well_name | VARCHAR(200) | 井名 |
| oilfield | VARCHAR(100) | 油田 |
| block | VARCHAR(100) | 区块 |
| well_type | VARCHAR(50) | 井别 |
| well_pattern | VARCHAR(50) | 井型 |
| well_class | VARCHAR(50) | 井级 |
| latitude | NUMERIC(10,6) | 纬度 |
| longitude | NUMERIC(10,6) | 经度 |
| elevation | NUMERIC(10,2) | 海拔 |
| ground_elevation | NUMERIC(10,2) | 地面海拔 |
| drill_date | DATE | 开钻日期 |
| completion_date | DATE | 完钻日期 |
| status | VARCHAR(20) | 状态 (默认: 'active') |
| created_at | TIMESTAMP | 创建时间 |
| updated_at | TIMESTAMP | 更新时间 |

**索引**:
- `idx_wells_well_no` - 井号
- `idx_wells_oilfield` - 油田
- `idx_wells_block` - 区块
- `idx_wells_status` - 状态

---

### 2. documents (文档表)
存储上传的文档信息

| 字段 | 类型 | 说明 |
|------|------|------|
| id | SERIAL | 主键 |
| well_no | VARCHAR(50) | 井号(外键) |
| document_id | VARCHAR(100) | 文档ID(唯一) |
| filename | VARCHAR(255) | 文件名 |
| file_path | VARCHAR(500) | 文件路径 |
| file_size | BIGINT | 文件大小 |
| file_extension | VARCHAR(10) | 文件扩展名 |
| mime_type | VARCHAR(100) | MIME类型 |
| document_type | VARCHAR(50) | 文档类型 |
| category | VARCHAR(50) | 分类 |
| doc_category | VARCHAR(100) | 文档分类 |
| upload_date | DATE | 上传日期 |
| uploaded_by | VARCHAR(100) | 上传者 |
| status | VARCHAR(20) | 状态 (默认: 'pending') |
| created_at | TIMESTAMP | 创建时间 |
| updated_at | TIMESTAMP | 更新时间 |

**外键**:
- `well_no` → `wells(well_no)` ON DELETE CASCADE

**索引**:
- `idx_documents_well_no` - 井号
- `idx_documents_document_type` - 文档类型
- `idx_documents_category` - 分类
- `idx_documents_doc_category` - 文档分类
- `idx_documents_status` - 状态
- `idx_documents_upload_date` - 上传日期

---

### 3. extracted_data (提取数据表)
存储从文档中提取的结构化数据

| 字段 | 类型 | 说明 |
|------|------|------|
| id | SERIAL | 主键 |
| document_id | INTEGER | 文档ID(外键，引用 documents.id) |
| well_no | VARCHAR(50) | 井号(外键) |
| field_name | VARCHAR(100) | 字段名 |
| field_value | TEXT | 字段值 |
| field_type | VARCHAR(20) | 字段类型 |
| confidence | NUMERIC(5,2) | 置信度 |
| is_valid | BOOLEAN | 是否有效 (默认: TRUE) |
| validation_errors | JSONB | 验证错误 |
| source | VARCHAR(20) | 来源 |
| created_at | TIMESTAMP | 创建时间 |
| updated_at | TIMESTAMP | 更新时间 |

**外键**:
- `document_id` → `documents(id)` ON DELETE CASCADE
- `well_no` → `wells(well_no)` ON DELETE CASCADE

**唯一约束**: `(document_id, field_name)`

**索引**:
- `idx_extracted_data_document_id` - 文档ID
- `idx_extracted_data_well_no` - 井号
- `idx_extracted_data_field_name` - 字段名
- `idx_extracted_data_confidence` - 置信度

---

### 4. quality_reports (质量评估表)
存储数据质量评估结果

| 字段 | 类型 | 说明 |
|------|------|------|
| id | SERIAL | 主键 |
| document_id | INTEGER | 文档ID(外键，引用 documents.id) |
| well_no | VARCHAR(50) | 井号(外键) |
| completeness | NUMERIC(5,2) | 完整性 |
| accuracy | NUMERIC(5,2) | 准确性 |
| consistency | NUMERIC(5,2) | 一致性 |
| confidence | NUMERIC(5,2) | 置信度 |
| overall_score | NUMERIC(5,2) | 总体评分 |
| quality_level | VARCHAR(20) | 质量等级 |
| issues | JSONB | 问题列表 |
| suggestions | JSONB | 改进建议 |
| validated_at | TIMESTAMP | 验证时间 |

**外键**:
- `document_id` → `documents(id)` ON DELETE CASCADE
- `well_no` → `wells(well_no)` ON DELETE CASCADE

**唯一约束**: `document_id`

**索引**:
- `idx_quality_reports_document_id` - 文档ID
- `idx_quality_reports_well_no` - 井号
- `idx_quality_reports_overall_score` - 总体评分

---

### 5. validation_results (校验结果表)
存储字段校验结果

| 字段 | 类型 | 说明 |
|------|------|------|
| id | SERIAL | 主键 |
| document_id | INTEGER | 文档ID(外键，引用 documents.id) |
| field_name | VARCHAR(100) | 字段名 |
| passed | BOOLEAN | 是否通过校验 |
| error_type | VARCHAR(20) | 错误类型 |
| error_message | TEXT | 错误信息 |
| suggestion | TEXT | 修正建议 |
| created_at | TIMESTAMP | 创建时间 |

**外键**:
- `document_id` → `documents(id)` ON DELETE CASCADE

**索引**:
- `idx_validation_results_document_id` - 文档ID
- `idx_validation_results_passed` - 是否通过

---

### 6. users (用户表)
存储系统用户

| 字段 | 类型 | 说明 |
|------|------|------|
| id | SERIAL | 主键 |
| username | VARCHAR(50) | 用户名(唯一) |
| email | VARCHAR(100) | 邮箱(唯一) |
| hashed_password | VARCHAR(255) | 加密密码 |
| full_name | VARCHAR(100) | 全名 |
| role | VARCHAR(20) | 角色 (默认: 'user') |
| is_active | BOOLEAN | 是否激活 (默认: TRUE) |
| created_at | TIMESTAMP | 创建时间 |
| updated_at | TIMESTAMP | 更新时间 |
| last_login_at | TIMESTAMP | 最后登录时间 |

**索引**:
- `idx_users_username` - 用户名
- `idx_users_email` - 邮箱
- `idx_users_role` - 角色

---

### 7. review_records (审核记录表)
存储人工审核记录

| 字段 | 类型 | 说明 |
|------|------|------|
| id | SERIAL | 主键 |
| document_id | INTEGER | 文档ID(外键，引用 documents.id) |
| reviewer_id | INTEGER | 审核人ID(外键，引用 users.id) |
| original_value | TEXT | 原始值 |
| corrected_value | TEXT | 修正值 |
| correction_type | VARCHAR(20) | 修正类型 |
| comment | TEXT | 备注 |
| created_at | TIMESTAMP | 创建时间 |

**外键**:
- `document_id` → `documents(id)` ON DELETE CASCADE
- `reviewer_id` → `users(id)` ON DELETE CASCADE

**索引**:
- `idx_review_records_document_id` - 文档ID
- `idx_review_records_reviewer_id` - 审核人ID

---

### 8. processing_logs (处理日志表)
存储文档处理日志

| 字段 | 类型 | 说明 |
|------|------|------|
| id | SERIAL | 主键 |
| document_id | INTEGER | 文档ID(外键，引用 documents.id，可为空) |
| well_no | VARCHAR(50) | 井号 |
| stage | VARCHAR(50) | 处理阶段 |
| status | VARCHAR(20) | 状态 |
| duration_ms | INTEGER | 耗时(毫秒) |
| message | TEXT | 消息 |
| error_message | TEXT | 错误信息 |
| log_metadata | JSONB | 元数据 |
| created_at | TIMESTAMP | 创建时间 |

**外键**:
- `document_id` → `documents(id)` ON DELETE SET NULL

**索引**:
- `idx_processing_logs_document_id` - 文档ID
- `idx_processing_logs_well_no` - 井号
- `idx_processing_logs_stage` - 处理阶段
- `idx_processing_logs_created_at` - 创建时间

---

### 9. statistics (统计数据表)
存储系统统计数据

| 字段 | 类型 | 说明 |
|------|------|------|
| id | SERIAL | 主键 |
| stat_date | VARCHAR(10) | 统计日期 (唯一) |
| total_documents | INTEGER | 总文档数 (默认: 0) |
| success_documents | INTEGER | 成功文档数 (默认: 0) |
| failed_documents | INTEGER | 失败文档数 (默认: 0) |
| avg_confidence | NUMERIC(5,3) | 平均置信度 |
| avg_processing_time_ms | INTEGER | 平均处理时间(毫秒) |
| total_fields_extracted | INTEGER | 总提取字段数 (默认: 0) |
| manual_review_rate | NUMERIC(5,3) | 人工审核率 |
| created_at | TIMESTAMP | 创建时间 |

**唯一约束**: `stat_date`

**索引**:
- `idx_statistics_stat_date` - 统计日期

---

## 触发器

脚本会自动为以下表创建 `updated_at` 自动更新触发器:

1. **wells** - 井信息表
2. **documents** - 文档表
3. **extracted_data** - 提取数据表
4. **users** - 用户表

触发器函数 `update_updated_at_column()` 会在每次 UPDATE 操作时自动将 `updated_at` 字段设置为当前时间。

---

## 初始数据

脚本会自动插入以下初始数据:

### 管理员用户

| 字段 | 值 |
|------|---|
| username | `admin` |
| email | `admin@wellinfo.com` |
| password | `admin123` (SHA-256 + salt 哈希) |
| full_name | 系统管理员 |
| role | `admin` |

**⚠️ 注意**: 生产环境请务必修改管理员密码！

---

## 表创建顺序

为确保外键约束正确，表按以下顺序创建:

```
1. wells (井信息表)
2. documents (文档表) - 引用 wells
3. extracted_data (提取数据表) - 引用 documents, wells
4. quality_reports (质量评估表) - 引用 documents, wells
5. validation_results (校验结果表) - 引用 documents
6. users (用户表) - 无外键依赖
7. review_records (审核记录表) - 引用 documents, users
8. processing_logs (处理日志表) - 引用 documents
9. statistics (统计数据表) - 无外键依赖
```

---

## 手动连接数据库

### 使用 psql 命令行

```bash
# 使用 wellinfo 用户连接
psql -U wellinfo -d wellinfo -h localhost
# 输入密码: wellinfo2026

# 使用 postgres 管理员连接
psql -U postgres -d postgres -h localhost
# 输入密码: 1437@2026
```

### 使用 Python

```python
import psycopg2

# 连接数据库
conn = psycopg2.connect(
    host="localhost",
    port="5432",
    database="wellinfo",
    user="wellinfo",
    password="wellinfo2026"
)

# 使用连接
cursor = conn.cursor()
cursor.execute("SELECT * FROM wells;")
results = cursor.fetchall()
```

### 使用 SQLAlchemy

```python
from sqlalchemy import create_engine

# 连接字符串
DATABASE_URL = "postgresql://wellinfo:wellinfo2026@localhost:5432/wellinfo"

# 创建引擎
engine = create_engine(DATABASE_URL)

# 连接数据库
with engine.connect() as conn:
    result = conn.execute("SELECT version();")
    print(result.fetchone())
```

---

## 常见问题

### 1. 连接失败: password authentication failed

**原因**: 密码错误

**解决**:
- 检查 `.env` 文件中的密码是否正确
- 检查 PostgreSQL 管理员密码: `postgres/1437@2026`

### 2. 连接失败: database "wellinfo" does not exist

**原因**: 数据库未创建

**解决**:
```bash
python scripts/init_database_simple.py
```

### 3. 连接失败: role "wellinfo" does not exist

**原因**: 用户未创建

**解决**:
```bash
python scripts/init_database_simple.py
```

### 4. 权限不足

**原因**: 用户权限未设置

**解决**: 重新运行初始化脚本,会自动授予权限

### 5. 外键约束错误: relation "users" does not exist

**原因**: 表创建顺序错误，`review_records` 表在 `users` 表之前创建

**解决**: 
- 确保使用最新的 `scripts/init_database.py`
- 脚本已修复表创建顺序，`users` 表会在 `review_records` 之前创建

---

## 重置数据库

如果需要完全重置数据库:

```bash
# 方式1: 使用脚本重新创建
python scripts/init_database.py

# 方式2: 手动删除后重新创建
psql -U postgres -d postgres -h localhost
\c postgres
DROP DATABASE wellinfo;
DROP USER wellinfo;
\q

# 然后重新运行初始化脚本
python scripts/init_database.py
```

---

## 备份和恢复

### 备份数据库

```bash
pg_dump -U wellinfo -h localhost wellinfo > wellinfo_backup.sql
```

### 恢复数据库

```bash
psql -U wellinfo -h localhost wellinfo < wellinfo_backup.sql
```

---

## 数据库架构图

```
wells (1) ──────── (N) documents (1) ──────── (N) extracted_data
     │                    │                         │
     │                    │                    (1) quality_reports
     │                    │                         │
     │                    │                    (N) validation_results
     │                    │                         │
     │                    │                    (N) review_records ────── (1) users
     │                    │                         │
     └────────────────────┴────────────────────── (N) processing_logs
                                      │
                                      │
                                      │
                               statistics (独立表)
```

---

## 下一步

数据库初始化完成后,可以:

1. ✅ 测试数据库连接
2. ✅ 启动应用服务
3. ✅ 上传文档测试
4. ✅ 查看提取结果

```bash
# 启动服务
python main.py

# 访问 API 文档
# http://localhost:8000/docs
```

---

## 与 db/models.py 的一致性

本初始化脚本创建的9张表与 `db/models.py` 中的 SQLAlchemy 模型定义完全一致:

| 表名 | 字段数 | 外键 | 索引 | 状态 |
|------|--------|------|------|------|
| wells | 16 | 无 | 4个 | ✅ 一致 |
| documents | 15 | wells(well_no) | 6个 | ✅ 一致 |
| extracted_data | 12 | documents(id), wells(well_no) | 4个 | ✅ 一致 |
| quality_reports | 12 | documents(id), wells(well_no) | 3个 | ✅ 一致 |
| validation_results | 7 | documents(id) | 2个 | ✅ 一致 |
| users | 10 | 无 | 3个 | ✅ 一致 |
| review_records | 8 | documents(id), users(id) | 2个 | ✅ 一致 |
| processing_logs | 10 | documents(id) | 4个 | ✅ 一致 |
| statistics | 9 | 无 | 1个 | ✅ 一致 |

**关键修复**:
- ✅ 所有 `document_id` 外键使用 `INTEGER` 类型 (引用 `documents.id`)
- ✅ 表创建顺序正确，确保外键约束有效
- ✅ 添加了 `users` 表到 `review_records` 之前
- ✅ 添加了缺失的3张表: `validation_results`, `review_records`, `statistics`
- ✅ 添加了 `wells.status` 索引
- ✅ 添加了 `users.last_login_at` 字段
