from django.db import models
from django.utils.timezone import now


# Create your models here.

class Session_State(models.Model):
    state = models.CharField(max_length=40,db_index=True)
    auth  = models.URLField(db_index=True)
    name  = models.CharField(max_length=80, db_index=True)
    code  = models.CharField(max_length=80, null=True, blank=True)
    atoken = models.CharField(max_length=40, null=True, blank=True)
    expires = models.DateTimeField(auto_now=False, null=True)
    rtoken = models.CharField(max_length=40, null=True, blank=True)

    def __str__(self):
        return self.state

    def is_expired(self):
        if now() >= self.expires:
            return True
        else:
            return False
