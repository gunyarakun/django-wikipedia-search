from django.conf.urls.defaults import *
from django.conf import settings
import os

urlpatterns = patterns('',
    (r'^$', 'wikipedia.searcher.views.index'),
    (r'^search/$', 'wikipedia.searcher.views.search'),
    (r'^search/(?P<lang>[^/]+)/(?P<query>[^/]+)/$', 'wikipedia.searcher.views.search'),
    (r'^title/(?P<lang>[^/]+)/(?P<query>[^/]+)/(?P<tpage>\d*)/$', 'wikipedia.searcher.views.search'),
    (r'^body/(?P<lang>[^/]+)/(?P<query>[^/]+)/(?P<bpage>\d*)/$', 'wikipedia.searcher.views.search'),
)

if settings.DEBUG:
  urlpatterns += patterns('',
    (r'^site_media/(?P<path>.*)$', 'django.views.static.serve',
     {'document_root': os.path.dirname(os.path.abspath(__file__)) + '/../resources'}),
  )
