import multiprocessing
import os

from dbgpt.util.parameter_utils import _get_dict_from_obj
from dbgpt.util.system_utils import get_system_info
from dbgpt.util.tracer import SpanType, SpanTypeRunName, initialize_tracer, root_tracer
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

# ==============================
# 日志配置
# ==============================
accesslog = "logs/gunicorn_access.log"
errorlog = "logs/gunicorn_error.log"
loglevel = "warning"
os.environ["UVICORN_CMD_ARGS"] = "--log-level warning"

# ==============================
# 全局变量存储 param 和 root span
# ==============================
global_param = None
_worker_root_span = None


# ==============================
# Master 进程初始化
# ==============================
def on_starting(_server):
    global global_param
    # 配置文件路径，可通过环境变量覆盖
    config_file = os.environ.get(
        "DBGPT_CONFIG_FILE", "configs/dbgpt-proxy-openai-hf.toml"
    )

    # 1. 加载配置
    global_param = load_config(config_file)

    # 2. 初始化 tracer（全局对象）
    trace_config = global_param.service.web.trace or global_param.trace
    trace_file = trace_config.file or os.path.join(
        "logs", "dbgpt_webserver_tracer.jsonl"
    )
    initialize_tracer(
        trace_file,
        system_app=system_app,
        root_operation_name=trace_config.root_operation_name or "DB-GPT-Webserver",
        tracer_parameters=trace_config,
    )

    # 3. 初始化应用（master 层全局初始化）
    initialize_app(global_param)
    print("Master process: initialize_app and tracer initialized.")


# ==============================
# Worker 进程初始化
# ==============================
def when_ready(_server):
    global _worker_root_span
    # 每个 worker 启动独立 root span
    _worker_root_span = root_tracer.start_span(
        "DB-GPT-Webserver-worker",
        span_type=SpanType.RUN,
        metadata={
            "run_service": SpanTypeRunName.WEBSERVER,
            "params": _get_dict_from_obj(global_param),
            "sys_infos": _get_dict_from_obj(get_system_info()),
        },
    )
    print(f"Worker {os.getpid()}: root span started.")


def worker_exit(_server, worker):
    global _worker_root_span
    # 关闭 worker root span
    if _worker_root_span:
        _worker_root_span.end()
        print(f"Worker {worker.pid}: root span finished.")
