
config, db, log, lock = 0,0,0,0
def _default_config(root, name):
    return {}

def _init(_config, _db, _log, _lock, m_name): #载入时被调用
    global config, db, log, lock
    config, db, log, lock = _config, _db, _log, _lock
    pass

def _exit():
    pass

def _crontab():
    pass

def _test():
    log.debug('_test')
    return 2