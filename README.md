# David Blog

一个基于 Django 5.2 构建的现代化个人博客系统。

## ✨ 特性

- **现代化设计**: 基于 Tailwind CSS + Alpine.js，支持响应式布局和深色模式
- **Markdown 支持**: 内置 Markdown 编辑器，支持代码高亮
- **全文搜索**: 集成 Whoosh/Elasticsearch 搜索引擎
- **评论系统**: 支持嵌套回复和邮件提醒
- **SEO 优化**: 自动生成 meta 标签，支持搜索引擎提交
- **插件系统**: 灵活的插件架构，易于扩展功能
- **高性能缓存**: 支持 Redis 缓存，提升访问速度
- **社交登录**: 支持 GitHub、Google 等 OAuth 登录

## 🛠️ 技术栈

- **后端**: Python 3.10+, Django 5.2
- **数据库**: SQLite (开发) / MySQL (生产)
- **前端**: Tailwind CSS 3.4, Alpine.js 3.13, HTMX 1.9
- **构建工具**: Vite 5.4
- **搜索引擎**: Whoosh / Elasticsearch

## 🚀 快速开始

### 1. 环境准备

```bash
# 克隆项目
git clone https://github.com/nomad2755/David_Blog.git
cd David_Blog

# 创建虚拟环境
python -m venv venv
venv\Scripts\activate  # Windows
# source venv/bin/activate  # Linux/Mac

# 安装依赖
pip install -r requirements.txt
```

### 2. 初始化数据库

```bash
# 执行数据库迁移
python manage.py migrate

# 创建超级管理员
python manage.py createsuperuser
```

### 3. 构建前端资源

```bash
cd frontend
npm install
npm run build
cd ..
```

### 4. 启动服务

```bash
# 收集静态文件
python manage.py collectstatic --noinput

# 启动开发服务器
python manage.py runserver 8000
```

访问 http://127.0.0.1:8000/ 查看博客首页。

## 📁 项目结构

```
David_Blog/
├── blog/              # 博客核心应用
├── accounts/          # 用户账户管理
├── comments/          # 评论系统
├── oauth/             # 第三方登录
├── plugins/           # 插件目录
│   ├── view_count/    # 浏览计数
│   ├── seo_optimizer/ # SEO 优化
│   └── ...            # 其他插件
├── templates/         # HTML 模板
├── frontend/          # 前端资源 (Vite)
└── djangoblog/        # 项目配置
```

## 🔧 配置说明

主要配置文件位于 `djangoblog/settings.py`，可以配置：

- 数据库连接
- 邮件发送
- 缓存后端
- OAuth 登录
- 站点信息

详细配置请参考 [配置文档](docs/config.md)。

## 📝 使用说明

### 后台管理

访问 http://127.0.0.1:8000/admin/ 登录后台管理系统，可以：

- 发布和管理文章
- 管理分类和标签
- 审核评论
- 配置站点信息
- 管理友情链接

### 个人介绍页面

访问 `/about.html` 查看个人介绍页面，可以在 `templates/blog/about.html` 中自定义内容。

## 🐳 Docker 部署

项目支持 Docker 部署，详见 [Docker 文档](docs/docker.md)。

```bash
docker-compose up -d
```

## 📄 许可证

本项目基于 MIT License 开源。
