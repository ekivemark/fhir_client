from django.db import models

# Create your models here.

class Session_State(models.Model):
    state = models.CharField(max_length=40,db_index=True)
    auth  = models.URLField(db_index=True)
    name  = models.CharField(max_length=80, db_index=True)
    code  = models.CharField(max_length=80, null=True, blank=True)

    def __str__(self):
        return self.state
