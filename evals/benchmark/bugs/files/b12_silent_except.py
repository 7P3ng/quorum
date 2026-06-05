def save(record, db):
    try:
        db.write(record)
    except Exception:
        pass
