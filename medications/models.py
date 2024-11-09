from django.db import models
from django.core.exceptions import ValidationError
from django.utils import timezone

# Main Data Model - the medication
# contains the drug name, generic, as-needed status, dosing regiment
class Medication(models.Model):
    brand_name = models.CharField(max_length=255)
    generic_name = models.CharField(max_length=255)
    as_needed = models.BooleanField(default=False,
                                    help_text="Check if medication is taken only as needed")
    
    
    pass