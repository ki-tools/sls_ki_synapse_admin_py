class Cookies:
    USER_EMAIL = 'user_email'

    @classmethod
    def user_email_get(cls, request):
        return request.cookies.get(cls.USER_EMAIL, None)

    @classmethod
    def user_email_set(cls, response, email):
        response.set_cookie(cls.USER_EMAIL, email)

    @classmethod
    def user_email_delete(cls, response):
        response.delete_cookie(cls.USER_EMAIL)
