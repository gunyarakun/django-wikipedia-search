# This is an auto-generated Django model module.
# You'll have to do the following manually to clean this up:
#   * Rearrange models' order
#   * Make sure each model has one field with primary_key=True
# Feel free to rename the models, but don't rename db_table values or field names.
#
# Also note: You'll have to insert the output of 'django-admin.py sqlinitialdata [appname]'
# into your database.

from django.db import models

class Article(models.Model):
  id = models.IntegerField(primary_key=True)
  title = models.CharField(maxlength=765)
#  body = models.TextField()
  author = models.CharField(maxlength=765)
  mdate = models.DateTimeField()
  size = models.IntegerField()
  class Meta:
    get_latest_by = 'mdate'

class JAArticle(models.Model):
  id = models.IntegerField(primary_key=True)
  title = models.CharField(maxlength=765)
#  body = models.TextField()
  author = models.CharField(maxlength=765)
  mdate = models.DateTimeField()
  size = models.IntegerField()
  class Meta:
    db_table = 'articles_ja'
    get_latest_by = 'mdate'

class ENArticle(models.Model):
  id = models.IntegerField(primary_key=True)
  title = models.CharField(maxlength=765)
#  body = models.TextField()
  author = models.CharField(maxlength=765)
  mdate = models.DateTimeField()
  size = models.IntegerField()
  class Meta:
    db_table = 'articles_en'
    get_latest_by = 'mdate'


