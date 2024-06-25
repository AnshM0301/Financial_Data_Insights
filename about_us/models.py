from django.db import models

class Feedback(models.Model):
    name = models.CharField(max_length=100, blank=True, default='Anonymous')
    feedback = models.TextField()
    rating = models.IntegerField(default=0)
    submitted_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"Feedback from {self.name} - {self.rating} stars"
