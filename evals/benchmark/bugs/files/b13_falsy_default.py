def retries(cfg):
    # bug: 0 is falsy, so an explicit retries=0 silently becomes 3
    return cfg.get('retries') or 3
