"""Derived Unicode search values; public metadata, never candidate records."""


def university_search(context):
    return context.get_current_parameters()['name'].casefold()


def group_search(context):
    fields=context.get_current_parameters()
    return f"{fields['title']} {fields['official_id']}".casefold()
