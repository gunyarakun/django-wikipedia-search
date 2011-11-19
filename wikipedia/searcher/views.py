# -*- coding: utf-8 -*-
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render_to_response
from django.template import RequestContext
from wikipedia.searcher.models import JAArticle, ENArticle
from django.core.paginator import ObjectPaginator, InvalidPage
import re
import _mysql

PAGE_ELEMENTS = 10
word_regex = re.compile('^(\+|\-|<|>|\(|\)|~|\*|\")?(?P<word>.*?)(\)|\*|\")?$')
# FIXME: LANG and langs should be one object
LANG = ('ja', 'en')
langs = [{ 'value': 'ja', 'show': '日本語版'}, { 'value': 'en', 'show': '英語版'}]

def index(request):
  return render_to_response('index.html', { 'langs': langs })

def redirect(lang, query):
  import urllib
  return HttpResponseRedirect('/search/' + urllib.quote(lang) + '/' + urllib.quote(query) + '/')

def paginate(obj, page):
  p = ObjectPaginator(
    obj,
    PAGE_ELEMENTS
  )
  try:
    obj_list = p.get_page(page - 1)
  except InvalidPage:
    obj_list = []
  return (obj_list, p)

def search(request, query = None, lang = None, tpage = 0, bpage = 0):
  if not (query and lang):
    query = request.POST.get('q')
    lang = request.POST.get('lang')
    if query and lang:
      return redirect(lang, query)
    else:
      return HttpResponseRedirect('/')

  # check lang
  if not lang in LANG:
    return HttpResponseRedirect('/')

  # default operator is and
  senna_query = '*D+ ' + query

  # get words for snippet highlight
  query = re.sub('　', ' ', query)
  query_words = query.split()
  query_words = [word_regex.match(w).group('word') for w in query_words if w not in ('OR',)]
  if len(query_words) == 0:
    return HttpResponseRedirect('/')
  snippet_args = ', '.join(["'%s', '<span class=\"hl\">', '</span>'" % _mysql.escape_string(w)
                            for w in query_words])

  try:
    tpage = o_tpage = int(tpage)
    bpage = o_bpage = int(bpage)
  except ValueError:
    return redirect(lang, query)

  if lang == 'ja':
    a = JAArticle
  elif lang == 'en':
    a = ENArticle

  if tpage > 0 or bpage == 0:
    if tpage == 0: o_tpage = 1
    (t, tp) = paginate(a.objects.filter(title__search = senna_query), o_tpage)
  else:
    (t, tp) = ([], None)

  if tpage == 0 or bpage > 0:
    if bpage == 0: o_bpage = 1
#    b = Article.objects.filter(body__search = senna_query)
    b = a.objects.all().extra(
      select={
        'snip': "snippet(body, 512, 3, 'utf8', 1, '...', '...<br>', %s)" % snippet_args
      },
      where=[
        "MATCH(body) AGAINST('%s' IN BOOLEAN MODE)" % _mysql.escape_string(senna_query)
      ],
      # TODO: use params
    )
    (b, bp) = paginate(b, o_bpage)
  else:
    (b, bp) = ([], None)

  return render_to_response('results.html',
    {'query': query, 'lang': lang, 'langs': langs,
     'titles': t, 'title_paginator': tp, 'title_page': o_tpage,
     'bodys' : b, 'body_paginator' : bp, 'body_page' : o_bpage, },
    context_instance = RequestContext(request))
