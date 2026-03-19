from prometheus_fastapi_instrumentator import Instrumentator
from fastapi import FastAPI

def setup_metrics(app: FastAPI):
    """
    Prometheus metrik toplayıcısını FastAPI uygulamasına bağlar
    ve /metrics endpoint'ini dışa açar.
    """
    instrumentator = Instrumentator(
        should_group_status_codes=False,
        should_ignore_untemplated=True,
        should_respect_env_var=False,
        should_instrument_requests_inprogress=True,
        excluded_handlers=["/metrics"],
        env_var_name="ENABLE_METRICS",
    )
    instrumentator.instrument(app).expose(app, endpoint="/metrics")
