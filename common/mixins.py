class TitleMixin:
    """
    Добавляет в контекст title.
    """
    title = None

    def get_context_data(self, *, object_list=None, **kwargs):
        context = super(TitleMixin, self).get_context_data(**kwargs)
        context['title'] = self.title
        return context