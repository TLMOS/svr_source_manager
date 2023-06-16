proc_name = "svr_sm_api"

workers = 4
max_requests = 1000
timeout = 30
graceful_timeout = 30
keepalive = 2


def pre_request(worker, req):
    req.path = "asdasdasdads"
