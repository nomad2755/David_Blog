# DjangoBlog 项目 AI 操作日志

> 本文件记录所有 AI 助手对项目的修改操作，便于追踪变更历史和解决问题。

---

## 📅 2026-04-21 - 个性化定制与功能增强

### 操作概述
对项目进行品牌标识移除、站点信息个性化，并添加个人介绍页面功能。

### 详细修改记录

#### 1. 服务启动与调试
- **问题**: 多进程占用 8000 端口导致服务无法启动
- **解决**: 使用 `taskkill /F /IM python.exe` 清理所有 Python 进程后重启
- **命令**: `python manage.py runserver 8000`

#### 2. 模板错误修复
- **文件**: `templates/blog/article_index.html`
- **问题**: `{% query article_list|length as article_count %}` 导致 AttributeError
- **原因**: `query` 标签期望 QuerySet，但 `length` 过滤器返回整数
- **修复**: 直接使用 `{{ article_list|length }}` 替代

#### 3. 品牌标识移除

##### 3.1 侧边栏 GitHub 徽章
- **文件**: `templates/blog/tags/sidebar.html`
- **操作**: 删除第 147-165 行的 GitHub Stars/Forks 徽章区域
- **影响**: 移除了指向原作者 liangliangyy/DjangoBlog 的链接

##### 3.2 页脚外部链接
- **文件**: `templates/share_layout/footer.html`
- **操作**: 
  - 移除"工具站"链接（指向 tools.lylinux.net）
  - 移除 GitHub 文本链接和图标按钮
  - 修改文案从 "Built with Django & Tailwind CSS" 改为 "Made with ❤ for sharing knowledge"

##### 3.3 导航栏外部链接
- **文件**: `templates/share_layout/nav.html`
- **操作**: 
  - 移除桌面端导航的"工具站"链接
  - 移除移动端导航的"工具站"链接

#### 4. 站点信息个性化
- **方式**: 通过 Django Shell 更新数据库 BlogSettings 表
- **命令**: 
```python
python manage.py shell -c "from blog.models import BlogSettings; settings = BlogSettings.objects.first(); settings.site_name = '我的个人博客'; settings.site_description = '分享技术心得，记录生活点滴'; settings.site_keywords = '技术,编程,生活'; settings.save()"
```
- **修改前**:
  - 站点名称: djangoblog
  - 站点描述: 基于Django的博客系统
  - 关键字: Django,Python
- **修改后**:
  - 站点名称: 我的个人博客
  - 站点描述: 分享技术心得，记录生活点滴
  - 关键字: 技术,编程,生活

#### 5. 新增个人介绍页面

##### 5.1 视图层
- **文件**: `blog/views.py`
- **新增类**: `AboutView(ListView)`
- **功能**: 
  - 模板: `blog/about.html`
  - SEO 配置: 标题、描述、关键字
  - 返回空查询集（不需要文章列表）

##### 5.2 URL 路由
- **文件**: `blog/urls.py`
- **新增路由**: `path('about.html', views.AboutView.as_view(), name='about')`
- **访问地址**: http://127.0.0.1:8000/about.html

##### 5.3 页面模板
- **文件**: `templates/blog/about.html` (新建)
- **内容结构**:
  - 页面标题: "关于我"
  - 介绍板块: 关于博客、技术栈、兴趣爱好、联系方式
  - 返回按钮: 链接到首页
  - 响应式设计，支持深色模式

##### 5.4 导航栏集成
- **文件**: `templates/share_layout/nav.html`
- **桌面端**: 在"归档"后添加 "About Me" 链接
- **移动端**: 用户后续删除了移动端的"关于"链接
- **激活状态**: 当前路径为 `/about.html` 时高亮显示

#### 6. 导航栏文案调整
- **文件**: `templates/share_layout/nav.html`
- **修改**: 将"关于"改为 "About Me"
- **位置**: 桌面端导航栏

### 技术要点

#### 数据库配置切换
- **原配置**: MySQL (`django.db.backends.mysql`)
- **新配置**: SQLite (`django.db.backends.sqlite3`)
- **原因**: 简化本地调试环境，避免 MySQL 连接问题
- **文件**: `djangoblog/settings.py`

#### 缓存机制
- 项目使用 Redis/Memcached 缓存
- 关键缓存键: `index_1`, `sidebarp`, `get_blog_setting`
- 归档页面使用 `cache_page(60 * 60)` 缓存 1 小时

#### 插件系统
- 已加载插件: article_copyright, reading_time, external_links, view_count, seo_optimizer, image_lazy_loading, article_recommendation
- Cloudflare 插件因缺少环境变量被禁用

### 遇到的问题与解决

1. **端口冲突**
   - 症状: 多个 Python 进程占用 8000 端口
   - 解决: `taskkill /F /IM python.exe` 强制终止所有进程

2. **模板渲染错误**
   - 症状: `AttributeError: 'int' object has no attribute 'filter'`
   - 原因: 误用 `query` 模板标签
   - 解决: 改用直接的 `length` 过滤器

3. **浏览器缓存问题**
   - 症状: 修改后页面仍显示旧内容
   - 解决: 强制刷新 (`Ctrl + Shift + R`) 或清除浏览器缓存

### 文件清单

#### 修改的文件
- `blog/views.py` - 添加 AboutView
- `blog/urls.py` - 添加 about 路由
- `djangoblog/settings.py` - 数据库配置改为 SQLite
- `templates/blog/article_index.html` - 修复 query 标签
- `templates/blog/tags/sidebar.html` - 移除 GitHub 徽章
- `templates/share_layout/footer.html` - 移除外部链接，修改文案
- `templates/share_layout/nav.html` - 添加 About Me 链接

#### 新增的文件
- `templates/blog/about.html` - 个人介绍页面模板
- `db.sqlite3` - SQLite 数据库文件
- `AI_OPERATIONS_LOG.md` - 本操作日志文件

### 验证结果
- ✅ 服务器正常运行在 http://127.0.0.1:8000/
- ✅ 首页正常显示，无 DjangoBlog 品牌标识
- ✅ 个人介绍页面可访问: http://127.0.0.1:8000/about.html
- ✅ 导航栏 "About Me" 链接正常工作
- ✅ 所有静态资源加载成功

### 后续建议
1. 自定义 `about.html` 中的个人信息（邮箱、社交账号等）
2. 考虑添加 favicon.ico 解决 404 警告
3. 如需移动端"About Me"链接，可在 nav.html 中重新添加
4. 定期备份 `db.sqlite3` 数据库文件

---

## 📝 使用说明

### 如何更新此日志
每次 AI 执行重要操作后，在此文件末尾添加新的章节，包含：
- 日期和操作概述
- 详细的修改记录（文件路径、具体变更）
- 遇到的问题和解决方案
- 技术要点和注意事项

### 日志格式规范
- 使用 Markdown 格式
- 按时间倒序排列（最新的在最上面）
- 每个操作包含完整的文件路径
- 记录关键命令和代码片段
- 标注成功/失败状态

---

*最后更新: 2026-04-21*
*维护者: AI Assistant*
