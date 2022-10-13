def json_default(value):
    import datetime
    if isinstance(value, datetime.datetime):
        return dict(year=value.year, month=value.month, day=value.day, hour=value.hour, minute=value.minute)
    elif isinstance(value, datetime.date):
        return dict(year=value.year, month=value.month, day=value.day)
    else:
        return value.__dict__


def to_rid(txt):
    if txt == '':
        return ''
    s = txt.lower()
    x = s.replace(' ', '_').replace("'", '').replace('é', 'e') \
        .replace('è', 'e').replace('ë', 'e').replace('â', 'a') \
        .replace('ô', 'o').replace('"', '').replace('ï', 'i') \
        .replace('à', 'a').replace('-', '').replace('ö', 'oe') \
        .replace('ä', 'ae').replace('ü', 'ue').replace('ß', 'ss').replace('ç', 'c')
    return f'_{x.lower()}'
