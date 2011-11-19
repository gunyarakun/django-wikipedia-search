def sql(request):
  from django.db import connection
  return { 'sql_queries': connection.queries }
