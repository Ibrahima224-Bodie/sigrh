class AdjustablePaginationMixin:
    page_size_param = 'per_page'
    page_size_options = [50, 100, 150, 200, 250, 300, 350, 400, 450, 500]
    default_page_size = 50

    def get_paginate_by(self, queryset):
        raw_value = self.request.GET.get(self.page_size_param)
        if raw_value:
            try:
                value = int(raw_value)
                if value in self.page_size_options:
                    return value
            except (TypeError, ValueError):
                pass

        configured = getattr(self, 'paginate_by', None)
        if configured in self.page_size_options:
            return configured
        return self.default_page_size

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        current_page_size = self.get_paginate_by(self.object_list)
        current_page = context.get('page_obj')

        context['page_size_options'] = self.page_size_options
        context['current_page_size'] = current_page_size
        context['row_start'] = ((current_page.number - 1) * current_page_size) if current_page else 0
        return context
