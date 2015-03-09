from django.db import models


# Create your models here.

class Reports(models.Model):
    Report_title = models.CharField(max_length=255)
    pub_date = models.DateTimeField('date created')
