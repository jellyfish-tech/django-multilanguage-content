from django.db import models

from django_multilanguage_content import to_translation


class Diff(models.Model):
    name = models.CharField(max_length=20)
    age = models.IntegerField()
    status = models.CharField(max_length=30)


@to_translation('name', 'status')
class Simple(models.Model):
    name = models.CharField(max_length=20)
    age = models.IntegerField()
    status = models.CharField(max_length=30)
