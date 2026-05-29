# David Blog - 部署文档

## 📌 项目概述

David Blog 是一个基于 Django 5.2 构建的现代化个人博客系统，前端使用 Tailwind CSS + Alpine.js + HTMX，通过 Vite 构建前端资源。

**服务器信息：**
- 公网 IP：`122.152.202.29`
- 操作系统：Ubuntu 24.04
- Python：3.12
- Node.js：22.x

**访问地址：**
- 博客首页：http://122.152.202.29
- 后台管理：http://122.152.202.29/admin/
- 前台登录：http://122.152.202.29/login/

**管理员账号：**
- 用户名：`admin`
- 密码：`admin123456`（请及时修改）

---

## 🏗️ 部署架构

```
用户请求 → Nginx(:80) → Gunicorn(:8000) → Django
                ↓
          静态文件直接返回
          (/static/ → /var/www/blog/static/)
          (/media/  → /var/www/blog/media/)
```

- **Nginx**：反向代理 + 静态文件服务，监听 `0.0.0.0:80`
- **Gunicorn**：WSGI 应用服务器，监听 `127.0.0.1:8000`，systemd 托管
- **静态文件**：由 Nginx 直接提供，路径 `/var/www/blog/static/`

---

## 🚀 服务器环境搭建步骤

### 1. 系统依赖安装

```bash
apt install -y python3.12-venv default-libmysqlclient-dev build-essential pkg-config nginx
```

### 2. 克隆项目

```bash
mkdir -p /root/blog
cd /root/blog
git clone --depth 1 https://github.com/nomad2755/David_Blog.git .
```

### 3. Python 虚拟环境

```bash
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
pip install gunicorn
```

### 4. 前端构建

```bash
cd frontend
npm install
npm run build
cd ..
```

### 5. Django 初始化

```bash
source venv/bin/activate

# 数据库迁移
python manage.py migrate

# 创建管理员
DJANGO_SUPERUSER_PASSWORD=admin123456 python manage.py createsuperuser --username admin --email admin@example.com --noinput

# 收集静态文件
python manage.py collectstatic --noinput
```

### 6. 静态文件部署到 Nginx

```bash
mkdir -p /var/www/blog/static /var/www/blog/media
cp -r /root/blog/collectedstatic/* /var/www/blog/static/
cp -r /root/blog/uploads/* /var/www/blog/media/ 2>/dev/null
chown -R www-data:www-data /var/www/blog
```

### 7. Gunicorn 配置

配置文件：`/root/blog/gunicorn.conf.py`

```python
import multiprocessing
bind = "127.0.0.1:8000"
workers = multiprocessing.cpu_count() * 2 + 1
worker_class = "gthread"
threads = 2
timeout = 120
max_requests = 1000
max_requests_jitter = 50
accesslog = "/root/blog/logs/gunicorn_access.log"
errorlog = "/root/blog/logs/gunicorn_error.log"
loglevel = "info"
```

### 8. Systemd 服务

文件：`/etc/systemd/system/djangoblog.service`

```ini
[Unit]
Description=David Blog Gunicorn Server
After=network.target

[Service]
Type=notify
User=root
Group=root
WorkingDirectory=/root/blog
ExecStart=/root/blog/venv/bin/gunicorn -c gunicorn.conf.py djangoblog.wsgi:application
ExecReload=/bin/kill -s HUP $MAINPID
KillMode=mixed
TimeoutStopSec=5
PrivateTmp=true
Restart=on-failure
RestartSec=5

[Install]
WantedBy=multi-user.target
```

启用并启动：

```bash
systemctl daemon-reload
systemctl enable djangoblog
systemctl start djangoblog
```

### 9. Nginx 配置

文件：`/etc/nginx/sites-available/djangoblog`

```nginx
server {
    listen 80;
    server_name _;

    access_log /root/blog/logs/nginx_access.log;
    error_log  /root/blog/logs/nginx_error.log;

    client_max_body_size 10M;

    gzip on;
    gzip_min_length 1024;
    gzip_types text/plain text/css application/json application/javascript text/xml application/xml text/javascript image/svg+xml;
    gzip_vary on;

    location /static/ {
        alias /var/www/blog/static/;
        expires 30d;
        add_header Cache-Control "public, immutable";
    }

    location /media/ {
        alias /var/www/blog/media/;
        expires 7d;
    }

    location /favicon.ico {
        alias /var/www/blog/static/favicon.ico;
        log_not_found off;
    }

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_redirect off;
        proxy_connect_timeout 60s;
        proxy_read_timeout 120s;
    }
}
```

启用：

```bash
ln -sf /etc/nginx/sites-available/djangoblog /etc/nginx/sites-enabled/djangoblog
rm -f /etc/nginx/sites-enabled/default
nginx -t
systemctl enable nginx
systemctl restart nginx
```

---

## 🔧 已完成的代码修改

### 1. Django 设置 (`djangoblog/settings.py`)

- `ALLOWED_HOSTS` 添加了服务器公网 IP `122.152.202.29`
- `CSRF_TRUSTED_ORIGINS` 添加了 `http://122.152.202.29`

### 2. 默认主题改为亮色 (`frontend/src/features/darkMode.js`)

**问题：** 新用户首次访问时，由于 `localStorage` 无记录且默认返回 `dark`，导致页面（特别是登录页输入框）背景为黑色。

**修改：** `getPreferredTheme()` 函数默认返回值从 `'dark'` 改为 `'light'`。

### 3. 首屏关键 CSS 增强 (`templates/share_layout/base.html`)

**问题：** Tailwind CSS 文件较大（~150KB），加载前页面只有极少的内联样式，导致首次访问布局偏小、闪烁。

**修改：** 在 `<style>` 标签中补充了：
- 完整的主题色 CSS 变量
- `font-size: 16px` 基准字号
- `box-sizing: border-box` 全局盒模型
- `max-w-6xl`、`px-4` 等容器基础样式
- 浏览器 autofill 输入框变黑修复

### 4. 登录页关键 CSS (`templates/share_layout/base_account.html`)

**问题：** 登录页使用独立的 `base_account.html` 模板，完全没有内联关键 CSS，导致输入框背景黑色、布局异常。

**修改：** 补全了与 `base.html` 一致的关键 CSS，包括：
- CSS 变量定义
- 表单元素基础样式
- autofill 修复
- Tailwind 快捷类（`bg-background`、`text-foreground` 等）

### 5. 分类导航高亮 (`templates/share_layout/nav.html`)

**问题：** HTMX `hx-boost` 只刷新 `#main` 区域，导航栏不会重新渲染，导致点击分类后选中状态不更新。

**修改：**
- 分类链接默认：黑色文字 + hover 绿色
- 当前选中分类：绿色背景 + 白色文字
- 子分类父级按钮同步使用绿色高亮

### 6. HTMX 导航状态同步 (`frontend/src/main.js`)

**问题：** HTMX 局部刷新后，导航栏高亮状态不会更新。

**修改：** 添加 `updateNavActiveState()` 函数，在 `htmx:afterSwap` 事件中自动更新分类链接的激活状态。

### 7. Gunicorn 生产配置 (`gunicorn.conf.py`)

新增 Gunicorn 配置文件，使用 gthread 工作模式，配置日志路径和性能参数。

---

## 📋 常用运维命令

```bash
cd /root/blog
source venv/bin/activate

# === 服务管理 ===
systemctl restart djangoblog      # 重启 Gunicorn
systemctl restart nginx            # 重启 Nginx
systemctl status djangoblog        # 查看 Gunicorn 状态
systemctl status nginx             # 查看 Nginx 状态

# === 日志查看 ===
tail -f logs/gunicorn_error.log    # Gunicorn 错误日志
tail -f logs/gunicorn_access.log   # Gunicorn 访问日志
tail -f logs/nginx_access.log      # Nginx 访问日志
tail -f logs/nginx_error.log       # Nginx 错误日志

# === 代码更新流程 ===
git pull origin master             # 拉取最新代码
python manage.py migrate           # 执行数据库迁移
python manage.py collectstatic --noinput  # 收集静态文件
rm -rf /var/www/blog/static/*      # 清空旧静态文件
cp -r collectedstatic/* /var/www/blog/static/  # 部署新静态文件
chown -R www-data:www-data /var/www/blog
systemctl restart djangoblog       # 重启服务

# === 前端重新构建 ===
cd frontend
npm install
npm run build
cd ..
python manage.py collectstatic --noinput
rm -rf /var/www/blog/static/*
cp -r collectedstatic/* /var/www/blog/static/
chown -R www-data:www-data /var/www/blog
systemctl restart djangoblog

# === 数据库管理 ===
python manage.py createsuperuser   # 创建管理员
python manage.py shell             # Django Shell
python manage.py dbshell           # 数据库 Shell

# === 清除缓存 ===
python manage.py shell -c "from django.core.cache import cache; cache.clear()"
```

---

## ⚠️ 注意事项

1. **安全组**：腾讯云安全组需放行 TCP:80 端口
2. **数据库**：当前使用 SQLite，生产环境建议切换 MySQL
3. **HTTPS**：建议配置 SSL 证书（Let's Encrypt）
4. **密码**：请及时修改管理员默认密码
5. **静态文件**：每次执行 `collectstatic` 后需同步到 `/var/www/blog/static/`
6. **前端修改**：修改 `frontend/` 下的文件后需重新 `npm run build`
