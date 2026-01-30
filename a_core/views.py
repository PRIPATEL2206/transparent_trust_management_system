# app/views.py
from django.urls import reverse_lazy, reverse
from django.views.generic.edit import FormView
from django.views.generic.detail import SingleObjectMixin
from django.http import Http404

class CreateOrUpdateView(SingleObjectMixin, FormView):
    """
    One view that supports:
      - Create when there's no pk/slug in the URL
      - Update when pk/slug is present
    """
    model = None             # set in subclass
    form_class = None        # or set `fields = "__all__"`
    fields = None            # if not using form_class
    template_name = None     # your custom template path
    success_url = None       # or override get_success_url()

    slug_field = "slug"
    slug_url_kwarg = "slug"
    pk_url_kwarg = "pk"

    def dispatch(self, request, *args, **kwargs):
        self.object = self.get_object_or_none()
        return super().dispatch(request, *args, **kwargs)

    # Allow missing pk/slug → create mode
    def get_object_or_none(self, queryset=None):
        queryset = queryset or self.get_queryset()
        pk = self.kwargs.get(self.pk_url_kwarg)
        slug = self.kwargs.get(self.slug_url_kwarg)

        if pk is None and slug is None:
            return None  # Create mode
        # Update mode
        try:
            return super().get_object(queryset=queryset)
        except Http404:
            raise  # bubble up 404 for invalid pk/slug

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["instance"] = self.object  # None for create, instance for update
        return kwargs

    def form_valid(self, form):
        self.object = form.save(self.request.user)
        return super().form_valid(form)

    def get_success_url(self):
        return self.request.META.get('HTTP_REFERER') or self.request.path