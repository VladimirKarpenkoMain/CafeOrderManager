from django.db import models

class Revenue(models.Model):

    amount = models.DecimalField(max_digits=12, decimal_places=2)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'Revenue(amount="{self.amount}", created_at={self.created_at})'