from django import template 

register = template.Library()

@register.inclusion_tag("templatetags/form_input_utils.html")
def input_tag(tag,**kargs):
    tag.field.widget.attrs.update(kargs)
    return {
        'tag':tag
    }