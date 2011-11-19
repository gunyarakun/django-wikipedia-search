from django import template

register = template.Library()

# Origin : http://code.djangoproject.com/wiki/PaginatorTag
@register.inclusion_tag('pager.html')
def pager(paginator, action, lang, query, page, adjacent_pages = 4):
#  try:
#    tag_name, paginator, action, adjacent_pages = token.split_contents()
#  except ValueError:
#    raise template.TemplateSyntaxError, \
#      "%r tag requires three arguments" % token.contents[0]

  page_numbers = [n for n in \
                  range(page - adjacent_pages, page + adjacent_pages + 1) \
                  if n > 0 and n <= paginator.pages]
  return {
    "action": action,
    "lang": lang,
    "query": query,
    "hits": paginator.hits,
    "results_per_page": paginator.num_per_page,
    "page": page,
    "pages": paginator.pages,
    "page_numbers": page_numbers,
    "next": page + 1,
    "previous": page - 1,
    "has_next": paginator.has_next_page(page - 1),
    "has_previous": paginator.has_previous_page(page - 1),
    "show_first": 1 not in page_numbers,
    "show_last": paginator.pages not in page_numbers,
  }
