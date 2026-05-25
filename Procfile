web: gunicorn a_core.wsgi:application --bind 0.0.0.0:$PORT --workers 3
websocket: daphne a_core.asgi:application --bind 0.0.0.0 --port $WS_PORT
