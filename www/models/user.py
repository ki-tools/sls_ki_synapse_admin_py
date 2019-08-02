class User(object):
    def __init__(self, id, email=None):
        self.id = id
        self.email = email
        self.is_active = True
        self.is_authenticated = True
        self.is_anonymous = False

    def get_id(self):
        return self.id
