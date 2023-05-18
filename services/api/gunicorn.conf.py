import multiprocessing

proc_name = "svr_core_api"

workers = multiprocessing.cpu_count() * 2 + 1
max_requests = 1000
timeout = 30
graceful_timeout = 30
keepalive = 2
