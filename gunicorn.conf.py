import multiprocessing
import os

bind = os.environ.get('GUNICORN_BIND', '0.0.0.0:8000')
workers = int(os.environ.get('WEB_CONCURRENCY', multiprocessing.cpu_count() * 2 + 1))
worker_class = 'gthread'
threads = 2
worker_tmp_dir = '/dev/shm'

timeout = 30
graceful_timeout = 10
keepalive = 5

max_requests = 1000
max_requests_jitter = 50

accesslog = '-'
errorlog = '-'
loglevel = os.environ.get('GUNICORN_LOG_LEVEL', 'info')
access_log_format = '%(h)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s" %(D)s'

preload_app = True

forwarded_allow_ips = os.environ.get('FORWARDED_ALLOW_IPS', '*')
proxy_protocol = False

limit_request_line = 8190
limit_request_fields = 100
limit_request_field_size = 8190


def on_starting(server):
    pass


def post_fork(server, worker):
    server.log.info('Worker spawned (pid: %s)', worker.pid)


def pre_exec(server):
    server.log.info('Forked child, re-executing.')


def when_ready(server):
    server.log.info('Server is ready. Spawning workers')


def worker_int(worker):
    worker.log.info('worker received INT or QUIT signal')


def worker_abort(worker):
    worker.log.info('worker received SIGABRT signal')
