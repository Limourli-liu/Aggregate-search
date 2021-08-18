config, Manager, log, lock = 0,0,0,0
def _default_config(root, name):
    return {}

# m_init(m_name, config, self, logging.getLogger(f'{name}.{m_name}'))
def _init(m_name, _config, _Manager, _log): #载入时被调用
    global config, Manager, log, lock
    config, Manager, log, lock = _config, _Manager, _log, _Manager.threading_lock
    _log.debug(lock)
    Manager.getMod("crontab").submit(m_name, 3, _crontab)
    pass

def _exit():
    log.debug('exit')
    pass

def _crontab():
    pass