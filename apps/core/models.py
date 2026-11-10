from django.db import models

# Create your models here.

class Barangay(models.Model):
    barangay_id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=50)
    city = models.CharField(max_length=50)
    province = models.CharField(max_length=50)

    class Meta:
        db_table = 'barangay'

    def __str__(self):
        return self.name

class Sitio(models.Model):
    sitio_id = models.AutoField(primary_key=True)
    barangay = models.ForeignKey(Barangay, on_delete=models.CASCADE, related_name='sitios', db_column='barangay_id')
    name = models.CharField(max_length=50)

    class Meta:
        db_table = 'sitio'

    def __str__(self):
            return self.name