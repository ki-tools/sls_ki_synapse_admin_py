class User(object):
    def __init__(self, id, email=None):
        self.id = id
        self.email = email
        # This should always be True.
        self.is_active = True
        self.is_authenticated = True

    def get_id(self):
        return self.id
