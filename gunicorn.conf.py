import multiprocessing
import os
from dbgpt_app.dbgpt_server import (
    initialize_app,
    load_config,
    system_app,
    initialize_tracer,
)

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

# ==============================
# 日志配置
# ==============================
accesslog = "logs/gunicorn_access.log"
errorlog = "logs/gunicorn_error.log"
loglevel = "warning"  # Gunicorn 日志等级
os.environ["UVICORN_CMD_ARGS"] = "--log-level warning"  # Uvicorn Worker 日志等级


# ==============================
# 应用初始化
# ==============================
def on_starting(server):
    """
    Gunicorn 启动时初始化应用 + 初始化 trace
    """
    config_file = "configs/dbgpt-proxy-openai-hf.toml"

    # 1. 加载配置
    param = load_config(config_file)

    # 2. 设置 system_app 配置，保证内部组件可用
    system_app.config.configs["app_config"] = param

    # 3. 初始化应用（不要调用run_webserver）
    initialize_app(param)

    # 4. 初始化 tracer（模拟run_webserver内的逻辑）
    trace_config = param.service.web.trace or param.trace
    trace_file = trace_config.file or os.path.join(
        "logs", "dbgpt_webserver_tracer.jsonl"
    )
    initialize_tracer(
        trace_file,
        system_app=system_app,
        root_operation_name=trace_config.root_operation_name or "DB-GPT-Webserver",
        tracer_parameters=trace_config,
    )
