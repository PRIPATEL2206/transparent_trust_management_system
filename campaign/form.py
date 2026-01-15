from decimal import Decimal
from django import forms
from django.core.exceptions import ValidationError
from django.utils.text import slugify
from django.forms import inlineformset_factory

from .models import Scheme, SchemeCategory, SchemeImages, SchemeStatus, Visibility,Request
from account.models import CustomUser



class CommaSeparatedTagsField(forms.CharField):
    """
    Accepts comma-separated tags and returns a clean Python list.
    Empty input -> [].
    """
    def to_python(self, value):
        if not value:
            return []
        if isinstance(value, list):
            return [str(t).strip() for t in value if str(t).strip()]
        parts = [p.strip() for p in str(value).split(",")]
        return [p for p in parts if p]


class MultiFileInput(forms.ClearableFileInput):
        allow_multiple_selected = True

class SchemeForm(forms.ModelForm):
    # Field customizations for UX
    title = forms.CharField(
        max_length=200,
        label="Title",
        widget=forms.TextInput(attrs={"class": "form-control"})
    )
    slug = forms.SlugField(
        max_length=220,
        required=False,  # allow auto-generation from title if blank
        label="Slug",
        help_text="If left blank, it will be generated from the title.",
        widget=forms.TextInput(attrs={"class": "form-control"})
    )
    short_description = forms.CharField(
        max_length=500,
        required=False,
        label="Short description",
        widget=forms.Textarea(attrs={"class": "form-control", "rows": 3})
    )
    description = forms.CharField(
        required=False,
        label="Description",
        widget=forms.Textarea(attrs={"class": "form-control", "rows": 6})
    )
    category = forms.ModelChoiceField(
        queryset=SchemeCategory.objects.all(),
        required=False,
        label="Category",
        widget=forms.Select(attrs={"class": "form-select"})
    )

    tags = CommaSeparatedTagsField(
        required=False,
        label="Tags",
        help_text="Enter comma-separated tags (e.g., health, education, women).",
        widget=forms.TextInput(attrs={"class": "form-control"})
    )

    cover_image = forms.ImageField(
        required=False,
        label="Cover image",
        help_text="Upload a cover image (optional)."
    )

    start_date = forms.DateTimeField(
        label="Start date & time",
        widget=forms.DateTimeInput(attrs={"type": "datetime-local", "class": "form-control"})
    )
    end_date = forms.DateTimeField(
        required=False,
        label="End date & time",
        widget=forms.DateTimeInput(attrs={"type": "datetime-local", "class": "form-control"}),
        help_text="Must be after the start date/time."
    )

    TIMEZONE_CHOICES = [
        ("Asia/Kolkata", "Asia/Kolkata (IST)"),
        ("UTC", "UTC"),
        ("Asia/Dubai", "Asia/Dubai"),
        ("Europe/London", "Europe/London"),
        ("America/New_York", "America/New_York"),
    ]
    timezone_name = forms.ChoiceField(
        choices=TIMEZONE_CHOICES,
        initial="Asia/Kolkata",
        label="Timezone",
        widget=forms.Select(attrs={"class": "form-select"})
    )

    goal_amount = forms.DecimalField(
        required=False,
        max_digits=12,
        decimal_places=2,
        min_value=Decimal("0.00"),
        label="Goal amount",
        widget=forms.NumberInput(attrs={"class": "form-control", "step": "0.01"})
    )
    minimum_donation_amount = forms.DecimalField(
        required=True,
        max_digits=12,
        decimal_places=2,
        min_value=Decimal("0.00"),
        label="Minimum donation amount",
        widget=forms.NumberInput(attrs={"class": "form-control", "step": "0.01"})
    )
    maximum_donation_amount = forms.DecimalField(
        required=False,
        max_digits=12,
        decimal_places=2,
        min_value=Decimal("0.00"),
        label="Maximum donation amount",
        help_text="Optional; must be ≥ minimum if set.",
        widget=forms.NumberInput(attrs={"class": "form-control", "step": "0.01"})
    )



    class Meta:
        model = Scheme
        # Excluding ForeignKey 'request' so you can set it in the view (e.g., from current request/context)
        exclude = ("request",'visibility','status')

    # -----------------------
    # Validations
    # -----------------------
    def clean_slug(self):
        """
        Enforce uniqueness manually to show a friendly error.
        Auto-generate from title if blank.
        """
        slug = self.cleaned_data.get("slug") or slugify(self.cleaned_data.get("title") or "")
        if not slug:
            raise ValidationError("Slug cannot be empty. Please provide a title.")
        qs = Scheme.objects.filter(slug=slug)
        if self.instance.pk:
            qs = qs.exclude(pk=self.instance.pk)
        if qs.exists():
            raise ValidationError("This slug is already in use. Please choose a different slug.")
        return slug

    def clean(self):
        cleaned = super().clean()
        start_date = cleaned.get("start_date")
        end_date = cleaned.get("end_date")
        min_amt = cleaned.get("minimum_donation_amount")
        max_amt = cleaned.get("maximum_donation_amount")

        if start_date and end_date and end_date <= start_date:
            self.add_error("end_date", "End date/time must be after the start date/time.")

        if min_amt is not None and max_amt is not None and max_amt < min_amt:
            self.add_error("maximum_donation_amount",
                           "Maximum donation must be greater than or equal to the minimum donation.")
        return cleaned


    # -----------------------
    # Save
    # -----------------------
    def save(self,user:CustomUser,commit=True):
        """
        Two-phase save to ensure cover_image and gallery images use instance.id in upload_to:
        1) Save instance without the cover image to get a primary key (id).
        2) Assign the cover image and save again.
        3) Create SchemeImages from gallery_bulk (multiple) after instance exists.
        Also ensures tags are stored as a unique list preserving order.
        """
        instance = super().save(commit=False)
        # normalize tags (unique & ordered)
        tags_list = self.cleaned_data.get("tags", [])
        instance.tags = list(dict.fromkeys([str(t) for t in tags_list]))

        if not instance.slug:
            instance.slug = slugify(instance.title)

        instance.cover_image = self.files.get("cover_image")
        instance.request=Request.objects.create(proposed_by=user)

        if commit:
            if not instance.pk:
                instance.save()
            else:
                instance.save()
            for f in self.files.getlist('gallery_bulk'):
                instance.gallery.create(image=f)

            self.save_m2m()

        return instance

