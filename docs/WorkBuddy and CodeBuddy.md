# `WorkBuddy` and `CodeBuddy`

`WorkBuddy`（管项目、执行、自动化） + `CodeBuddy`（写代码、架构、编码）

### 核心分工

| 助手      | 角色            | 职责                                                       |
| :-------- | :-------------- | :--------------------------------------------------------- |
| CodeBuddy | 架构师 + 程序员 | 输出技术方案、编写代码、设计数据库、定义接口、解决技术问题 |
| WorkBuddy | 项目经理 + 运维 | 在本地创建项目、初始化 Git、运行命令、启动服务、提交代码   |

**你的角色**：提需求、验收结果。

### 为什么需要两个助手？

CodeBuddy 擅长**生成代码和技术设计**，但它不能直接操作你的电脑（创建文件夹、打开终端、执行命令）。
WorkBuddy 则负责**执行这些实际操作**，让项目从设计落地为可运行的工程。

如果你只让 CodeBuddy 做所有事，你仍需要手动去创建目录、安装依赖、运行命令——这正是 WorkBuddy 可以帮你自动完成的。

## 落地流程

### 0. 构建环境

1. 在电脑里创建根目录：

   ```
   d:\workspaces\well-keyinfo-extraction
   ```

2. 在里面新建文件夹 

   ```
   docs
   ```

   ，把你的需求文档放进去：

   ```
   d:\workspaces\well-keyinfo-extraction\docs\AI-驱动油气井关键信息提取.md
   ```

### 1. 让 WorkBuddy 完整理解需求

打开 WorkBuddy，绑定工作区：

```
d:\workspaces\well-keyinfo-extraction
```

```text
我现在的项目根目录是：d:/workspaces/well-info-extraction/

请读取：@/docs/AI-驱动油气井关键信息提取.md 和 @/ocs/AI-驱动油气井关键信息提取-AI模型构建.md

进行需求分析，并输出需求分析文档。结果保存到 docs/AI-驱动油气井关键信息提取-需求分析.md

```

### 2. 架构设计（WorkBuddy -> CodeBuddy 评审）

#### 2.1 发给 WorkBuddy

```text
基于 @/docs/AI-驱动油气井关键信息提取-需求分析.md 

进行架构设计，并输出架构设计文档，结果保存到 docs/AI-驱动油气井关键信息提取-架构设计.md

请自动创建完整的项目目录结构，并生成 PROJECT_CONTEXT.md 全局上下文文件。
```



#### 2.2 发给 CodeBuddy（评审 + 加固）

```text
基于 @/@PROJECT_CONTEXT.md
请评审 @/docs/AI-驱动油气井关键信息提取-架构设计.md
给出可直接开发的最终架构。
```

#### 2.3 生成实现代码（CodeBuddy 负责）

```text
基于 @/@PROJECT_CONTEXT.md

- 创建项目目录结构
- 实现配置模块
- 实现数据库模型
- 实现文档预处理模块
- 实现AI模型模块
- 实现校验模块
- 实现处理管道
- 实现API接口
- 创建依赖文件和配置

```





```text
基于 @/PROJECT_CONTEXT.md 和需求文档 @/docs/AI-驱动油气井关键信息提取.md
帮我输出：
整体技术路线
各阶段模型选型
提示词设计原则
文档分类提示词
井号识别提示词
各类文档字段抽取提示词
最终要提取的油气井关键字段清单
功能模块划分
按天 / 按模块的开发计划
保存到：docs/DEVELOPMENT_PLAN.md
```

### 3. 让 WorkBuddy 生成依赖、启动脚本、入口文件

```text
基于当前项目结构，自动生成：
requirements.txt
src/main.py 主入口
run.bat 一键启动脚本
README.md
```





### 标准工作流

#### 1. 给 CodeBuddy 发技术方案

```text
我现在有一个 AI 驱动油气井关键信息提取的项目，技术方案如下：
[粘贴你的方案]
请帮我：
- 梳理架构
- 设计数据库
- 输出接口清单
- 给出目录结构
- 生成可运行代码
```

#### 2. 让 WorkBuddy 创建项目骨架

你可以把 CodeBuddy 输出的设计（目录结构、技术栈、数据库等）**复制粘贴**给 WorkBuddy，然后让它执行。

也可以让 CodeBuddy 把设计保存成一个 `design.md` 或 `project.json` 文件，然后让 WorkBuddy 读取该文件来创建项目。

```text
CodeBuddy设计输出目录：C:\Users\zanef\CodeBuddy\Claw\

根据如上 CodeBuddy 的设计内容：
1. 在 D:\Workspaces\ 下创建项目文件夹
2. 初始化 Git 仓库(github 账号/密码：zanef0211/1234Iqwer)
3. 生成前后端目录结构

```

#### 3. 让 CodeBuddy 填充核心代码

```text


按照之前的设计，请生成：
- 数据库模型（SQLAlchemy / Prisma / …）
- 后端接口（Controller / Service / Dao）
- 统一响应格式、异常处理
- JWT 登录认证
```

#### 4. 让 WorkBuddy 运行与部署

```text
请帮我：
- 安装依赖
- 启动后端服务（端口 8080）
- 启动前端
- 运行测试
- 提交 Git（feat: 完成第一版）
```

### 日常迭代（一句话完成）

你每天只需说：

```text
今天实现用户管理模块：增删改查，字段：用户名、邮箱、角色。
CodeBuddy 写代码，WorkBuddy 负责运行、测试、提交。
```





### 二、开始启动项目

#### 第 1 步：把你的「技术方案」发给 AI

打开 **WorkBuddy / CodeBuddy**，直接发：

```text
我现在有一个开发项目，我把技术方案发给你，
你帮我：
1. 梳理项目架构
2. 拆分成开发步骤
3. 生成技术栈选型
4. 生成数据库设计
5. 生成接口文档
6. 生成完整可运行代码
```

然后把你的方案粘贴进去。

#### 第 2 步：让 `CodeBuddy` 输出「可执行架构」

继续发：

```text
用CodeBuddy帮我输出：
1. 项目目录结构
2. 技术栈（前端/后端/数据库/中间件）
3. 接口清单
4. 数据库表结构
5. 开发排期（按模块拆分）
```

它会给你**工程化、可直接落地**的结构，不是空话。

#### 第 3 步：让 WorkBuddy 帮你「创建项目」

在 **WorkBuddy** 里发（这一步它会真的在你电脑上创建项目）：

```text
根据刚才的架构，帮我：
1. 在 D:\dev\ 下创建项目文件夹
2. 初始化 Git 仓库
3. 创建前后端目录结构
4. 生成基础项目模板
5. 打开 VS Code
```

WorkBuddy 会**自动操作你的电脑**，10 秒建好项目骨架。

#### 第 4 步：CodeBuddy 开始写核心代码

切换到 **CodeBuddy（CLI 或 VS Code 插件）**：

```text
帮我生成：
1. 数据库模型（SQL/MyBatis/Prisma 任选）
2. 后端接口（Controller/Service/Dao）
3. 统一返回格式、异常处理
4. 权限、登录、JWT
```

CodeBuddy 会**一次性生成多文件、可直接运行**的代码。

#### 第 5 步：WorkBuddy 帮你运行、调试、部署

回到 WorkBuddy：

```text
帮我：
1. 安装依赖
2. 启动后端服务
3. 启动前端
4. 查看端口是否占用
5. 运行测试
```

它会**自动打开终端、执行命令、看日志**。

#### 第 6 步：迭代开发（你只需要说需求）

你以后每天只需要做这一步：

```text
今天实现【XX模块】：
- 功能1：XXX
- 功能2：XXX
- 字段：XXX
CodeBuddy写代码，WorkBuddy负责运行、测试、提交Git。
```

#### 第 7 步：自动提交 Git（超级省心）

```text
WorkBuddy，帮我：
git add .
git commit -m "feat: 完成XX模块"
git push
```

