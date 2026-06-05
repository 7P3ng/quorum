def save(record, db):
    try:
        db.write(record)
    except IOError as exc:
        logging.error('write failed: %s', exc)
        raise
