# Windows psycopg2 编码问题解决方案

## 问题描述

在 Windows 上使用 psycopg2 连接 PostgreSQL 时，出现以下错误：

```
'utf-8' codec can't decode byte 0xd6 in position 61: invalid continuation byte
```

## 原因分析

### 根本原因

1. **Windows 代码页问题**
   - Windows 默认代码页: 936 (GBK)
   - PostgreSQL 服务器返回的消息使用 GBK 编码
   - psycopg2 期望 UTF-8 编码
   - 编码不匹配导致解码错误

2. **PostgreSQL 服务器配置**
   - PostgreSQL 服务器的客户端编码设置
   - 服务器消息使用的字符集

3. **psycopg2 的编码处理**
   - psycopg2 库内部的编码转换问题
   - Windows 上的已知 bug

---

## 解决方案

### 方案1: 修改 PostgreSQL 密码为纯ASCII（推荐）

#### 步骤1: 使用 pgAdmin 修改密码

1. 打开 pgAdmin
2. 连接到 PostgreSQL 服务器
3. 展开 Server Groups → Servers → PostgreSQL (localhost:5432)
4. 展开 Login/Roles
5. 右键点击 `postgres` → Properties
6. 在 Definition 标签页中，修改 Password 为纯ASCII:
   ```
   postgres123
   ```
7. 点击 Save

#### 步骤2: 更新所有配置文件

更新以下文件中的密码配置：

**1. `scripts/init_database.py`**
```python
# 修改前
ADMIN_DB_URL = f"postgresql://postgres:{admin_password}@localhost:5432/postgres"
# 修改后
ADMIN_DB_URL = "postgresql://postgres:postgres123@localhost:5432/postgres"
```

**2. `scripts/init_database_simple.py`**
```python
# 修改前
ADMIN_DB_URL = f"postgresql://postgres:{admin_password}@localhost:5432/postgres"
# 修改后
ADMIN_DB_URL = "postgresql://postgres:postgres123@localhost:5432/postgres"
```

**3. `main.py`（如果有）**
```python
# 修改前
DATABASE_URL = "postgresql://wellinfo:wellinfo2026@localhost:5432/wellinfo"
# 如果需要连接 postgres 数据库
ADMIN_DATABASE_URL = "postgresql://postgres:postgres123@localhost:5432/postgres"
```

#### 步骤3: 执行初始化

```bash
# 删除现有数据库（使用 pgAdmin 或其他工具）
# 在 pgAdmin 中:
# 1. 右键点击 wellinfo 数据库 → Delete/Drop

# 或者使用 psql（如果可用）
psql -U postgres -c "DROP DATABASE IF EXISTS wellinfo;"

# 执行初始化
venv\Scripts\python scripts/init_database.py
```

---

### 方案2: 使用 psql 命令行工具

如果系统中安装了 psql，可以直接使用：

```bash
# 设置 PostgreSQL bin 路径
set PATH=%PATH%;C:\Program Files\PostgreSQL\16\bin

# 连接并删除数据库
psql -U postgres -c "DROP DATABASE IF EXISTS wellinfo;"

# 执行初始化
python scripts/init_database.py
```

---

### 方案3: 使用 pgAdmin 直接操作（最简单）

#### 通过 pgAdmin 删除并重新创建

1. **删除数据库**
   - 在 pgAdmin 中找到 `wellinfo` 数据库
   - 右键 → Delete/Drop

2. **删除用户**
   - 展开 Login/Roles
   - 找到 `wellinfo` 用户
   - 右键 → Delete/Drop

3. **手动执行 SQL**
   - 打开 Query Tool
   - 执行以下 SQL:

```sql
-- 创建用户
CREATE USER wellinfo WITH PASSWORD 'wellinfo2026';

-- 创建数据库
CREATE DATABASE wellinfo OWNER = wellinfo
    ENCODING = 'UTF8'
    LC_COLLATE = 'en_US.UTF-8'
    LC_CTYPE = 'en_US.UTF-8'
    TEMPLATE = template0;

-- 授予权限
GRANT ALL PRIVILEGES ON DATABASE wellinfo TO wellinfo;

-- 连接到 wellinfo 数据库并授予权限
\c wellinfo

GRANT ALL ON SCHEMA public TO wellinfo;
```

4. **执行表创建脚本**
   - 在 Query Tool 中执行 `scripts/init_database.py` 中的 SQL 语句
   - 或者创建一个 SQL 脚本包含所有表创建语句

---

### 方案4: 配置 PostgreSQL 服务器编码（高级）

#### 修改 PostgreSQL 配置

1. **编辑 `postgresql.conf`**

路径: `C:\Program Files\PostgreSQL\16\data\postgresql.conf`

找到并修改以下配置：

```ini
# 客户端编码
client_encoding = utf8

# 或者设置为 SQL_ASCII（最简单）
# client_encoding = SQL_ASCII
```

2. **重启 PostgreSQL 服务**

```bash
net stop postgresql-x64-16
net start postgresql-x64-16
```

3. **重新尝试初始化**

```bash
python scripts/init_database.py
```

---

## 临时解决方案

### 当前问题解决

由于数据库 `wellinfo` 已存在，需要先删除：

#### 方法1: 使用 pgAdmin（推荐）

1. 打开 pgAdmin
2. 找到 `wellinfo` 数据库
3. 右键 → Delete/Drop
4. 确认删除

#### 方法2: 使用 SQL 脚本

创建一个纯文本 SQL 文件：

```sql
-- drop_database.sql
DROP DATABASE IF EXISTS wellinfo;
DROP USER IF EXISTS wellinfo;
```

通过 pgAdmin 的 Query Tool 执行。

#### 方法3: 暂时忽略警告

如果不想删除现有数据库，可以修改 `init_database.py` 跳过数据库创建步骤：

```python
# 在 create_database() 函数中找到:
if exists:
    logger.info("⚠️  数据库 'wellinfo' 已存在")
    # 修改为:
    logger.info("⚠️  数据库 'wellinfo' 已存在，跳过创建")
    # 继续执行后续步骤...
```

---

## 推荐操作步骤

### 快速解决（5分钟）

1. **使用 pgAdmin 删除现有数据库**
   - 打开 pgAdmin
   - 找到 `wellinfo` 数据库
   - 右键 → Delete/Drop

2. **修改 postgres 密码为纯ASCII**
   - 在 pgAdmin 中修改 postgres 用户密码为 `postgres123`

3. **更新配置文件**
   - 修改 `scripts/init_database.py`
   - 修改 `scripts/init_database_simple.py`
   - 密码改为 `postgres123`

4. **执行初始化**
   ```bash
   venv\Scripts\python scripts/init_database.py
   ```

---

## 长期解决方案

### 统一编码标准

1. **PostgreSQL 服务器配置**
   ```ini
   # postgresql.conf
   client_encoding = utf8
   ```

2. **Windows 系统编码**
   - 使用 UTF-8 语言支持（Windows 10 1809+）
   - 控制面板 → 区域 → 管理 → 更改系统区域设置
   - 勾选 "Beta版: 使用 Unicode UTF-8 提供全球语言支持"

3. **数据库密码**
   - 使用纯 ASCII 字符
   - 避免特殊符号
   - 使用强密码但不包含编码问题字符

---

## 常见错误

### 错误1: 'utf-8' codec can't decode byte 0xd6

**原因**: Windows GBK 编码与 UTF-8 不匹配

**解决**: 修改密码为纯 ASCII 或配置 PostgreSQL 编码

---

### 错误2: fe_sendauth: no password supplied

**原因**: pgpass 文件不被识别

**解决**: 直接在代码中指定密码（纯 ASCII）

---

### 错误3: password authentication failed

**原因**: 密码错误或包含特殊字符

**解决**: 修改为纯 ASCII 密码

---

## 相关文件

| 文件 | 说明 | 需要修改 |
|------|------|---------|
| `scripts/init_database.py` | 完整初始化脚本 | ✅ 密码配置 |
| `scripts/init_database_simple.py` | 简化初始化脚本 | ✅ 密码配置 |
| `scripts/drop_database.py` | 删除数据库脚本 | ✅ 密码配置 |
| `main.py` | 主程序 | ⚠️ 可能有数据库连接 |
| `.env` | 环境变量（如果有） | ⚠️ 可能有数据库连接 |

---

## 总结

### 临时解决
- 使用 pgAdmin 手动删除数据库
- 修改密码为纯 ASCII
- 更新配置文件
- 执行初始化

### 长期解决
- 配置 PostgreSQL 使用 UTF-8
- 修改 Windows 系统编码为 UTF-8
- 所有密码使用纯 ASCII 字符
- 统一项目编码标准

---

**推荐优先使用方案1（修改密码为纯 ASCII），这是最简单且最可靠的方法。** ✅
