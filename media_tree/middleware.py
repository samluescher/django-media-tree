from django.conf import settings

class SessionPostMiddleware(object):
    
    def process_request(self, request):
        if not request.COOKIES.has_key(settings.SESSION_COOKIE_NAME) and request.POST.has_key(settings.SESSION_COOKIE_NAME):
            request.COOKIES[settings.SESSION_COOKIE_NAME] = request.POST[settings.SESSION_COOKIE_NAME]