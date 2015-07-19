from django.db import models
from django.conf import settings

class pyanoroll(models.Model):
	titel_text = models.CharField(max_length=200)
	composer_text = models.CharField(max_length=200)
	roletype_text = models.CharField(max_length=200)
	producer_text = models.CharField(max_length=200)
	playspeed = models.IntegerField()
	roleimage = models.ImageField()
# Create your models here.
