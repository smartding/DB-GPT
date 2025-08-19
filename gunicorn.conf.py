import multiprocessing

from dbgpt_app.dbgpt_server import initialize_app, load_config, system_app

# ==============================
# Gunicorn 基本配置
# ==============================
bind = "0.0.0.0:5670"
workers = multiprocessing.cpu_count() * 2 + 1
worker_class = "uvicorn.workers.UvicornWorker"

worker_connections = 1000
max_requests = 1000
max_requests_jitter = 100
preload_app = True

accesslog = "logs/gunicorn_access.log"
errorlog = "logs/gunicorn_error.log"
loglevel = "warning"


# ==============================
# 应用初始化
# ==============================
def on_starting(server):
    """
    Gunicorn 启动时初始化应用
    """
    config_file = "configs/dbgpt-proxy-openai-hf.toml"

    # 1. 加载配置
    param = load_config(config_file)

    # 2. 保证 system_app.config.configs["app_config"] 已设置
    system_app.config.configs["app_config"] = param

    # 3. 调用 initialize_app 初始化组件（不要调用 run_webserver）
    initialize_app(param)
