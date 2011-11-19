from django.conf import settings
from django.db import connection

class DBDebugMiddleware:
    """
    "DBDebug" middleware for debug out O/R Mapper's SQL:
    """

    def process_response(self, request, response):
        if settings.DEBUG :
            for query in connection.queries:
                print "cost: %s \n sql:%s" % (query['time'], query['sql'])
        return response
