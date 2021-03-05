# Ref: https://riptutorial.com/python/example/10954/create-singleton-class-with-a-decorator
def singleton(cls):  # type: ignore
    """Singleton decorator"""
    instance = [None]

    def _wrapper(*args, **kwargs):  # type: ignore
        if instance[0] is None:
            instance[0] = cls(*args, **kwargs)
        return instance[0]

    return _wrapper
