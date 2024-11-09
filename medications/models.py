from django.db import models
from django.core.exceptions import ValidationError
from django.utils import timezone

# Main Data Model - the medication
# contains the drug name, generic, as-needed status, dosing regiment


class Medication(models.Model):
    prescription_name = models.CharField(max_length=255)
    generic_name = models.CharField(max_length=255)

    # As needed meds
    as_needed = models.BooleanField(default=False,
                                    help_text="Check if medication is taken only as needed")
    max_daily_doses = models.PositiveIntegerField(null=True, blank=True,
                                                  help_text="max num doses allowed per day")
    dose_period = models.PositiveIntegerField(null=True, blank=True,
                                              help_text="Minimum suggest hours between doses")

    # metainfo
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def clean(self):
        if self.is_as_needed:
            if not self.max_daily_doses:
                raise ValidationError(
                    "Max Daily Doses Required for As-needed meds")
            if not self.dose_period:
                raise ValidationError(
                    "Min time b/w doses required for as-needed medications")
        else:
            if self.max_daily_doses or self.dose_period:
                raise ValidationError("field not required")

    def __str__(self):
        return f"{self.prescription_name} ({'As needed' if self.as_needed else 'Scheduled'})"

# Dosing Units: (e.g., mg, mL, pills/capsules)
class DoseUnit(models.Model):
    name = models.CharField(max_length=50, unique=True)
    symbol = models.CharField(max_length=10)

    def __str__(self):
        return self.symbol

# Scheduling units to be inserted into the larger calendar itself
# e.g. take tacrolimus 7mg at 9am daily.
class MedicationSchedule(models.Model):
    medication = models.ForeignKey(Medication, on_delete=models.CASCADE)
    start_date = models.DateField()
    end_date = models.DateField(null=True, blank=True)
    dose_amount = models.DecimalField(max_digits=8, decimal_places=2)
    dose_unit = models.ForeignKey(DoseUnit, on_delete=models.PROTECT)

    FREQUENCY_TYPES = [
        ('daily', 'Every Day'),
        ('days_interval', 'Every X Days'),
        ('weekly', 'Specific Days of the Week'),
        ('Monthly', 'Specific Days of the Month'),
        ('as_needed', 'As Needed'),
    ]

    frequency_type = models.CharField(max_length=20, choices=FREQUENCY_TYPES)
    days_interval = models.PositiveIntegerField(null=True, blank=True)
    weekly_days = models.CharField(max_length=20, null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)

    def clean(self):
        if self.frequency_type == 'as_needed':
            if not self.medication.as_needed:
                raise ValidationError(
                    'Only as needed meds need the as needed frequency value')
            # clear schedule fields if using as_needed models
            self.days_interval = None
            self.weekly_days = None
        else:
            if self.medication.as_needed:
                raise ValidationError(
                    " As needed medication requires a frequency")

            if self.end_date and self.start_date > self.end_date:
                raise ValidationError("End Date must be after start date")

            if self.frequency_type == 'days_interval' and not self.days_interval:
                raise ValidationError(
                    'Days interval required for this frequency type')

            if self.frequency_type == 'weekly' and not self.weekly_days:
                raise ValidationError(
                    'Days of the week are required for this frequency type')

    def __str__(self):
        return f"{self.medication.prescription_name} - {self.dose_amount}{self.dose_unit.symbol}"

#Accumulation of DoseUnits above for each medication with additional actions to operate on them
#These doseunits will be compiled into a calendar view (Day,Week,Month)
class DoseLog(models.Model):
    medication_schedule = models.ForeignKey(MedicationSchedule, on_delete=models.CASCADE)
    
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('taken', 'Taken'),
        ('missed', 'Missed'),
        ('skipped', 'Skipped'),
    ]
    
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    
    #optional metainfo fields(?)
    scheduled_datetime = models.DateTimeField(null=True, blank=True)
    taken_datetime = models.DateTimeField(null=True, blank=True)
    dose_taken = models.DecimalField(max_digits=8, decimal_places=2)
    
    reason= models.TextField(blank=True, 
                             help_text="Reason for taking as-needed med/skipping doses")
    
    def clean(self):
        if self.medication_schedule.frequency_type =="as_needed":
            if not self.taken_datetime:
                raise ValidationError("Taken Date and Time required for as-needed meds")
            if not self.reason:
                raise ValidationError("Reason required for as-needed medications")
            
            #daily dose limit checks - 
            doses_taken_today = DoseLog.objects.filter(
                medication_schedule=self.medication_schedule,
                taken_datetime__date=self.taken_datetime.date()
            ).count()
            
            if doses_taken_today >= self.medication_schedule.max_daily_doses:
                raise ValidationError("Maximum daily doses exceed, proceed with caution")
            
            # min time b/w doses
            last_dose = DoseLog.objects.filter(
                medication_schedule=self.medication_schedule,
                taken_datetime__lt=self.taken_datetime,
                status='taken'
            ).order_by('-taken_datetime').first()
            
            if last_dose:
                #TODO: MAKE SURE ALL THE TIMEUNITS ARE PROPERLY ALIGNED
                hours_since_last = (self.taken_datetime - last_dose.taken_datetime).total_seconds() / 3600
                if hours_since_last < self.medication_schedule.medication.dose_period:
                    #TODO: calculate how much longer until the next dose is avail.
                    raise ValidationError("Minimum time between doses not yet met.")
        else:
            if not self.schedule_datetime:
                raise ValidationError("Scheduled time required for medicastions")
    def __str__(self):
        schedule = self.medication_schedule
        if schedule.frequency_type == 'as_needed':
            return f"{schedule.medication.prescription_name} - Taken: {self.taken_datetime}"
        return f"{schedule.medication.prescription_name} - Scheduled: {self.scheduled_datetime}"
    
