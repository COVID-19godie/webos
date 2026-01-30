# Gunicorn 生产环境配置

# 绑定地址
bind = '127.0.0.1:8000'

# 工作进程数（建议：CPU核心数 * 2 + 1）
workers = 2

# 工作模式
worker_class = 'sync'

# 超时设置
timeout = 120
keepalive = 5
graceful_timeout = 30

# 最大请求数（防止内存泄漏）
max_requests = 1000
max_requests_jitter = 50

# 日志配置
errorlog = '/www/wwwroot/zmg-webos/logs/gunicorn_error.log'
accesslog = '/www/wwwroot/zmg-webos/logs/gunicorn_access.log'
loglevel = 'info'
access_log_format = '%(h)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s"'

# 进程名
proc_name = 'zmg-backend'

# 守护进程（宝塔使用 supervisor 管理，设为 False）
daemon = False

# 预加载应用
preload_app = True
