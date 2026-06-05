def retries(cfg):
    return cfg.get('retries', 3)   # honors an explicit 0
