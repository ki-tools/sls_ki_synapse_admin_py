from www.core import ParamStore


class User(object):
    def __init__(self, id, email=None):
        self.id = id
        self.email = email

    @property
    def is_active(self):
        return True

    @property
    def is_authenticated(self):
        return True

    @property
    def is_anonymous(self):
        return False

    def get_id(self):
        return self.id
