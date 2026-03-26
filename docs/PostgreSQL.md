# PostgreSQL

常用操作

```bash
pgAdmin  # Management Tools for PostgreSQL
psql  # SQL Shell
Server [localhost]:
Database [postgres]:
Port [5432]:
Username [postgres]:
用户 postgres 的口令：

SELECT version();

postgresql://[用户名[:密码]@][主机][:端口][/数据库名][?参数]

postgresql://wellinfo:wellinfo2026@localhost:5432/wellinfo

-- 创建用户 wellinfo，并设置密码
CREATE USER wellinfo WITH PASSWORD 'wellinfo2026';

-- 创建数据库 wellinfo，并指定所有者
CREATE DATABASE wellinfo OWNER wellinfo;

-- 可选：授予 wellinfo 用户对该数据库的所有权限
GRANT ALL PRIVILEGES ON DATABASE wellinfo TO wellinfo;

```



The database superuser (`postgres`)

```bash
password: 14372026
port: 5432
locale: DEFAULT

# 以超级用户身份连接数据库：
psql -U postgres -d postgres
# 执行修改密码的 SQL 命令
ALTER USER postgres WITH PASSWORD '1437@2026';

# 列出所有数据库
\l
SELECT datname FROM pg_database;

# 切换数据库
\c wellinfo

# 列出所有表
\dt
SELECT table_name FROM information_schema.tables WHERE table_schema = 'public';

# 查看用户（角色）
\du
SELECT rolname FROM pg_roles;
# 收回数据库权限
REVOKE ALL PRIVILEGES ON DATABASE dbname FROM username;
# 收回模式权限（如 public 模式）
REVOKE ALL PRIVILEGES ON SCHEMA public FROM username;
# 收回表权限
REVOKE ALL PRIVILEGES ON ALL TABLES IN SCHEMA schema_name FROM username;
# 收回默认权限（如果用户设置了 ALTER DEFAULT PRIVILEGES）
ALTER DEFAULT PRIVILEGES FOR ROLE username REVOKE ALL ON TABLES FROM public;
# 也可以使用 DROP OWNED BY username 一次性清理所有依赖权限
# 删除数据库
DROP DATABASE dbname;
# 删除用户（角色）
# 直接删除（若无依赖）
DROP USER username; 或 DROP ROLE rolename;
# 如果用户拥有对象或权限，需先清理依赖，常见步骤：
# 转移所有权（将用户拥有的对象转给其他用户，如 postgres）
REASSIGN OWNED BY username TO postgres;
# 清除用户在其他对象上的权限及默认权限
DROP OWNED BY username;
# 现在可以安全删除
DROP USER username;

# DROP OWNED 会删除用户拥有的所有对象（表、视图等），如果对象需要保留，请先用 REASSIGN OWNED 转移所有权。


---
Installation Directory: D:\InstallFiles\PostgreSQL\18
Server Installation Directory: D:\InstallFiles\PostgreSQL\18
Data Directory: D:\InstallFiles\PostgreSQL\18\data
Database Port: 5432
Database Superuser: postgres
Operating System Account: NT AUTHORITY\NetworkService
Database Service: postgresql-x64-18
Command Line Tools Installation Directory: D:\InstallFiles\PostgreSQL\18
pgAdmin4 Installation Directory: D:\InstallFiles\PostgreSQL\18\pgAdmin 4
Stack Builder Installation Directory: D:\InstallFiles\PostgreSQL\18
Installation Log: C:\Users\zanef\AppData\Local\Temp\install-postgresql.log
```

### MINIO

```text
D:\InstallFiles\minio\bin\minio.exe
D:\InstallFiles\minio\data
cd /d D:\InstallFiles\minio\bin
minio.exe server D:\InstallFiles\minio\data --console-address ":9001"

```

### Requiments.txt

```bash
# paddlepaddle==3.3.0
python -m pip install paddlepaddle==3.3.0 -i https://www.paddlepaddle.org.cn/packages/stable/cpu/

# paddleocr==2.7.0.3
# If you only want to use the basic text recognition feature (returns text position coordinates and content), including the PP-OCR series
python -m pip install paddleocr
# If you want to use all features such as document parsing, document understanding, document translation, key information extraction, etc.
# python -m pip install "paddleocr[all]"
```


## 删除远程 git 仓库的文件
```bash
# .gitignore 增加 .workbuddy

# 1. 从 Git 中移除 .workbuddy
git rm -r --cached .workbuddy

# 2. 提交
git commit -m "chore: 清理 .workbuddy 目录"

# 3. 推送
git push origin master
```