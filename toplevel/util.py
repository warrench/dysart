def start(services):
    for service in services.values():
        service.start()

def stop(services):
    for service in services.values():
        service.stop()

def status(services):
    for service in services.values():
        service.get_status()

def restart():
    stop()
    start()
