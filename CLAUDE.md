# David Blog - 项目记忆

## 基本信息

- **项目地址**：/root/blog/
- **Git 仓库**：https://github.com/nomad2755/David_Blog.git
- **技术栈**：Django 5.2 + Tailwind CSS + Alpine.js + HTMX + Vite
- **公网 IP**：122.152.202.29
- **访问地址**：http://122.152.202.29
- **后台管理**：http://122.152.202.29/admin/
- **管理员**：admin / admin123456

## 部署架构

```
Nginx(:80) → Gunicorn(:8000, 127.0.0.1) → Django
    ↓
静态文件: /var/www/blog/static/ (Nginx 直接提供)
媒体文件: /var/www/blog/media/
```

## 服务管理

```bash
systemctl restart djangoblog    # 重启 Gunicorn
systemctl restart nginx         # 重启 Nginx
```

## 静态文件部署流程

每次 collectstatic 后必须同步到 Nginx 目录：
```bash
source venv/bin/activate
python manage.py collectstatic --noinput
rm -rf /var/www/blog/static/*
cp -r collectedstatic/* /var/www/blog/static/
chown -R www-data:www-data /var/www/blog
```

## 前端构建流程

修改 frontend/ 下的文件后：
```bash
cd /root/blog/frontend && npm run build
# 然后执行上面的静态文件部署流程
systemctl restart djangoblog
```

## 已完成的改动

1. **settings.py** - ALLOWED_HOSTS/CSRF 添加公网 IP；Redis 缓存自动检测配置
2. **darkMode.js** - 默认主题改为 light（修复输入框黑色问题）
3. **base.html** - 增强首屏关键 CSS（防布局闪烁）
4. **base_account.html** - 补全登录页关键 CSS
5. **nav.html** - 分类导航绿色高亮交互
6. **main.js** - HTMX 导航状态同步（hx-boost 下选中状态更新）
7. **gunicorn.conf.py** - 生产环境 Gunicorn 配置
8. **mdeditor 粘贴图片** - `static/admin/js/mdeditor_paste_image.js`，支持编辑器内 Ctrl+V 粘贴/拖拽图片
9. **个人简历系统** - BlogSettings 新增 resume_* 字段，后台 fieldsets 分组管理
10. **简历前端展示** - about.html 新增个人信息、联系方式、个人优势、工作经历、最近项目等区块
11. **Admin JSON 辅助** - `static/admin/js/resume_json_helper.js`，工作经历 JSON 填入示例/格式化/验证
12. **split_comma 过滤器** - `blog/templatetags/blog_tags.py`，逗号分隔字符串转列表
13. **Redis 缓存** - 解决 LocMemCache 多 worker 缓存不一致问题，自动检测本地 Redis
14. **评论系统增强** - 支持游客评论（姓名+邮箱），评论表单优化
15. **文章编辑页优化** - `templates/blog/article_edit.html` 前端编辑体验增强

## 待处理

- [ ] 配置 HTTPS（Let's Encrypt）
- [ ] 生产环境切换 MySQL
- [ ] 修改管理员默认密码

## 分类列表

- Software Technology (ID: 3)
- English (ID: 4)
- AI (ID: 5)

## 关键路径

- 虚拟环境: /root/blog/venv/
- Django 配置: /root/blog/djangoblog/settings.py
- 前端源码: /root/blog/frontend/
- Vite 构建产物: /root/blog/blog/static/blog/dist/
- Gunicorn 配置: /root/blog/gunicorn.conf.py
- Gunicorn 服务: /etc/systemd/system/djangoblog.service
- Nginx 配置: /etc/nginx/sites-available/djangoblog
- 日志目录: /root/blog/logs/
