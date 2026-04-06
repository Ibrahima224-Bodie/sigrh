from django.db import migrations


def _unique_programme_code(Programme, filiere_id, base_code, exclude_pk=None):
    base = (base_code or '').strip() or 'PRG'
    base = base[:50]
    candidate = base
    suffix = 1
    qs = Programme.objects.filter(filiere_id=filiere_id)
    if exclude_pk:
        qs = qs.exclude(pk=exclude_pk)
    while qs.filter(code=candidate).exists():
        suffix += 1
        suffix_text = f"-{suffix}"
        candidate = f"{base[:50 - len(suffix_text)]}{suffix_text}"
    return candidate


def forwards(apps, schema_editor):
    Filiere = apps.get_model('enseignants', 'Filiere')
    Programme = apps.get_model('enseignants', 'Programme')
    Affectation = apps.get_model('enseignants', 'Affectation')
    through = Filiere.etablissements.through

    # 1) Backfill initial: legacy FK -> M2M
    for filiere in Filiere.objects.exclude(etablissement_id=None).iterator():
        through.objects.get_or_create(
            filiere_id=filiere.id,
            etablissement_id=filiere.etablissement_id,
        )

    # 2) Merge duplicates into a single shared reference by business signature.
    groups = {}
    for filiere in Filiere.objects.all().order_by('id'):
        key = (
            (filiere.nom or '').strip().lower(),
            (filiere.description or '').strip().lower(),
            filiere.duree_mois or 0,
            filiere.nombre_heures_total or 0,
        )
        groups.setdefault(key, []).append(filiere.id)

    for _, ids in groups.items():
        if len(ids) <= 1:
            continue

        master_id = ids[0]
        duplicate_ids = ids[1:]

        master = Filiere.objects.filter(pk=master_id).first()
        if master is None:
            continue

        for dup_id in duplicate_ids:
            dup = Filiere.objects.filter(pk=dup_id).first()
            if dup is None:
                continue

            # Merge linked etablissements
            for etab_id in through.objects.filter(filiere_id=dup.id).values_list('etablissement_id', flat=True):
                through.objects.get_or_create(filiere_id=master.id, etablissement_id=etab_id)

            # Reattach programmes to master, preserving unique code per filiere
            for programme in Programme.objects.filter(filiere_id=dup.id).order_by('id'):
                programme.code = _unique_programme_code(Programme, master.id, programme.code, exclude_pk=programme.pk)
                programme.filiere_id = master.id
                programme.save(update_fields=['code', 'filiere'])

            # Reattach affectations
            Affectation.objects.filter(filiere_id=dup.id).update(filiere_id=master.id)

            # Keep a coherent legacy FK for compatibility
            if not master.etablissement_id and dup.etablissement_id:
                master.etablissement_id = dup.etablissement_id
                master.save(update_fields=['etablissement'])

            dup.delete()

    # 3) Ensure each filiere keeps a principal etablissement in legacy FK
    for filiere in Filiere.objects.all().order_by('id'):
        first_etab_id = through.objects.filter(filiere_id=filiere.id).values_list('etablissement_id', flat=True).first()
        if first_etab_id and filiere.etablissement_id != first_etab_id:
            filiere.etablissement_id = first_etab_id
            filiere.save(update_fields=['etablissement'])


def backwards(apps, schema_editor):
    Filiere = apps.get_model('enseignants', 'Filiere')
    through = Filiere.etablissements.through

    # Keep the first linked etablissement as legacy FK on rollback.
    for filiere in Filiere.objects.all().order_by('id'):
        first_etab_id = through.objects.filter(filiere_id=filiere.id).values_list('etablissement_id', flat=True).first()
        if first_etab_id:
            filiere.etablissement_id = first_etab_id
            filiere.save(update_fields=['etablissement'])


class Migration(migrations.Migration):

    dependencies = [
        ('enseignants', '0019_alter_filiere_options_alter_filiere_unique_together_and_more'),
    ]

    operations = [
        migrations.RunPython(forwards, backwards),
    ]
