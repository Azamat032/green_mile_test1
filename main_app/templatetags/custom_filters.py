from django import template
from django.templatetags.static import static

register = template.Library()


@register.filter
def lookup(value, key):
    return value.get(key, '') if isinstance(value, dict) else value


@register.filter
def split(value, delimiter):
    return value.split(delimiter)


@register.filter
def get_item(dictionary, key):
    return dictionary.get(key, '')


@register.filter
def get_template_url(template_dict, design):
    template = template_dict.get(design)
    if template and template.background_image:
        return template.background_image.url
    return static(f'images/default-{design}.jpg')
