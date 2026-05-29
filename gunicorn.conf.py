# Gunicorn 配置文件
import multiprocessing

# 绑定地址
bind = "127.0.0.1:8000"

# 工作进程数 (建议 CPU核心数 * 2 + 1)
workers = multiprocessing.cpu_count() * 2 + 1

# 工作模式
worker_class = "gthread"
threads = 2

# 超时时间
timeout = 120

# 最大请求数，超过后重启worker（防止内存泄漏）
max_requests = 1000
max_requests_jitter = 50

# 日志
accesslog = "/root/blog/logs/gunicorn_access.log"
errorlog = "/root/blog/logs/gunicorn_error.log"
loglevel = "info"

# 进程名
proc_name = "djangoblog"

# 安全设置
limit_request_line = 4094
limit_request_fields = 100
limit_request_field_size = 8190
