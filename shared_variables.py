import threading

user_processing_status = {}
status_lock = threading.Lock()
sse_clients = {} 
