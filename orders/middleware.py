from django.http import HttpResponseForbidden
from django.shortcuts import render


class Custom403Middleware:
    """
    Кастомное middleware для обработки ответа 403 (доступ запрещен).
    Если в процессе обработки запроса возвращается HttpResponseForbidden,
    middleware перехватывает ответ и отображает кастомный шаблон.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)

        # Проверка, является ли ответ экземпляром HttpResponseForbidden
        if isinstance(response, HttpResponseForbidden):
            message = response.content.decode('utf-8')  # Получение текста сообщения из ответа
            context = {'message': message, 'title': '403 Forbidden'}

            return render(
                request,
                'base/403_custom.html',
                status=403,
                context=context
            )

        # Если не 403, вернуть исходный ответ
        return response
