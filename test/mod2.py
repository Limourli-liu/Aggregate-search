config, Manager, log, lock = 0,0,0,0
def _default_config(root, name):
    return {}

# m_init(m_name, config, self, logging.getLogger(f'{name}.{m_name}'))
def _init(m_name, _config, _Manager, _log): #载入时被调用
    global config, Manager, log, lock
    config, Manager, log, lock = _config, _Manager, _log, _Manager.threading_lock
    Manager.getMod("crontab").submit(m_name, 1, _crontab)
    pass

def _exit():
    a = 1/0
    pass

def _crontab():
    log.debug('crontab')
    pass

def _test():
    log.debug('_test')
    return 2