from django.contrib import admin
from .models import Medication, DoseUnit, MedicationSchedule, DoseLog

@admin.register(Medication)
class MedicationAdmin(admin.ModelAdmin):
    list_display = ('name', 'as_needed', 'created_at', 'updated_at')
    list_filter = ('as_needed')
    search_fields = ('name',)
    
@admin.register(DoseUnit)
class DoseUnitAdmin(admin.ModelAdmin):
    list_display = ('name', 'symbol')
    search_fields = ('name', 'symbol')

@admin.register(MedicationSchedule)
class MedicationScheduleAdmin(admin.ModelAdmin):
    list_display = ('medication', 'frequency_type', 'dose_amount', 'dose_unit', 'is_active')
    list_filter = ('frequency', 'is_active')
    search_fields = ('medication__prescription_name', 'medication__generic_name',)
    
@admin.register(DoseLog)
class DoseLogAdmin(admin.ModelAdmin):
    list_display = ('medication_schedule', 'scheduled_datetime', 'taken_datetime', 'status')
    list_filter = ('status', 'taken_datetime')
    search_fields = ('medication_schedule__medication__prescription_name','medication__generic_name',)