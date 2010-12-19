from django import template

def string_repeat(string, times):
    return string * times

register = template.Library()
register.simple_tag(string_repeat)
