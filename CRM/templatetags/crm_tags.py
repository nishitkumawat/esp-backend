from django import template
from django.utils.timesince import timesince

register = template.Library()


@register.filter
def status_badge(status):
    """Return Bootstrap badge class for lead status."""
    mapping = {
        'new': 'primary',
        'to_quote': 'info',
        'quote_sent': 'warning',
        'future_lead': 'secondary',
        'deal_closed': 'success',
        'not_useful': 'danger',
    }
    return mapping.get(status, 'secondary')


@register.filter
def status_label(status):
    """Return human-readable label for lead status."""
    mapping = {
        'new': 'New',
        'to_quote': 'To Quote',
        'quote_sent': 'Quote Sent',
        'future_lead': 'Future Lead',
        'deal_closed': 'Deal Closed',
        'not_useful': 'Not Useful',
    }
    return mapping.get(status, status)


@register.filter
def category_label(category):
    """Return human-readable label for lead category."""
    mapping = {
        'solar_structure': 'Solar Structure',
        'roll_forming_machine': 'Roll Forming Machine',
    }
    return mapping.get(category, category)


@register.filter
def time_ago(value):
    """Return '5 minutes ago' style string."""
    if value:
        return timesince(value) + ' ago'
    return ''


@register.filter
def direction_icon(direction):
    """Return arrow icon for message direction."""
    if direction == 'incoming':
        return '←'
    return '→'
