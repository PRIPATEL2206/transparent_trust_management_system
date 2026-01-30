from decimal import Decimal
from django import forms
from django.core.exceptions import ValidationError
from django.utils.text import slugify
from django.forms import inlineformset_factory

from .models import Campaign, CampaignCategory, CampaignImages, Visibility
from request_app.models import Request,RequestStatus
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

class CampaignForm(forms.ModelForm):
    # Field customizations for UX
    title = forms.CharField(max_length=200,)
    slug = forms.SlugField(max_length=220,required=False)
    short_description = forms.CharField(max_length=500,)  
    description = forms.CharField()
    category = forms.ModelChoiceField(queryset=CampaignCategory.objects.all(),)
    tags = CommaSeparatedTagsField()
    cover_image = forms.ImageField(required=False)
    start_date = forms.DateTimeField()   
    end_date = forms.DateTimeField()

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
    )

    goal_amount = forms.DecimalField(
        decimal_places=2,
        min_value=Decimal("0.00"),
    )
    minimum_donation_amount = forms.DecimalField(
        required=True,
        decimal_places=2,
        min_value=Decimal("0.00"),
    )
    maximum_donation_amount = forms.DecimalField(
        decimal_places=2,
        min_value=Decimal("0.00"),
    )



    class Meta:
        model = Campaign
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
        qs = Campaign.objects.filter(slug=slug)
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
        3) Create CampaignImages from gallery_bulk (multiple) after instance exists.
        Also ensures tags are stored as a unique list preserving order.
        """
        instance = super().save(commit=False)
        # normalize tags (unique & ordered)
        tags_list = self.cleaned_data.get("tags", [])
        instance.tags = list(dict.fromkeys([str(t) for t in tags_list]))

        if not instance.slug:
            instance.slug = slugify(instance.title)
        instance.cover_image = self.cleaned_data.get("cover_image") or self.files.get("cover_image")
        instance.request=Request.objects.create(proposed_by=user)
        if commit:
            if instance.request.status==RequestStatus.DRAFT:
                # print("instance.id",instance.id)
                instance.save()
            else:
                raise Exception("Campaign request is not in draft status")

            for f in self.files.getlist('gallery_bulk'):
                instance.gallery.create(image=f)

            self.save_m2m()

        return instance

