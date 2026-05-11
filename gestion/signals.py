from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from .models import Inscripcion


@receiver(post_save, sender=Inscripcion)
def actualizar_plazas_al_inscribir(sender, instance, created, **kwargs):
    """
    Signal handler: decrements available slots when a new Inscripcion is created.
    Uses max(0, ...) to prevent plazas_disponibles from going negative.
    """
    if created:
        actividad = instance.actividad
        actividad.plazas_disponibles = max(0, actividad.plazas_disponibles - 1)
        actividad.save(update_fields=['plazas_disponibles'])


@receiver(post_delete, sender=Inscripcion)
def restaurar_plazas_al_cancelar(sender, instance, **kwargs):
    """
    Signal handler: increments available slots when an Inscripcion is deleted.
    Restores the slot to the activity.
    """
    actividad = instance.actividad
    actividad.plazas_disponibles += 1
    actividad.save(update_fields=['plazas_disponibles'])
