from django.db import models

# Create your models here.
class MedicalCase(models.Model):  
    patient_id = models.CharField(max_length=100, unique=True)  
    # created_date = models.DateTimeField(auto_now_add=True,null=True)
    status = models.BooleanField(default=False)
    # jaw = models.CharField(max_length=255, verbose_name="牙齿类型", default='') 
    model_path = models.CharField(max_length=255,  default='') 
    label_path = models.CharField(max_length=255, default='')
  
    def __str__(self):  
        return f"Case ID: {self.patient_id}, Processed: {self.status}"  