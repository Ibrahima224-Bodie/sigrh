import csv
from datetime import datetime
import unicodedata
import json

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth import get_user_model
from django.http import HttpResponse, HttpResponseForbidden, JsonResponse
from django.shortcuts import render, get_object_or_404, redirect
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse, reverse_lazy
from django.db import IntegrityError
from django.db import transaction
from django.db.models import Q, Prefetch
from django.db.models.functions import Lower
from config.pagination import AdjustablePaginationMixin
from apps.comptes.permissions import PermissionRequiredMixin, EnseignantsWriteRequiredMixin, any_permission_required, user_has_any_model_permission
from .models import (
    Etablissement,
    Filiere,
    Programme,
    Module,
    Professeur,
    Affectation,
    Region,
    Prefecture,
    Commune,
    Quartier,
    Secteur,
)
from .forms import (
    EtablissementForm, FiliereForm, ProgrammeForm, ModuleForm,
    ProfesseurForm, AffectationForm, RegionForm, PrefectureForm,
    CommuneForm, QuartierForm, SecteurForm
)

User = get_user_model()


def _build_professeur_username(professeur):
    if professeur.email:
        base = professeur.email.split('@')[0].strip().lower()
    elif professeur.matricule:
        base = professeur.matricule.strip().lower()
    else:
        base = f"{(professeur.prenom or '').strip()}.{(professeur.nom or '').strip()}".strip('.').lower()

    base = base or "professeur"
    username = base
    suffix = 1
    while User.objects.filter(username__iexact=username).exists():
        suffix += 1
        username = f"{base}{suffix}"
    return username


def _initial_professeur_password(professeur):
    if professeur.matricule:
        return professeur.matricule.strip()
    if professeur.telephone and len(professeur.telephone.strip()) >= 4:
        return f"Prof@{professeur.telephone.strip()[-4:]}"
    return "Prof@12345"


def _ensure_user_for_professeur(professeur):
    existing_user = None
    if professeur.email:
        existing_user = User.objects.filter(email__iexact=professeur.email).first()

    if not existing_user and professeur.matricule:
        existing_user = User.objects.filter(username__iexact=professeur.matricule).first()

    if existing_user:
        existing_user.first_name = professeur.prenom or ""
        existing_user.last_name = professeur.nom or ""
        existing_user.role = 'professeur'
        existing_user.is_active = bool(professeur.actif)
        if professeur.email:
            existing_user.email = professeur.email
        existing_user.save()
        return existing_user, False, None

    username = _build_professeur_username(professeur)
    password = _initial_professeur_password(professeur)
    user = User(
        username=username,
        first_name=professeur.prenom or "",
        last_name=professeur.nom or "",
        email=professeur.email or "",
        role='professeur',
        is_active=bool(professeur.actif),
    )
    user.set_password(password)
    user.save()
    return user, True, password


def _split_full_name(full_name):
    parts = [p for p in (full_name or '').strip().split() if p]
    if not parts:
        return '', ''
    if len(parts) == 1:
        return parts[0], ''
    return parts[0], ' '.join(parts[1:])


def _normalize_username(value):
    normalized = unicodedata.normalize('NFKD', value or '')
    cleaned = ''.join(ch for ch in normalized if ch.isascii() and (ch.isalnum() or ch in '._-')).lower()
    return cleaned.strip('._-')


def _build_directeur_username(etablissement):
    if etablissement.email:
        base = _normalize_username(etablissement.email.split('@')[0])
    else:
        base = _normalize_username((etablissement.directeur or '').replace(' ', '.'))

    base = base or 'directeur'
    username = base
    suffix = 1
    while User.objects.filter(username__iexact=username).exists():
        suffix += 1
        username = f"{base}{suffix}"
    return username


def _initial_directeur_password(etablissement):
    contact = ''.join(ch for ch in (etablissement.contact or '') if ch.isdigit())
    if len(contact) >= 4:
        return f"Dir@{contact[-4:]}"
    return "Directeur@12345"


def _ensure_user_for_directeur(etablissement):
    directeur_nom = (etablissement.directeur or '').strip()
    if not directeur_nom:
        return None, False, None

    first_name, last_name = _split_full_name(directeur_nom)
    existing_user = None

    if etablissement.email:
        existing_user = User.objects.filter(email__iexact=etablissement.email).first()

    if not existing_user and first_name:
        qs = User.objects.filter(first_name__iexact=first_name)
        if last_name:
            qs = qs.filter(last_name__iexact=last_name)
        existing_user = qs.first()

    if existing_user:
        existing_user.first_name = first_name
        existing_user.last_name = last_name
        existing_user.role = 'directeur_ecole'
        existing_user.is_active = True
        if etablissement.email:
            existing_user.email = etablissement.email
        existing_user.save()
        return existing_user, False, None

    username = _build_directeur_username(etablissement)
    password = _initial_directeur_password(etablissement)
    user = User(
        username=username,
        first_name=first_name,
        last_name=last_name,
        email=etablissement.email or '',
        role='directeur_ecole',
        is_active=True,
    )
    user.set_password(password)
    user.save()
    return user, True, password


class GenericEntityContextMixin:
    entity_label = ''
    entity_label_plural = ''
    list_url_name = ''

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['entity_label'] = self.entity_label
        context['entity_label_plural'] = self.entity_label_plural
        context['list_url_name'] = self.list_url_name
        return context


def add_model_permission_flags(context, request, model):
    app_label = model._meta.app_label
    model_name = model._meta.model_name
    can_view = request.user.has_perm(f'{app_label}.view_{model_name}')
    can_add = request.user.has_perm(f'{app_label}.add_{model_name}')
    can_change = request.user.has_perm(f'{app_label}.change_{model_name}')
    can_delete = request.user.has_perm(f'{app_label}.delete_{model_name}')
    context.update({
        'can_view': can_view,
        'can_add': can_add,
        'can_change': can_change,
        'can_delete': can_delete,
        'can_export_template': False,
        'can_export_data': False,
        'can_export': False,
        'can_import': False,
    })
    csv_entity = context.get('csv_entity')
    if csv_entity and csv_entity in ENTITY_CSV_PERMS:
        csv_perm = ENTITY_CSV_PERMS[csv_entity]
        has_csv = request.user.has_perm(csv_perm)
        context['can_export_template'] = has_csv and can_view
        context['can_export_data'] = has_csv and can_view
        context['can_export'] = has_csv and can_view
        context['can_import'] = has_csv and (can_add or can_change)
    return context


def _resolve_besoin_programme(module, etablissement_id=None, filiere_id=None):
    programmes = module.programmes_principaux.select_related('filiere', 'filiere__etablissement').prefetch_related('filiere__etablissements')
    if filiere_id:
        programme = programmes.filter(filiere_id=filiere_id).first()
    elif etablissement_id:
        programme = programmes.filter(
            Q(filiere__etablissements__id=etablissement_id) | Q(filiere__etablissement_id=etablissement_id)
        ).first()
    else:
        programme = programmes.first()
    filiere = programme.filiere if programme else None
    etablissement = filiere.get_primary_etablissement() if filiere else None
    return programme, filiere, etablissement


def _get_need_affectations(module, etablissement_id=None, filiere_id=None, exclude_affectation_id=None):
    queryset = module.affectations.filter(actif=True).select_related('professeur', 'etablissement', 'filiere')
    if exclude_affectation_id:
        queryset = queryset.exclude(pk=exclude_affectation_id)
    if etablissement_id:
        queryset = queryset.filter(etablissement_id=etablissement_id)
    if filiere_id:
        queryset = queryset.filter(filiere_id=filiere_id)
    return queryset


def _get_professeur_capacity_snapshot(professeur, exclude_affectation_id=None):
    affectations = professeur.affectations.filter(actif=True)
    if exclude_affectation_id:
        affectations = affectations.exclude(pk=exclude_affectation_id)
    heures_utilisees = sum(affectation.heures_affectees for affectation in affectations)
    heures_affectees = professeur.heures_affectees or 0
    heures_restantes = max(heures_affectees - heures_utilisees, 0)
    return {
        'heures_disponibles': heures_affectees,
        'heures_affectees': heures_affectees,
        'heures_utilisees': heures_utilisees,
        'heures_restantes': heures_restantes,
    }


def _has_specialite_match(professeur, module):
    specialite_tokens = {token for token in (professeur.specialite or '').lower().replace('-', ' ').split() if len(token) > 3}
    module_tokens = {token for token in (module.nom or '').lower().replace('-', ' ').split() if len(token) > 3}
    return bool(specialite_tokens.intersection(module_tokens))


def _build_professeur_suggestions(module, etablissement=None, filiere=None, besoin_heures=0, exclude_affectation_id=None, limit=None):
    candidats = Professeur.objects.filter(actif=True).select_related('etablissement').order_by('nom', 'prenom')
    suggestions = []

    for professeur in candidats:
        snapshot = _get_professeur_capacity_snapshot(professeur, exclude_affectation_id=exclude_affectation_id)
        if snapshot['heures_restantes'] <= 0:
            continue

        deja_sur_besoin = Affectation.objects.filter(
            actif=True,
            professeur=professeur,
            module=module,
            etablissement=etablissement,
            filiere=filiere,
        )
        if exclude_affectation_id:
            deja_sur_besoin = deja_sur_besoin.exclude(pk=exclude_affectation_id)

        meme_etablissement = bool(etablissement and professeur.etablissement_id == etablissement.id)
        specialite_match = _has_specialite_match(professeur, module)
        if not specialite_match:
            continue
        heures_proposees = min(snapshot['heures_restantes'], max(besoin_heures, 0)) if besoin_heures else snapshot['heures_restantes']
        query_string = (
            f"?professeur={professeur.pk}&etablissement={etablissement.pk if etablissement else ''}"
            f"&filiere={filiere.pk if filiere else ''}&module={module.pk}"
            f"&heures_affectees={heures_proposees}"
        )
        suggestions.append({
            'professeur': professeur,
            'heures_restantes': snapshot['heures_restantes'],
            'heures_affectees_total': snapshot['heures_affectees'],
            'heures_proposees': heures_proposees,
            'meme_etablissement': meme_etablissement,
            'specialite_match': specialite_match,
            'deja_sur_besoin': deja_sur_besoin.exists(),
            'create_affectation_url': f"{reverse('enseignants:affectation_create')}{query_string}",
        })

    suggestions.sort(
        key=lambda item: (
            item['heures_proposees'],
            item['specialite_match'],
            item['meme_etablissement'],
            0 if item['deja_sur_besoin'] else 1,
            item['professeur'].nom.lower(),
            item['professeur'].prenom.lower(),
        ),
        reverse=True,
    )
    if limit is not None:
        return suggestions[:limit]
    return suggestions


def _build_besoin_row(module, etablissement_id=None, filiere_id=None, exclude_affectation_id=None, include_suggestions=False):
    programme, filiere, etablissement = _resolve_besoin_programme(module, etablissement_id=etablissement_id, filiere_id=filiere_id)
    if filiere_id and filiere is None:
        filiere = Filiere.objects.select_related('etablissement').prefetch_related('etablissements').filter(pk=filiere_id).first()
        etablissement = filiere.get_primary_etablissement() if filiere else etablissement
    if etablissement_id and etablissement is None:
        etablissement = Etablissement.objects.filter(pk=etablissement_id).first()

    actifs_qs = _get_need_affectations(
        module,
        etablissement_id=etablissement.id if etablissement else etablissement_id,
        filiere_id=filiere.id if filiere else filiere_id,
        exclude_affectation_id=exclude_affectation_id,
    )
    heures_couvertes = sum(affectation.heures_affectees for affectation in actifs_qs)
    professeurs_existants = actifs_qs.values('professeur_id').distinct().count()
    requis = module.nombre_heures
    besoins = max(requis - heures_couvertes, 0)

    if besoins == 0:
        etat = 'COUVERT'
    elif heures_couvertes == 0:
        etat = 'CRITIQUE'
    else:
        etat = 'PARTIEL'

    suggestions = []
    if include_suggestions:
        suggestions = _build_professeur_suggestions(
            module,
            etablissement=etablissement,
            filiere=filiere,
            besoin_heures=besoins,
            exclude_affectation_id=exclude_affectation_id,
            limit=3,
        )

    suggestion_url = reverse('enseignants:besoin_suggestions', kwargs={'module_id': module.pk})
    query_params = []
    if etablissement:
        query_params.append(f"etablissement={etablissement.pk}")
    if filiere:
        query_params.append(f"filiere={filiere.pk}")
    if query_params:
        suggestion_url = f"{suggestion_url}?{'&'.join(query_params)}"

    return {
        'etablissement': etablissement,
        'filiere': filiere,
        'programme': programme,
        'module': module,
        'duree': module.nombre_heures,
        'requis': requis,
        'existant': heures_couvertes,
        'besoins': besoins,
        'souhait': besoins,
        'profil_souhaite': f"Spécialité liée à {module.nom}",
        'etat': etat,
        'professeurs_existants': professeurs_existants,
        'professeurs_mobilisables': suggestions,
        'suggestion_url': suggestion_url,
    }


def _forbid_if_no_model_permission(user, model, actions, message):
    if user_has_any_model_permission(user, model, actions):
        return None
    return HttpResponseForbidden(message)


# ============= REFERENTIELS ADMIN =============

class RegionListView(LoginRequiredMixin, PermissionRequiredMixin, AdjustablePaginationMixin, ListView):
    model = Region
    model_permission_model = Region
    required_action = 'view'
    template_name = 'enseignants/generic_list.html'
    context_object_name = 'items'
    paginate_by = 20

    def get_queryset(self):
        queryset = Region.objects.all()
        search = self.request.GET.get('search')
        if search:
            queryset = queryset.filter(nom__icontains=search)
        return queryset.order_by('nom')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            'search': self.request.GET.get('search', ''),
            'entity_label': 'Region',
            'entity_label_plural': 'Regions',
            'create_url_name': 'enseignants:region_create',
            'update_url_name': 'enseignants:region_update',
            'delete_url_name': 'enseignants:region_delete',
            'csv_entity': 'regions',
        })
        return add_model_permission_flags(context, self.request, Region)


class RegionCreateView(LoginRequiredMixin, EnseignantsWriteRequiredMixin, GenericEntityContextMixin, CreateView):
    model = Region
    form_class = RegionForm
    template_name = 'enseignants/generic_form.html'
    success_url = reverse_lazy('enseignants:region_list')
    entity_label = 'Region'
    entity_label_plural = 'Regions'
    list_url_name = 'enseignants:region_list'


class RegionUpdateView(LoginRequiredMixin, EnseignantsWriteRequiredMixin, GenericEntityContextMixin, UpdateView):
    model = Region
    form_class = RegionForm
    template_name = 'enseignants/generic_form.html'
    success_url = reverse_lazy('enseignants:region_list')
    entity_label = 'Region'
    entity_label_plural = 'Regions'
    list_url_name = 'enseignants:region_list'


class RegionDeleteView(LoginRequiredMixin, EnseignantsWriteRequiredMixin, GenericEntityContextMixin, DeleteView):
    model = Region
    template_name = 'enseignants/generic_confirm_delete.html'
    success_url = reverse_lazy('enseignants:region_list')
    entity_label = 'Region'
    entity_label_plural = 'Regions'
    list_url_name = 'enseignants:region_list'


class PrefectureListView(LoginRequiredMixin, PermissionRequiredMixin, AdjustablePaginationMixin, ListView):
    model = Prefecture
    model_permission_model = Prefecture
    required_action = 'view'
    template_name = 'enseignants/generic_list.html'
    context_object_name = 'items'
    paginate_by = 20

    def get_queryset(self):
        queryset = Prefecture.objects.select_related('region').all()
        search = self.request.GET.get('search')
        region = self.request.GET.get('region')
        if search:
            queryset = queryset.filter(Q(nom__icontains=search) | Q(region__nom__icontains=search))
        if region:
            queryset = queryset.filter(region_id=region)
        return queryset.order_by('region__nom', 'nom')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            'search': self.request.GET.get('search', ''),
            'entity_label': 'Prefecture',
            'entity_label_plural': 'Prefectures',
            'create_url_name': 'enseignants:prefecture_create',
            'update_url_name': 'enseignants:prefecture_update',
            'delete_url_name': 'enseignants:prefecture_delete',
            'relations_hint': 'Relation: region',
            'csv_entity': 'prefectures',
            'item_rows': [
                {
                    'object': prefecture,
                    'label': prefecture.nom,
                    'extra_values': [prefecture.region.nom if prefecture.region_id else ''],
                }
                for prefecture in context['items']
            ],
            'extra_columns': ['Region'],
        })
        return add_model_permission_flags(context, self.request, Prefecture)


class PrefectureCreateView(LoginRequiredMixin, EnseignantsWriteRequiredMixin, GenericEntityContextMixin, CreateView):
    model = Prefecture
    form_class = PrefectureForm
    template_name = 'enseignants/generic_form.html'
    success_url = reverse_lazy('enseignants:prefecture_list')
    entity_label = 'Prefecture'
    entity_label_plural = 'Prefectures'
    list_url_name = 'enseignants:prefecture_list'


class PrefectureUpdateView(LoginRequiredMixin, EnseignantsWriteRequiredMixin, GenericEntityContextMixin, UpdateView):
    model = Prefecture
    form_class = PrefectureForm
    template_name = 'enseignants/generic_form.html'
    success_url = reverse_lazy('enseignants:prefecture_list')
    entity_label = 'Prefecture'
    entity_label_plural = 'Prefectures'
    list_url_name = 'enseignants:prefecture_list'


class PrefectureDeleteView(LoginRequiredMixin, EnseignantsWriteRequiredMixin, GenericEntityContextMixin, DeleteView):
    model = Prefecture
    template_name = 'enseignants/generic_confirm_delete.html'
    success_url = reverse_lazy('enseignants:prefecture_list')
    entity_label = 'Prefecture'
    entity_label_plural = 'Prefectures'
    list_url_name = 'enseignants:prefecture_list'


class CommuneListView(LoginRequiredMixin, PermissionRequiredMixin, AdjustablePaginationMixin, ListView):
    model = Commune
    model_permission_model = Commune
    required_action = 'view'
    template_name = 'enseignants/generic_list.html'
    context_object_name = 'items'
    paginate_by = 20

    def get_queryset(self):
        queryset = Commune.objects.select_related('prefecture', 'prefecture__region').all()
        search = self.request.GET.get('search')
        if search:
            queryset = queryset.filter(Q(nom__icontains=search) | Q(prefecture__nom__icontains=search))
        return queryset.order_by('prefecture__region__nom', 'prefecture__nom', 'nom')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            'search': self.request.GET.get('search', ''),
            'entity_label': 'Commune',
            'entity_label_plural': 'Communes',
            'create_url_name': 'enseignants:commune_create',
            'update_url_name': 'enseignants:commune_update',
            'delete_url_name': 'enseignants:commune_delete',
            'relations_hint': 'Relation: prefecture, region',
            'csv_entity': 'communes',
            'item_rows': [
                {
                    'object': commune,
                    'label': commune.nom,
                    'extra_values': [
                        commune.prefecture.nom if commune.prefecture_id else '',
                        commune.prefecture.region.nom if commune.prefecture_id and commune.prefecture.region_id else '',
                    ],
                }
                for commune in context['items']
            ],
            'extra_columns': ['Prefecture', 'Region'],
        })
        return add_model_permission_flags(context, self.request, Commune)


class CommuneCreateView(LoginRequiredMixin, EnseignantsWriteRequiredMixin, GenericEntityContextMixin, CreateView):
    model = Commune
    form_class = CommuneForm
    template_name = 'enseignants/generic_form.html'
    success_url = reverse_lazy('enseignants:commune_list')
    entity_label = 'Commune'
    entity_label_plural = 'Communes'
    list_url_name = 'enseignants:commune_list'


class CommuneUpdateView(LoginRequiredMixin, EnseignantsWriteRequiredMixin, GenericEntityContextMixin, UpdateView):
    model = Commune
    form_class = CommuneForm
    template_name = 'enseignants/generic_form.html'
    success_url = reverse_lazy('enseignants:commune_list')
    entity_label = 'Commune'
    entity_label_plural = 'Communes'
    list_url_name = 'enseignants:commune_list'


class CommuneDeleteView(LoginRequiredMixin, EnseignantsWriteRequiredMixin, GenericEntityContextMixin, DeleteView):
    model = Commune
    template_name = 'enseignants/generic_confirm_delete.html'
    success_url = reverse_lazy('enseignants:commune_list')
    entity_label = 'Commune'
    entity_label_plural = 'Communes'
    list_url_name = 'enseignants:commune_list'


class QuartierListView(LoginRequiredMixin, PermissionRequiredMixin, AdjustablePaginationMixin, ListView):
    model = Quartier
    model_permission_model = Quartier
    required_action = 'view'
    template_name = 'enseignants/generic_list.html'
    context_object_name = 'items'
    paginate_by = 20

    def get_queryset(self):
        queryset = Quartier.objects.select_related('commune', 'commune__prefecture').all()
        search = self.request.GET.get('search')
        if search:
            queryset = queryset.filter(Q(nom__icontains=search) | Q(commune__nom__icontains=search))
        return queryset.order_by('commune__prefecture__nom', 'commune__nom', 'nom')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            'search': self.request.GET.get('search', ''),
            'entity_label': 'Quartier',
            'entity_label_plural': 'Quartiers',
            'create_url_name': 'enseignants:quartier_create',
            'update_url_name': 'enseignants:quartier_update',
            'delete_url_name': 'enseignants:quartier_delete',
            'relations_hint': 'Relation: commune, prefecture',
            'csv_entity': 'quartiers',
            'item_rows': [
                {
                    'object': quartier,
                    'label': quartier.nom,
                    'extra_values': [
                        quartier.commune.nom if quartier.commune_id else '',
                        quartier.commune.prefecture.nom if quartier.commune_id and quartier.commune.prefecture_id else '',
                    ],
                }
                for quartier in context['items']
            ],
            'extra_columns': ['Commune', 'Prefecture'],
        })
        return add_model_permission_flags(context, self.request, Quartier)


class QuartierCreateView(LoginRequiredMixin, EnseignantsWriteRequiredMixin, GenericEntityContextMixin, CreateView):
    model = Quartier
    form_class = QuartierForm
    template_name = 'enseignants/generic_form.html'
    success_url = reverse_lazy('enseignants:quartier_list')
    entity_label = 'Quartier'
    entity_label_plural = 'Quartiers'
    list_url_name = 'enseignants:quartier_list'


class QuartierUpdateView(LoginRequiredMixin, EnseignantsWriteRequiredMixin, GenericEntityContextMixin, UpdateView):
    model = Quartier
    form_class = QuartierForm
    template_name = 'enseignants/generic_form.html'
    success_url = reverse_lazy('enseignants:quartier_list')
    entity_label = 'Quartier'
    entity_label_plural = 'Quartiers'
    list_url_name = 'enseignants:quartier_list'


class QuartierDeleteView(LoginRequiredMixin, EnseignantsWriteRequiredMixin, GenericEntityContextMixin, DeleteView):
    model = Quartier
    template_name = 'enseignants/generic_confirm_delete.html'
    success_url = reverse_lazy('enseignants:quartier_list')
    entity_label = 'Quartier'
    entity_label_plural = 'Quartiers'
    list_url_name = 'enseignants:quartier_list'


class SecteurListView(LoginRequiredMixin, PermissionRequiredMixin, AdjustablePaginationMixin, ListView):
    model = Secteur
    model_permission_model = Secteur
    required_action = 'view'
    template_name = 'enseignants/generic_list.html'
    context_object_name = 'items'
    paginate_by = 20

    def get_queryset(self):
        queryset = Secteur.objects.select_related('quartier', 'quartier__commune').all()
        search = self.request.GET.get('search')
        if search:
            queryset = queryset.filter(
                Q(nom__icontains=search)
                | Q(quartier__nom__icontains=search)
                | Q(quartier__commune__nom__icontains=search)
            )
        return queryset.order_by('nom')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            'search': self.request.GET.get('search', ''),
            'entity_label': 'Secteur',
            'entity_label_plural': 'Secteurs',
            'create_url_name': 'enseignants:secteur_create',
            'update_url_name': 'enseignants:secteur_update',
            'delete_url_name': 'enseignants:secteur_delete',
            'relations_hint': 'Relation: quartier, commune',
            'csv_entity': 'secteurs',
            'item_rows': [
                {
                    'object': secteur,
                    'label': secteur.nom,
                    'extra_values': [
                        secteur.quartier.nom if secteur.quartier_id else '',
                        secteur.quartier.commune.nom if secteur.quartier_id and secteur.quartier.commune_id else '',
                    ],
                }
                for secteur in context['items']
            ],
            'extra_columns': ['Quartier', 'Commune'],
        })
        return add_model_permission_flags(context, self.request, Secteur)


class SecteurCreateView(LoginRequiredMixin, EnseignantsWriteRequiredMixin, GenericEntityContextMixin, CreateView):
    model = Secteur
    form_class = SecteurForm
    template_name = 'enseignants/generic_form.html'
    success_url = reverse_lazy('enseignants:secteur_list')
    entity_label = 'Secteur'
    entity_label_plural = 'Secteurs'
    list_url_name = 'enseignants:secteur_list'


class SecteurUpdateView(LoginRequiredMixin, EnseignantsWriteRequiredMixin, GenericEntityContextMixin, UpdateView):
    model = Secteur
    form_class = SecteurForm
    template_name = 'enseignants/generic_form.html'
    success_url = reverse_lazy('enseignants:secteur_list')
    entity_label = 'Secteur'
    entity_label_plural = 'Secteurs'
    list_url_name = 'enseignants:secteur_list'


class SecteurDeleteView(LoginRequiredMixin, EnseignantsWriteRequiredMixin, GenericEntityContextMixin, DeleteView):
    model = Secteur
    template_name = 'enseignants/generic_confirm_delete.html'
    success_url = reverse_lazy('enseignants:secteur_list')
    entity_label = 'Secteur'
    entity_label_plural = 'Secteurs'
    list_url_name = 'enseignants:secteur_list'


# ============= ETABLISSEMENT VIEWS =============

class EtablissementListView(LoginRequiredMixin, PermissionRequiredMixin, AdjustablePaginationMixin, ListView):
    model = Etablissement
    model_permission_model = Etablissement
    required_action = 'view'
    template_name = 'enseignants/etablissement_list.html'
    context_object_name = 'etablissements'
    paginate_by = 20
    
    def get_queryset(self):
        queryset = Etablissement.objects.all()
        search = self.request.GET.get('search')
        if search:
            queryset = queryset.filter(
                Q(nom__icontains=search) | Q(code__icontains=search) | Q(email__icontains=search)
            )
        return queryset.order_by(Lower('nom'), 'nom')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['search'] = self.request.GET.get('search', '')
        return add_model_permission_flags(context, self.request, Etablissement)


class EtablissementDetailView(LoginRequiredMixin, PermissionRequiredMixin, DetailView):
    model = Etablissement
    model_permission_model = Etablissement
    required_action = 'view'
    template_name = 'enseignants/etablissement_detail.html'
    context_object_name = 'etablissement'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['filieres'] = self.object.filieres.all()
        context['professeurs'] = self.object.professeurs.all()
        return context


class EtablissementCreateView(LoginRequiredMixin, EnseignantsWriteRequiredMixin, CreateView):
    model = Etablissement
    form_class = EtablissementForm
    template_name = 'enseignants/etablissement_form.html'
    success_url = reverse_lazy('enseignants:etablissement_list')

    def form_valid(self, form):
        with transaction.atomic():
            response = super().form_valid(form)
            user, created, password = _ensure_user_for_directeur(self.object)

        if user and created:
            messages.success(
                self.request,
                f"Établissement enregistré. Compte directeur créé: identifiant '{user.username}', mot de passe provisoire '{password}'."
            )
        elif user:
            messages.info(
                self.request,
                f"Établissement enregistré. Compte directeur existant mis à jour: '{user.username}' (rôle directeur d'école)."
            )
        return response


class EtablissementUpdateView(LoginRequiredMixin, EnseignantsWriteRequiredMixin, UpdateView):
    model = Etablissement
    form_class = EtablissementForm
    template_name = 'enseignants/etablissement_form.html'
    success_url = reverse_lazy('enseignants:etablissement_list')

    def form_valid(self, form):
        with transaction.atomic():
            response = super().form_valid(form)
            user, created, password = _ensure_user_for_directeur(self.object)

        if user and created:
            messages.success(
                self.request,
                f"Établissement mis à jour. Compte directeur créé: identifiant '{user.username}', mot de passe provisoire '{password}'."
            )
        elif user:
            messages.info(
                self.request,
                f"Établissement mis à jour. Compte directeur existant mis à jour: '{user.username}' (rôle directeur d'école)."
            )
        return response


class EtablissementDeleteView(LoginRequiredMixin, EnseignantsWriteRequiredMixin, DeleteView):
    model = Etablissement
    template_name = 'enseignants/etablissement_confirm_delete.html'
    success_url = reverse_lazy('enseignants:etablissement_list')


# ============= FILIERE VIEWS =============

class FiliereListView(LoginRequiredMixin, PermissionRequiredMixin, AdjustablePaginationMixin, ListView):
    model = Filiere
    model_permission_model = Filiere
    required_action = 'view'
    template_name = 'enseignants/filiere_list.html'
    context_object_name = 'filieres'
    paginate_by = 20
    
    def get_queryset(self):
        queryset = Filiere.objects.prefetch_related('etablissements').all()
        search = self.request.GET.get('search')
        etablissement = self.request.GET.get('etablissement')
        if search:
            queryset = queryset.filter(
                Q(nom__icontains=search) | Q(code__icontains=search)
            )
        if etablissement:
            queryset = queryset.filter(etablissements__id=etablissement)
        return queryset.distinct().order_by('nom')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['search'] = self.request.GET.get('search', '')
        context['etablissements'] = Etablissement.objects.all()
        context['selected_etablissement'] = self.request.GET.get('etablissement', '')
        return add_model_permission_flags(context, self.request, Filiere)


class FiliereDetailView(LoginRequiredMixin, PermissionRequiredMixin, DetailView):
    model = Filiere
    model_permission_model = Filiere
    required_action = 'view'
    template_name = 'enseignants/filiere_detail.html'
    context_object_name = 'filiere'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['programmes'] = self.object.programmes.all()
        context['etablissements_lies'] = self.object.etablissements.order_by('nom')
        return context


class FiliereCreateView(LoginRequiredMixin, EnseignantsWriteRequiredMixin, CreateView):
    model = Filiere
    form_class = FiliereForm
    template_name = 'enseignants/filiere_form.html'
    success_url = reverse_lazy('enseignants:filiere_list')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['programme_heures_map'] = json.dumps(
            {str(programme.id): (programme.nombre_heures or 0) for programme in Programme.objects.only('id', 'nombre_heures')}
        )
        return context

    def _sync_programmes(self, programmes):
        selected_ids = [programme.id for programme in programmes]
        Programme.objects.filter(filiere=self.object).exclude(id__in=selected_ids).update(filiere=None)
        if selected_ids:
            Programme.objects.filter(id__in=selected_ids).update(filiere=self.object)
            self.object.programme_id = selected_ids[0]
        else:
            self.object.programme_id = None
        self.object.save(update_fields=['programme'])

    @staticmethod
    def _build_unique_code(base_code, exclude_pk=None):
        base = (base_code or '').strip() or 'FILIERE'
        base = base[:50]
        candidate = base
        suffix = 1
        qs = Filiere.objects.exclude(pk=exclude_pk) if exclude_pk else Filiere.objects.all()
        while qs.filter(code=candidate).exists():
            suffix += 1
            suffix_text = f"-{suffix}"
            candidate = f"{base[:50 - len(suffix_text)]}{suffix_text}"
        return candidate

    def form_valid(self, form):
        etablissements = list(form.cleaned_data.get('etablissements') or [])
        if not etablissements:
            form.add_error('etablissements', "Veuillez sélectionner au moins un établissement.")
            return self.form_invalid(form)

        programmes = form.cleaned_data.get('programmes') or []

        with transaction.atomic():
            self.object = form.save(commit=False)
            self.object.etablissement = etablissements[0]
            self.object.code = self._build_unique_code(self.object.code)
            self.object.save()
            self.object.etablissements.set(etablissements)
            self._sync_programmes(programmes)

        return redirect(self.get_success_url())


class FiliereUpdateView(LoginRequiredMixin, EnseignantsWriteRequiredMixin, UpdateView):
    model = Filiere
    form_class = FiliereForm
    template_name = 'enseignants/filiere_form.html'
    success_url = reverse_lazy('enseignants:filiere_list')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['programme_heures_map'] = json.dumps(
            {str(programme.id): (programme.nombre_heures or 0) for programme in Programme.objects.only('id', 'nombre_heures')}
        )
        return context

    def _sync_programmes(self, programmes):
        selected_ids = [programme.id for programme in programmes]
        Programme.objects.filter(filiere=self.object).exclude(id__in=selected_ids).update(filiere=None)
        if selected_ids:
            Programme.objects.filter(id__in=selected_ids).update(filiere=self.object)
            self.object.programme_id = selected_ids[0]
        else:
            self.object.programme_id = None
        self.object.save(update_fields=['programme'])

    @staticmethod
    def _build_unique_code(base_code, exclude_pk=None):
        base = (base_code or '').strip() or 'FILIERE'
        base = base[:50]
        candidate = base
        suffix = 1
        qs = Filiere.objects.exclude(pk=exclude_pk) if exclude_pk else Filiere.objects.all()
        while qs.filter(code=candidate).exists():
            suffix += 1
            suffix_text = f"-{suffix}"
            candidate = f"{base[:50 - len(suffix_text)]}{suffix_text}"
        return candidate

    def form_valid(self, form):
        etablissements = list(form.cleaned_data.get('etablissements') or [])
        if not etablissements:
            form.add_error('etablissements', "Veuillez sélectionner au moins un établissement.")
            return self.form_invalid(form)

        programmes = form.cleaned_data.get('programmes') or []

        with transaction.atomic():
            self.object = form.save(commit=False)
            self.object.etablissement = etablissements[0]
            self.object.code = self._build_unique_code(self.object.code, exclude_pk=self.object.pk)
            self.object.save()
            self.object.etablissements.set(etablissements)

            self._sync_programmes(programmes)

        return redirect(self.get_success_url())


class FiliereDeleteView(LoginRequiredMixin, EnseignantsWriteRequiredMixin, DeleteView):
    model = Filiere
    template_name = 'enseignants/generic_confirm_delete.html'
    success_url = reverse_lazy('enseignants:filiere_list')

    def test_func(self):
        user = self.request.user
        return bool(user and user.is_authenticated and user.is_superuser and user.has_perm('enseignants.delete_filiere'))

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['entity_label'] = 'Filiere'
        context['entity_label_plural'] = 'Filieres'
        context['list_url_name'] = 'enseignants:filiere_list'
        return context


# ============= PROGRAMME VIEWS =============

class ProgrammeListView(LoginRequiredMixin, PermissionRequiredMixin, AdjustablePaginationMixin, ListView):
    model = Programme
    model_permission_model = Programme
    required_action = 'view'
    template_name = 'enseignants/generic_list.html'
    context_object_name = 'items'
    paginate_by = 20

    def get_queryset(self):
        queryset = Programme.objects.select_related('filiere').all()
        search = self.request.GET.get('search')
        if search:
            queryset = queryset.filter(Q(nom__icontains=search) | Q(filiere__nom__icontains=search))
        return queryset.order_by('nom')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            'search': self.request.GET.get('search', ''),
            'entity_label': 'Programme',
            'entity_label_plural': 'Programmes',
            'create_url_name': 'enseignants:programme_create',
            'update_url_name': 'enseignants:programme_update',
            'delete_url_name': 'enseignants:programme_delete',
            'relations_hint': 'Relation: filiere et modules de formation (multiple)',
            'csv_entity': 'programmes',
        })
        return add_model_permission_flags(context, self.request, Programme)

class ProgrammeCreateView(LoginRequiredMixin, EnseignantsWriteRequiredMixin, CreateView):
    model = Programme
    form_class = ProgrammeForm
    template_name = 'enseignants/programme_form.html'
    success_url = reverse_lazy('enseignants:programme_list')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['module_heures_map'] = json.dumps(
            {str(module.id): (module.nombre_heures or 0) for module in Module.objects.only('id', 'nombre_heures')}
        )
        return context


class ProgrammeDetailView(LoginRequiredMixin, PermissionRequiredMixin, DetailView):
    model = Programme
    model_permission_model = Programme
    required_action = 'view'
    template_name = 'enseignants/programme_detail.html'
    context_object_name = 'programme'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['modules'] = self.object.module_formation.all().order_by('nom')
        return context


class ProgrammeUpdateView(LoginRequiredMixin, EnseignantsWriteRequiredMixin, UpdateView):
    model = Programme
    form_class = ProgrammeForm
    template_name = 'enseignants/programme_form.html'
    success_url = reverse_lazy('enseignants:programme_list')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['module_heures_map'] = json.dumps(
            {str(module.id): (module.nombre_heures or 0) for module in Module.objects.only('id', 'nombre_heures')}
        )
        return context


class ProgrammeDeleteView(LoginRequiredMixin, EnseignantsWriteRequiredMixin, DeleteView):
    model = Programme
    template_name = 'enseignants/generic_confirm_delete.html'
    success_url = reverse_lazy('enseignants:programme_list')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['entity_label'] = 'Programme'
        context['entity_label_plural'] = 'Programmes'
        context['list_url_name'] = 'enseignants:programme_list'
        return context


# ============= MODULE VIEWS =============

class ModuleListView(LoginRequiredMixin, PermissionRequiredMixin, AdjustablePaginationMixin, ListView):
    model = Module
    model_permission_model = Module
    required_action = 'view'
    template_name = 'enseignants/generic_list.html'
    context_object_name = 'items'
    paginate_by = 20

    def get_queryset(self):
        queryset = Module.objects.all()
        search = self.request.GET.get('search')
        if search:
            queryset = queryset.filter(Q(nom__icontains=search) | Q(code__icontains=search))
        return queryset.order_by('nom')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            'search': self.request.GET.get('search', ''),
            'entity_label': 'Module',
            'entity_label_plural': 'Modules',
            'create_url_name': 'enseignants:module_create',
            'update_url_name': 'enseignants:module_update',
            'delete_url_name': 'enseignants:module_delete',
            'relations_hint': 'Aucune relation obligatoire',
            'csv_entity': 'modules',
        })
        return add_model_permission_flags(context, self.request, Module)

class ModuleCreateView(LoginRequiredMixin, EnseignantsWriteRequiredMixin, CreateView):
    model = Module
    form_class = ModuleForm
    template_name = 'enseignants/module_form.html'
    success_url = reverse_lazy('enseignants:module_list')


class ModuleDetailView(LoginRequiredMixin, PermissionRequiredMixin, DetailView):
    model = Module
    model_permission_model = Module
    required_action = 'view'
    template_name = 'enseignants/module_detail.html'
    context_object_name = 'module'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['affectations'] = self.object.affectations.filter(actif=True)
        return context


class ModuleUpdateView(LoginRequiredMixin, EnseignantsWriteRequiredMixin, UpdateView):
    model = Module
    form_class = ModuleForm
    template_name = 'enseignants/module_form.html'
    success_url = reverse_lazy('enseignants:module_list')


class ModuleDeleteView(LoginRequiredMixin, EnseignantsWriteRequiredMixin, DeleteView):
    model = Module
    template_name = 'enseignants/generic_confirm_delete.html'
    success_url = reverse_lazy('enseignants:module_list')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['entity_label'] = 'Module'
        context['entity_label_plural'] = 'Modules'
        context['list_url_name'] = 'enseignants:module_list'
        return context


# ============= PROFESSEUR VIEWS =============

class ProfesseurListView(LoginRequiredMixin, PermissionRequiredMixin, AdjustablePaginationMixin, ListView):
    model = Professeur
    model_permission_model = Professeur
    required_action = 'view'
    template_name = 'enseignants/professeur_list.html'
    context_object_name = 'professeurs'
    paginate_by = 20
    
    def get_queryset(self):
        queryset = Professeur.objects.select_related('etablissement').all()
        search = self.request.GET.get('search')
        etablissement = self.request.GET.get('etablissement')
        statut = self.request.GET.get('statut')
        if search:
            queryset = queryset.filter(
                Q(matricule__icontains=search) | Q(nom__icontains=search) | Q(prenom__icontains=search) | 
                Q(email__icontains=search) | Q(specialite__icontains=search)
            )
        if etablissement:
            queryset = queryset.filter(etablissement_id=etablissement)
        if statut:
            queryset = queryset.filter(statut=statut)
        return queryset.order_by('etablissement', 'nom', 'prenom')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['search'] = self.request.GET.get('search', '')
        context['etablissements'] = Etablissement.objects.all()
        context['selected_etablissement'] = self.request.GET.get('etablissement', '')
        context['selected_statut'] = self.request.GET.get('statut', '')
        context['statut_choices'] = Professeur._meta.get_field('statut').choices
        context['csv_entity'] = 'professeurs'
        return add_model_permission_flags(context, self.request, Professeur)


class ProfesseurDetailView(LoginRequiredMixin, PermissionRequiredMixin, DetailView):
    model = Professeur
    model_permission_model = Professeur
    required_action = 'view'
    template_name = 'enseignants/professeur_detail.html'
    context_object_name = 'professeur'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['affectations'] = self.object.affectations.filter(actif=True)
        context['heures_restantes'] = self.object.heures_restantes
        context['taux_utilisation'] = self.object.taux_utilisation
        taux = float(self.object.taux_utilisation or 0)
        context['taux_utilisation_width'] = max(0, min(int(round(taux)), 100))
        context['quota_atteint'] = context['heures_restantes'] <= 0
        # Récupérer le compte utilisateur lié pour fallback photo de profil
        User = get_user_model()
        prof = self.object
        linked_user = None
        if prof.email:
            linked_user = User.objects.filter(email__iexact=prof.email).first()
        if linked_user is None and prof.matricule:
            linked_user = User.objects.filter(username__iexact=prof.matricule).first()
        context['professeur_user'] = linked_user
        return context


class ProfesseurCreateView(LoginRequiredMixin, EnseignantsWriteRequiredMixin, CreateView):
    model = Professeur
    form_class = ProfesseurForm
    template_name = 'enseignants/professeur_form.html'
    success_url = reverse_lazy('enseignants:professeur_list')

    def form_valid(self, form):
        with transaction.atomic():
            response = super().form_valid(form)
            user, created, password = _ensure_user_for_professeur(self.object)

        if created:
            messages.success(
                self.request,
                f"Professeur enregistré. Compte utilisateur créé: identifiant '{user.username}', mot de passe provisoire '{password}'."
            )
        else:
            messages.info(
                self.request,
                f"Professeur enregistré. Compte utilisateur existant mis à jour: '{user.username}' (rôle professeur)."
            )
        return response


class ProfesseurUpdateView(LoginRequiredMixin, EnseignantsWriteRequiredMixin, UpdateView):
    model = Professeur
    form_class = ProfesseurForm
    template_name = 'enseignants/professeur_form.html'
    success_url = reverse_lazy('enseignants:professeur_list')


class ProfesseurDeleteView(LoginRequiredMixin, EnseignantsWriteRequiredMixin, DeleteView):
    model = Professeur
    template_name = 'enseignants/professeur_confirm_delete.html'
    success_url = reverse_lazy('enseignants:professeur_list')


# ============= AFFECTATION VIEWS =============

class AffectationListView(LoginRequiredMixin, PermissionRequiredMixin, AdjustablePaginationMixin, ListView):
    model = Professeur
    model_permission_model = Affectation
    required_action = 'view'
    template_name = 'enseignants/affectation_list.html'
    context_object_name = 'affectation_groups'
    paginate_by = 20
    
    def get_queryset(self):
        affectations_qs = (
            Affectation.objects.select_related('professeur', 'module')
            .only(
                'id', 'professeur_id', 'module__nom', 'heures_affectees', 'nombre_heures',
                'priorite', 'date_debut', 'date_fin', 'actif'
            )
            .all()
        )
        search = self.request.GET.get('search')
        priorite = self.request.GET.get('priorite')
        if search:
            affectations_qs = affectations_qs.filter(
                Q(professeur__nom__icontains=search) | Q(professeur__prenom__icontains=search) |
                Q(module__nom__icontains=search)
            )
        if priorite:
            affectations_qs = affectations_qs.filter(priorite=priorite)

        affectations_qs = affectations_qs.order_by('-priorite', 'module__nom')
        prof_ids = affectations_qs.values_list('professeur_id', flat=True).distinct()
        return (
            Professeur.objects.filter(pk__in=prof_ids)
            .only('id', 'prenom', 'nom', 'etablissement_id')
            .prefetch_related(Prefetch('affectations', queryset=affectations_qs, to_attr='filtered_affectations'))
            .order_by('nom', 'prenom')
        )
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['search'] = self.request.GET.get('search', '')
        context['selected_priorite'] = self.request.GET.get('priorite', '')
        context['priorite_choices'] = Affectation._meta.get_field('priorite').choices
        group_rows = []
        for professeur in context['affectation_groups']:
            affectations = list(getattr(professeur, 'filtered_affectations', []))
            if not affectations:
                continue
            total_heures = sum((a.heures_affectees or a.nombre_heures or 0) for a in affectations)
            date_debut_min = min(a.date_debut for a in affectations if a.date_debut)
            dates_fin = [a.date_fin for a in affectations if a.date_fin]
            date_fin_max = max(dates_fin) if dates_fin else None
            group_rows.append({
                'professeur': professeur,
                'affectations': affectations,
                'total_heures': total_heures,
                'date_debut_min': date_debut_min,
                'date_fin_max': date_fin_max,
                'all_actif': all(a.actif for a in affectations),
            })
        context['group_rows'] = group_rows
        return add_model_permission_flags(context, self.request, Affectation)


class AffectationDetailView(LoginRequiredMixin, PermissionRequiredMixin, DetailView):
    model = Affectation
    model_permission_model = Affectation
    required_action = 'view'
    template_name = 'enseignants/affectation_detail.html'
    context_object_name = 'affectation'


class AffectationCreateView(LoginRequiredMixin, EnseignantsWriteRequiredMixin, CreateView):
    model = Affectation
    form_class = AffectationForm
    template_name = 'enseignants/affectation_form.html'
    success_url = reverse_lazy('enseignants:affectation_list')

    def dispatch(self, request, *args, **kwargs):
        professeur_value = request.GET.get('professeur') or request.GET.get('professeur_id')
        if professeur_value:
            professeur = Professeur.objects.filter(pk=professeur_value).first()
            if professeur:
                snapshot = _get_professeur_capacity_snapshot(professeur)
                heures_restantes = snapshot['heures_restantes']
                if heures_restantes <= 0:
                    messages.warning(
                        request,
                        "Quota atteint: ce professeur ne peut plus recevoir de nouvelle affectation.",
                    )
                    return redirect('enseignants:professeur_detail', pk=professeur.pk)
        return super().dispatch(request, *args, **kwargs)

    def get_initial(self):
        initial = super().get_initial()
        for field_name in ['professeur', 'professeur_id', 'etablissement', 'filiere', 'programme', 'module', 'heures_affectees']:
            value = self.request.GET.get(field_name)
            if value:
                if field_name == 'professeur_id':
                    initial['professeur'] = value
                else:
                    initial[field_name] = value
        return initial

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['module_heures_map'] = json.dumps(
            {str(module.id): (module.nombre_heures or 0) for module in Module.objects.only('id', 'nombre_heures')}
        )
        context['affectation_preview_url'] = reverse('enseignants:ajax-affectation-preview')
        context['current_affectation_id'] = ''
        return context


class AffectationUpdateView(LoginRequiredMixin, EnseignantsWriteRequiredMixin, UpdateView):
    model = Affectation
    form_class = AffectationForm
    template_name = 'enseignants/affectation_form.html'
    success_url = reverse_lazy('enseignants:affectation_list')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['module_heures_map'] = json.dumps(
            {str(module.id): (module.nombre_heures or 0) for module in Module.objects.only('id', 'nombre_heures')}
        )
        context['affectation_preview_url'] = reverse('enseignants:ajax-affectation-preview')
        context['current_affectation_id'] = self.object.pk
        return context


class AffectationDeleteView(LoginRequiredMixin, EnseignantsWriteRequiredMixin, DeleteView):
    model = Affectation
    template_name = 'enseignants/affectation_confirm_delete.html'
    success_url = reverse_lazy('enseignants:affectation_list')


class BesoinListView(LoginRequiredMixin, PermissionRequiredMixin, AdjustablePaginationMixin, ListView):
    model = Module
    allowed_permissions = ('enseignants.view_besoin',)
    template_name = 'enseignants/besoin_list.html'
    context_object_name = 'besoins'
    paginate_by = 25

    def get_queryset(self):
        queryset = Module.objects.all()

        search = self.request.GET.get('search', '').strip()
        etablissement_id = self.request.GET.get('etablissement', '').strip()
        filiere_id = self.request.GET.get('filiere', '').strip()

        if search:
            queryset = queryset.filter(
                Q(nom__icontains=search)
                | Q(code__icontains=search)
                | Q(programmes_principaux__nom__icontains=search)
                | Q(programmes_principaux__filiere__nom__icontains=search)
            )

        if etablissement_id:
            queryset = queryset.filter(
                Q(programmes_principaux__filiere__etablissements__id=etablissement_id)
                | Q(programmes_principaux__filiere__etablissement_id=etablissement_id)
            )

        if filiere_id:
            queryset = queryset.filter(programmes_principaux__filiere_id=filiere_id)

        return queryset.distinct().order_by('nom', 'ordre')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        etablissement_id = self.request.GET.get('etablissement', '').strip()
        filiere_id = self.request.GET.get('filiere', '').strip()

        rows = []
        for module in context['page_obj'].object_list:
            rows.append(
                _build_besoin_row(
                    module,
                    etablissement_id=etablissement_id or None,
                    filiere_id=filiere_id or None,
                    include_suggestions=False,
                )
            )

        context['besoin_rows'] = rows
        context['search'] = self.request.GET.get('search', '')
        context['selected_etablissement'] = etablissement_id
        context['selected_filiere'] = filiere_id
        context['etablissements'] = Etablissement.objects.order_by('nom')
        context['filieres'] = Filiere.objects.order_by('nom')
        return add_model_permission_flags(context, self.request, Module)


class BesoinSuggestionsView(LoginRequiredMixin, PermissionRequiredMixin, ListView):
    model = Professeur
    allowed_permissions = ('enseignants.view_besoin_suggestions',)
    template_name = 'enseignants/besoin_suggestions.html'
    context_object_name = 'suggestions'

    def dispatch(self, request, *args, **kwargs):
        self.module = get_object_or_404(Module, pk=self.kwargs['module_id'])
        self.etablissement_id = request.GET.get('etablissement', '').strip() or None
        self.filiere_id = request.GET.get('filiere', '').strip() or None
        return super().dispatch(request, *args, **kwargs)

    def get_queryset(self):
        return Professeur.objects.none()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        row = _build_besoin_row(
            self.module,
            etablissement_id=self.etablissement_id,
            filiere_id=self.filiere_id,
            include_suggestions=False,
        )
        context.update({
            'module': self.module,
            'besoin_row': row,
            'suggestions': _build_professeur_suggestions(
                self.module,
                etablissement=row['etablissement'],
                filiere=row['filiere'],
                besoin_heures=row['besoins'],
            ),
            'back_url': reverse('enseignants:besoin_list'),
        })
        return context


@login_required
@any_permission_required(
    'enseignants.access_geo_filters',
    'enseignants.view_etablissement',
    'enseignants.add_etablissement',
    'enseignants.change_etablissement',
)
def ajax_prefectures(request):
    region_id = request.GET.get('region_id')
    queryset = Prefecture.objects.none()
    if region_id:
        if str(region_id).isdigit():
            queryset = Prefecture.objects.filter(region_id=int(region_id)).order_by('nom')
        else:
            queryset = Prefecture.objects.filter(region__nom__iexact=region_id).order_by('nom')
    return JsonResponse({
        'results': [{'id': item.id, 'nom': item.nom} for item in queryset]
    })


@login_required
@any_permission_required(
    'enseignants.access_geo_filters',
    'enseignants.view_etablissement',
    'enseignants.add_etablissement',
    'enseignants.change_etablissement',
)
def ajax_communes(request):
    prefecture_id = request.GET.get('prefecture_id')
    queryset = Commune.objects.none()
    if prefecture_id:
        if str(prefecture_id).isdigit():
            queryset = Commune.objects.filter(prefecture_id=int(prefecture_id)).order_by('nom')
        else:
            queryset = Commune.objects.filter(prefecture__nom__iexact=prefecture_id).order_by('nom')
    return JsonResponse({
        'results': [{'id': item.id, 'nom': item.nom} for item in queryset]
    })


@login_required
@any_permission_required(
    'enseignants.access_geo_filters',
    'enseignants.view_etablissement',
    'enseignants.add_etablissement',
    'enseignants.change_etablissement',
)
def ajax_quartiers(request):
    commune_id = request.GET.get('commune_id')
    queryset = Quartier.objects.none()
    if commune_id:
        if str(commune_id).isdigit():
            queryset = Quartier.objects.filter(commune_id=int(commune_id)).order_by('nom')
        else:
            queryset = Quartier.objects.filter(commune__nom__iexact=commune_id).order_by('nom')
    return JsonResponse({
        'results': [{'id': item.id, 'nom': item.nom} for item in queryset]
    })


@login_required
@any_permission_required(
    'enseignants.access_geo_filters',
    'enseignants.view_etablissement',
    'enseignants.add_etablissement',
    'enseignants.change_etablissement',
)
def ajax_secteurs(request):
    quartier_id = request.GET.get('quartier_id')
    queryset = Secteur.objects.none()
    if quartier_id:
        if str(quartier_id).isdigit():
            queryset = Secteur.objects.filter(quartier_id=int(quartier_id)).order_by('nom')
        else:
            queryset = Secteur.objects.filter(quartier__nom__iexact=quartier_id).order_by('nom')
    return JsonResponse({
        'results': [{'id': item.id, 'nom': item.nom} for item in queryset]
    })


@login_required
@any_permission_required(
    'enseignants.view_affectation',
    'enseignants.add_affectation',
    'enseignants.change_affectation',
    'enseignants.view_programme',
    'enseignants.view_filiere',
)
def ajax_programmes_by_filiere(request):
    filiere_id = request.GET.get('filiere_id')
    include_programme_id = request.GET.get('include_programme_id')
    queryset = Programme.objects.none()
    if filiere_id and str(filiere_id).isdigit():
        queryset = Programme.objects.filter(filiere_id=int(filiere_id)).order_by('nom')
    if include_programme_id and str(include_programme_id).isdigit():
        queryset = Programme.objects.filter(
            Q(pk__in=queryset.values_list('pk', flat=True)) | Q(pk=int(include_programme_id))
        ).distinct().order_by('nom')
    return JsonResponse({
        'results': [{'id': item.id, 'nom': item.nom} for item in queryset]
    })


@login_required
@any_permission_required(
    'enseignants.filter_modules_by_filiere',
    'enseignants.view_affectation',
    'enseignants.add_affectation',
    'enseignants.change_affectation',
    'enseignants.view_module',
    'enseignants.view_filiere',
)
def ajax_modules_by_filiere(request):
    filiere_id = request.GET.get('filiere_id')
    programme_id = request.GET.get('programme_id')
    include_module_id = request.GET.get('include_module_id')
    queryset = Module.objects.none()
    if filiere_id and str(filiere_id).isdigit():
        queryset = (
            Module.objects.filter(programmes_principaux__filiere_id=int(filiere_id))
            .distinct()
            .order_by('nom')
        )
        if programme_id and str(programme_id).isdigit():
            queryset = queryset.filter(programmes_principaux__id=int(programme_id)).distinct().order_by('nom')
    if include_module_id and str(include_module_id).isdigit():
        queryset = Module.objects.filter(
            Q(pk__in=queryset.values_list('pk', flat=True)) | Q(pk=int(include_module_id))
        ).distinct().order_by('nom')
    return JsonResponse({
        'results': [
            {'id': item.id, 'nom': item.nom, 'nombre_heures': item.nombre_heures}
            for item in queryset
        ]
    })


@login_required
@any_permission_required(
    'enseignants.filter_filieres_by_etablissement',
    'enseignants.view_affectation',
    'enseignants.add_affectation',
    'enseignants.change_affectation',
    'enseignants.view_filiere',
)
def ajax_filieres_by_etablissement(request):
    etablissement_id = request.GET.get('etablissement_id')
    include_filiere_id = request.GET.get('include_filiere_id')
    queryset = Filiere.objects.none()
    if etablissement_id and str(etablissement_id).isdigit():
        etab_id = int(etablissement_id)
        queryset = Filiere.objects.filter(
            Q(etablissements__id=etab_id) | Q(etablissement_id=etab_id)
        ).distinct().order_by('nom')
    if include_filiere_id and str(include_filiere_id).isdigit():
        queryset = Filiere.objects.filter(
            Q(pk__in=queryset.values_list('pk', flat=True)) | Q(pk=int(include_filiere_id))
        ).distinct().order_by('nom')
    return JsonResponse({
        'results': [{'id': item.id, 'nom': item.nom} for item in queryset]
    })


@login_required
@any_permission_required(
    'enseignants.preview_affectation',
    'enseignants.view_affectation',
    'enseignants.add_affectation',
    'enseignants.change_affectation',
)
def ajax_affectation_preview(request):
    professeur_id = request.GET.get('professeur_id')
    module_id = request.GET.get('module_id')
    etablissement_id = request.GET.get('etablissement_id')
    filiere_id = request.GET.get('filiere_id')
    current_affectation_id = request.GET.get('current_affectation_id') or None
    date_debut_raw = request.GET.get('date_debut')
    date_fin_raw = request.GET.get('date_fin')

    date_debut = None
    date_fin = None
    try:
        date_debut = datetime.strptime(date_debut_raw, '%Y-%m-%d').date() if date_debut_raw else None
    except ValueError:
        date_debut = None
    try:
        date_fin = datetime.strptime(date_fin_raw, '%Y-%m-%d').date() if date_fin_raw else None
    except ValueError:
        date_fin = None

    module = Module.objects.filter(pk=module_id).first() if module_id else None
    professeur = Professeur.objects.select_related('etablissement').filter(pk=professeur_id).first() if professeur_id else None
    filiere = Filiere.objects.select_related('etablissement').prefetch_related('etablissements').filter(pk=filiere_id).first() if filiere_id else None
    etablissement = Etablissement.objects.filter(pk=etablissement_id).first() if etablissement_id else None

    if module and not filiere and etablissement:
        _, filiere, _ = _resolve_besoin_programme(module, etablissement_id=etablissement.pk)
    if filiere and not etablissement:
        etablissement = filiere.get_primary_etablissement()

    row = None
    if module:
        row = _build_besoin_row(
            module,
            etablissement_id=etablissement.pk if etablissement else None,
            filiere_id=filiere.pk if filiere else None,
            exclude_affectation_id=current_affectation_id,
        )
    professeur_snapshot = _get_professeur_capacity_snapshot(professeur, exclude_affectation_id=current_affectation_id) if professeur else None

    suggested_heures = 0
    max_heures_professeur = 0
    max_heures_besoin = 0
    professeur_occupe = False
    conflit_message = ''

    if professeur and date_debut:
        conflits = professeur.affectations.filter(actif=True)
        if current_affectation_id:
            conflits = conflits.exclude(pk=current_affectation_id)
        if date_fin:
            conflits = conflits.filter(
                date_debut__lte=date_fin
            ).filter(
                Q(date_fin__isnull=True) | Q(date_fin__gte=date_debut)
            )
        else:
            conflits = conflits.filter(
                Q(date_fin__isnull=True) | Q(date_fin__gte=date_debut)
            )

        if conflits.exists():
            conflit = conflits.order_by('date_debut').first()
            professeur_occupe = True
            conflit_message = (
                f"Professeur occupé du {conflit.date_debut.strftime('%d/%m/%Y')} "
                f"au {(conflit.date_fin.strftime('%d/%m/%Y') if conflit.date_fin else 'en cours')}"
            )
    if row and professeur_snapshot:
        suggested_heures = min(row['besoins'], professeur_snapshot['heures_restantes'])
        max_heures_professeur = professeur_snapshot['heures_restantes']
        max_heures_besoin = row['besoins']
    elif professeur_snapshot:
        max_heures_professeur = professeur_snapshot['heures_restantes']
    elif row:
        max_heures_besoin = row['besoins']

    max_heures_affectables = suggested_heures
    if max_heures_affectables == 0:
        non_zero_caps = [value for value in [max_heures_professeur, max_heures_besoin] if value > 0]
        max_heures_affectables = min(non_zero_caps) if non_zero_caps else 0

    if professeur_occupe:
        max_heures_affectables = 0
        suggested_heures = 0

    return JsonResponse({
        'module': {
            'id': module.pk,
            'nom': module.nom,
            'heures_totales': module.nombre_heures,
        } if module else None,
        'professeur': {
            'id': professeur.pk,
            'nom_complet': f"{professeur.prenom} {professeur.nom}",
            'specialite': professeur.specialite,
            'etablissement': professeur.etablissement.nom if professeur.etablissement_id else '',
            **professeur_snapshot,
        } if professeur and professeur_snapshot else None,
        'besoin': {
            'etat': row['etat'],
            'heures_couvertes': row['existant'],
            'heures_restantes': row['besoins'],
            'professeurs_existants': row['professeurs_existants'],
            'etablissement': row['etablissement'].nom if row['etablissement'] else '',
            'filiere': row['filiere'].nom if row['filiere'] else '',
        } if row else None,
        'heures_suggerees': suggested_heures,
        'max_heures_professeur': max_heures_professeur,
        'max_heures_besoin': max_heures_besoin,
        'max_heures_affectables': max_heures_affectables,
        'professeur_occupe': professeur_occupe,
        'conflit_message': conflit_message,
    })


ENTITY_CSV_PERMS = {
    'regions':      'enseignants.csv_regions',
    'prefectures':  'enseignants.csv_prefectures',
    'communes':     'enseignants.csv_communes',
    'quartiers':    'enseignants.csv_quartiers',
    'secteurs':     'enseignants.csv_secteurs',
    'programmes':   'enseignants.csv_programmes',
    'modules':      'enseignants.csv_modules',
    'professeurs':  'enseignants.csv_professeurs',
}

ENTITY_CSV_IMPORT_PERMS = ENTITY_CSV_PERMS  # même permission couvre export et import


CSV_CONFIG = {
    'regions': {
        'model': Region,
        'fields': ['id', 'nom'],
        'list_url': 'enseignants:region_list',
    },
    'prefectures': {
        'model': Prefecture,
        'fields': ['id', 'region_id', 'nom'],
        'list_url': 'enseignants:prefecture_list',
    },
    'communes': {
        'model': Commune,
        'fields': ['id', 'prefecture_id', 'nom'],
        'list_url': 'enseignants:commune_list',
    },
    'quartiers': {
        'model': Quartier,
        'fields': ['id', 'commune_id', 'nom'],
        'list_url': 'enseignants:quartier_list',
    },
    'secteurs': {
        'model': Secteur,
        'fields': ['id', 'commune_id', 'quartier_id', 'nom'],
        'required_fields': ['quartier_id', 'nom'],
        'context_only_fields': ['commune_id'],
        'context_field_map': {'commune_id': Commune},
        'list_url': 'enseignants:secteur_list',
    },
    'etablissements': {
        'model': Etablissement,
        'fields': [
            'id', 'nom', 'code', 'region_id', 'prefecture_id', 'commune_id', 'quartier_id',
            'secteur_id', 'localisation', 'contact', 'email', 'directeur', 'date_creation'
        ],
        'required_fields': ['nom'],
        'list_url': 'enseignants:etablissement_list',
    },
    'filieres': {
        'model': Filiere,
        'fields': [
            'id', 'nom', 'programme_id', 'etablissement_id', 'code', 'description',
            'duree_mois', 'nombre_heures_total'
        ],
        'list_url': 'enseignants:filiere_list',
    },
    'programmes': {
        'model': Programme,
        'fields': [
            'id', 'nom', 'filiere_id', 'code', 'description',
            'semestre', 'nombre_heures', 'ordre'
        ],
        'list_url': 'enseignants:programme_list',
    },
    'modules': {
        'model': Module,
        'fields': [
            'id', 'nom', 'code', 'description',
            'nombre_heures', 'ordre'
        ],
        'required_fields': ['nom', 'nombre_heures'],
        'header_aliases': {
            'heure': 'nombre_heures',
            'heures': 'nombre_heures',
            'nb_heures': 'nombre_heures',
            'nombre heure': 'nombre_heures',
            'nombre heures': 'nombre_heures',
            'nombre d heures': 'nombre_heures',
        },
        'list_url': 'enseignants:module_list',
    },
    'professeurs': {
        'model': Professeur,
        'fields': [
            'id', 'matricule', 'prenom', 'nom', 'sexe', 'hierarchie', 'email',
            'telephone', 'specialite', 'statut', 'corps', 'etablissement_id',
            'date_embauche', 'actif', 'heures_affectees', 'heures_disponibles'
        ],
        'required_fields': ['prenom', 'nom', 'specialite'],
        'list_url': 'enseignants:professeur_list',
    },
}


def _normalize_value(value):
    if value is None:
        return None
    value = str(value).strip()
    return value or None


def _normalize_header_name(value):
    if value is None:
        return ''
    raw = str(value).strip().lower()
    raw = unicodedata.normalize('NFD', raw)
    raw = ''.join(ch for ch in raw if unicodedata.category(ch) != 'Mn')
    return ' '.join(raw.replace('_', ' ').split())


def _normalize_geo_key(value):
    normalized = _normalize_header_name(value)
    return ''.join(ch for ch in normalized if ch.isalnum())


def _resolve_csv_field_name(header, expected_headers, header_aliases):
    header_key = _normalize_header_name(header)
    expected_by_key = {_normalize_header_name(field): field for field in expected_headers}
    for field in expected_headers:
        if field.endswith('_id'):
            relation_name = field[:-3]
            relation_aliases = {
                relation_name,
                f'{relation_name}_nom',
                f'nom_{relation_name}',
                f'{relation_name}_code',
                f'code_{relation_name}',
                f'{relation_name} nom',
                f'nom {relation_name}',
                f'{relation_name} code',
                f'code {relation_name}',
            }
            for alias in relation_aliases:
                expected_by_key[_normalize_header_name(alias)] = field
    if header_key in expected_by_key:
        return expected_by_key[header_key]
    alias_target = header_aliases.get(header_key)
    if alias_target in expected_headers:
        return alias_target
    return None


def _get_fk_lookup_mode(field_name, source_header):
    if not source_header or not field_name.endswith('_id'):
        return 'value'

    source_key = _normalize_header_name(source_header)
    field_key = _normalize_header_name(field_name)
    relation_key = _normalize_header_name(field_name[:-3])

    if source_key == field_key:
        return 'id'
    if 'code' in source_key:
        return 'code'
    if source_key == relation_key or 'nom' in source_key:
        return 'name'
    return 'name'


def _build_related_queryset_with_context(related_model, payload):
    queryset = related_model.objects.all()
    for related_field in related_model._meta.get_fields():
        if not getattr(related_field, 'many_to_one', False):
            continue
        payload_key = f'{related_field.name}_id'
        payload_value = payload.get(payload_key)
        if payload_value is not None:
            queryset = queryset.filter(**{payload_key: payload_value})
    return queryset


def _get_related_parent_fields(related_model):
    parent_fields = []
    for related_field in related_model._meta.get_fields():
        if getattr(related_field, 'many_to_one', False):
            parent_fields.append(f'{related_field.name}')
    return parent_fields


def _format_import_error(line_no, column_name, message, raw_value=None):
    parts = [f'Ligne {line_no}']
    if column_name:
        parts.append(f"colonne '{column_name}'")
    if raw_value is not None and _normalize_value(raw_value) is not None:
        parts.append(f"valeur '{_normalize_value(raw_value)}'")
    prefix = ', '.join(parts)
    return f"{prefix}: {message}"


def _resolve_related_object_by_value(related_model, raw_value, lookup_mode, payload):
    queryset = _build_related_queryset_with_context(related_model, payload)
    normalized = _normalize_value(raw_value)
    if normalized is None:
        return None, None

    if lookup_mode == 'id':
        obj = queryset.filter(pk=normalized).first()
        if obj:
            return obj, None
        return None, f"Relation invalide: id={normalized} inexistant"

    lookup_fields = []
    if lookup_mode == 'code' and any(field.name == 'code' for field in related_model._meta.fields):
        lookup_fields.append('code__iexact')

    if lookup_mode == 'name' and any(field.name == 'nom' for field in related_model._meta.fields):
        lookup_fields.append('nom__iexact')

    if lookup_mode == 'value' and any(field.name == 'nom' for field in related_model._meta.fields):
        lookup_fields.append('nom__iexact')

    if lookup_mode == 'value' and any(field.name == 'code' for field in related_model._meta.fields):
        lookup_fields.append('code__iexact')

    if not lookup_fields:
        lookup_fields.append('pk')

    matches = []
    for lookup_field in lookup_fields:
        current_matches = list(queryset.filter(**{lookup_field: normalized})[:2])
        if current_matches:
            matches = current_matches
            break

    if not matches:
        return None, f"Relation invalide: valeur '{normalized}' introuvable"
    if len(matches) > 1:
        parent_fields = _get_related_parent_fields(related_model)
        if parent_fields:
            return None, (
                f"Relation ambigue: valeur '{normalized}' correspond a plusieurs enregistrements. "
                f"Ajoutez aussi une colonne de contexte parmi: {', '.join(parent_fields)}"
            )
        return None, f"Relation ambigue: valeur '{normalized}' correspond a plusieurs enregistrements"
    return matches[0], None


def _build_csv_writer(response):
    response.write('\ufeff')
    return csv.writer(response, delimiter=';', lineterminator='\n')


def _build_csv_reader(decoded_lines):
    sample = '\n'.join(decoded_lines[:5])
    delimiter = ';'
    try:
        dialect = csv.Sniffer().sniff(sample, delimiters=';,')
        delimiter = dialect.delimiter
    except csv.Error:
        pass
    return csv.DictReader(decoded_lines, delimiter=delimiter)


def _resolve_fk_or_error(model, field_name, raw_value, payload=None, source_header=None):
    normalized = _normalize_value(raw_value)
    if normalized is None:
        return None, None

    if not field_name.endswith('_id'):
        return normalized, None

    rel_field = field_name[:-3]
    try:
        field = model._meta.get_field(rel_field)
    except Exception:
        return normalized, None

    related_model = field.remote_field.model
    lookup_mode = _get_fk_lookup_mode(field_name, source_header)
    related_obj, error = _resolve_related_object_by_value(related_model, normalized, lookup_mode, payload or {})
    if error:
        return None, f"{field_name}: {error}"
    return related_obj.pk, None


def _coerce_field_value(model, field_name, value):
    if value is None:
        return None
    if field_name.endswith('_id'):
        return value

    try:
        field = model._meta.get_field(field_name)
        internal_type = field.get_internal_type()

        if internal_type == 'DateField':
            # Accepte aussi les formats Excel courants.
            for fmt in ('%Y-%m-%d', '%d/%m/%Y', '%d-%m-%Y'):
                try:
                    return datetime.strptime(value, fmt).date()
                except ValueError:
                    continue

        if internal_type in ('IntegerField', 'PositiveIntegerField', 'PositiveSmallIntegerField', 'SmallIntegerField'):
            cleaned = str(value).replace('\u00a0', '').replace(' ', '').strip()
            if cleaned == '':
                return None
            return int(cleaned)

        if internal_type == 'BooleanField':
            cleaned = str(value).strip().lower()
            if cleaned in ('1', 'true', 't', 'vrai', 'oui', 'y', 'yes'):
                return True
            if cleaned in ('0', 'false', 'f', 'faux', 'non', 'n', 'no'):
                return False
            return value
    except Exception:
        pass

    return value


def _normalize_professeur_payload(payload):
    statut = payload.get('statut')
    if statut is not None:
        statut_key = _normalize_header_name(statut)
        statut_map = {
            'fonctionnaire': 'permanent',
            'permanent': 'permanent',
            'contractuel': 'contractuel',
            'vacataire': 'vacataire',
            'autre': 'autre',
        }
        payload['statut'] = statut_map.get(statut_key, statut)

    sexe = payload.get('sexe')
    if sexe is not None:
        sexe_key = _normalize_header_name(sexe)
        sexe_map = {
            'm': 'M',
            'masculin': 'M',
            'f': 'F',
            'feminin': 'F',
        }
        payload['sexe'] = sexe_map.get(sexe_key, sexe)

    matricule = payload.get('matricule')
    if matricule is not None:
        payload['matricule'] = str(matricule).replace('\u00a0', ' ').strip()

    return payload


def _get_export_header(field_name):
    if field_name.endswith('_id'):
        return field_name[:-3]
    return field_name


def _get_related_display_value(obj):
    if obj is None:
        return None
    if hasattr(obj, 'nom'):
        return obj.nom
    if hasattr(obj, 'code') and obj.code:
        return obj.code
    return str(obj)


def _get_export_field_value(item, field_name):
    if field_name.endswith('_id'):
        related_obj = getattr(item, field_name[:-3], None)
        return _get_related_display_value(related_obj)
    return getattr(item, field_name, None)


def _generate_module_code(base_name):
    base = ''.join(ch for ch in (base_name or '').upper() if ch.isalnum())[:20] or 'MODULE'
    candidate = base
    suffix = 1
    while Module.objects.filter(code=candidate).exists():
        suffix += 1
        candidate = f"{base[:16]}{suffix:04d}"
    return candidate


def _save_import_row(model, entity, payload):
    # Pour les modules, genere un code automatique si absent.
    if entity == 'modules':
        row_name = payload.get('nom')
        if row_name:
            create_payload = payload.copy()
            if not create_payload.get('code'):
                create_payload['code'] = _generate_module_code(row_name)
            return model.objects.create(**create_payload), 'created'

    # Pour les quartiers, reutilise un quartier existant (commune_id + nom)
    # afin de permettre l'ajout de secteurs sur plusieurs lignes du meme quartier.
    if entity == 'quartiers':
        row_name = payload.get('nom')
        commune_id = payload.get('commune_id')
        if row_name and commune_id:
            existing = model.objects.filter(commune_id=commune_id, nom=row_name).first()
            if existing:
                return existing, 'existing'

    return model.objects.create(**payload), 'created'


@login_required
def export_csv_template(request, entity):
    config = CSV_CONFIG.get(entity)
    if not config:
        return HttpResponse("Entité non supportée.", status=400)
    perm = ENTITY_CSV_PERMS.get(entity)
    if not perm or not request.user.has_perm(perm):
        return HttpResponseForbidden(
            "Vous n'avez pas la permission de télécharger ce modèle CSV.",
        )

    forbidden_response = _forbid_if_no_model_permission(
        request.user,
        config['model'],
        ('view', 'add', 'change'),
        "Vous n'avez pas la permission de télécharger ce modèle CSV.",
    )
    if forbidden_response is not None:
        return forbidden_response

    response = HttpResponse(content_type='text/csv; charset=utf-8')
    response['Content-Disposition'] = f'attachment; filename="template_{entity}.csv"'
    writer = _build_csv_writer(response)
    headers = [_get_export_header(field) for field in config['fields']]
    writer.writerow(headers)
    return response


@login_required
def export_csv_data(request, entity):
    config = CSV_CONFIG.get(entity)
    if not config:
        return HttpResponse("Entité non supportée.", status=400)
    perm = ENTITY_CSV_PERMS.get(entity)
    if not perm or not request.user.has_perm(perm):
        return HttpResponseForbidden(
            "Vous n'avez pas la permission d'exporter ces données.",
        )

    forbidden_response = _forbid_if_no_model_permission(
        request.user,
        config['model'],
        ('view',),
        "Vous n'avez pas la permission d'exporter ces données.",
    )
    if forbidden_response is not None:
        return forbidden_response

    response = HttpResponse(content_type='text/csv; charset=utf-8')
    response['Content-Disposition'] = f'attachment; filename="{entity}.csv"'

    model = config['model']
    fields = config['fields']
    writer = _build_csv_writer(response)
    headers = [_get_export_header(field) for field in fields]
    writer.writerow(headers)

    for item in model.objects.select_related().all():
        writer.writerow([_get_export_field_value(item, field) for field in fields])

    return response


@login_required
def import_csv_data(request, entity):
    config = CSV_CONFIG.get(entity)
    if not config:
        return HttpResponse("Entité non supportée.", status=400)
    perm = ENTITY_CSV_PERMS.get(entity)
    if not perm or not request.user.has_perm(perm):
        return HttpResponseForbidden(
            "Vous n'avez pas la permission d'importer ces données.",
        )

    forbidden_response = _forbid_if_no_model_permission(
        request.user,
        config['model'],
        ('add', 'change'),
        "Vous n'avez pas la permission d'importer ces données.",
    )
    if forbidden_response is not None:
        return forbidden_response

    if request.method != 'POST':
        return HttpResponse("Méthode non autorisée.", status=405)

    csv_file = request.FILES.get('file')
    if not csv_file:
        messages.error(request, 'Aucun fichier CSV fourni.')
        return redirect(config.get('list_url', 'enseignants:etablissement_list'))

    try:
        decoded = csv_file.read().decode('utf-8-sig').splitlines()
        reader = _build_csv_reader(decoded)
        model = config['model']
        created = 0
        skipped = 0
        auto_assigned_etablissement = 0
        errors = []

        if entity == 'quartiers' and not Commune.objects.exists():
            messages.error(request, "Import impossible: aucune commune disponible. Importez d'abord les communes.")
            return redirect(config.get('list_url', 'enseignants:etablissement_list'))

        if entity == 'secteurs' and not Quartier.objects.exists():
            messages.error(request, "Import impossible: aucun quartier disponible. Importez d'abord les quartiers.")
            return redirect(config.get('list_url', 'enseignants:etablissement_list'))

        if not reader.fieldnames:
            messages.error(request, 'Le fichier CSV ne contient pas d\'en-tetes valides.')
            return redirect(config.get('list_url', 'enseignants:etablissement_list'))

        normalized_headers = [header.strip() for header in reader.fieldnames if header]
        expected_headers = config['fields']
        header_aliases = config.get('header_aliases', {})
        required_headers = config.get('required_fields', [field for field in expected_headers if field != 'id'])

        header_map = {}
        unknown_headers = []

        for header in normalized_headers:
            resolved_field = _resolve_csv_field_name(header, expected_headers, header_aliases)
            if not resolved_field:
                unknown_headers.append(header)
                continue
            if resolved_field not in header_map:
                header_map[resolved_field] = header

        missing_required = [field for field in required_headers if field not in header_map]

        if unknown_headers or missing_required:
            if unknown_headers:
                messages.error(request, f"Import {entity}: colonnes inconnues: {'; '.join(unknown_headers)}")
            if missing_required:
                messages.error(request, f"Import {entity}: colonnes requises manquantes: {'; '.join(missing_required)}")
            return redirect(config.get('list_url', 'enseignants:etablissement_list'))

        quartier_by_name = {}
        default_quartier_id = None
        if entity == 'secteurs':
            for quartier in Quartier.objects.all().only('id', 'nom').order_by('id'):
                if default_quartier_id is None:
                    default_quartier_id = quartier.id
                normalized_name = _normalize_geo_key(quartier.nom)
                if normalized_name and normalized_name not in quartier_by_name:
                    quartier_by_name[normalized_name] = quartier.id

        default_professeur_etablissement_id = None
        if entity == 'professeurs':
            default_etablissement = Etablissement.objects.only('id').order_by('id').first()
            if default_etablissement:
                default_professeur_etablissement_id = default_etablissement.id

        for line_no, row in enumerate(reader, start=2):
            # Ignore les lignes vides.
            if not any(_normalize_value(v) for v in row.values()):
                continue

            if entity == 'secteurs':
                quartier_header = header_map.get('quartier_id')
                nom_header = header_map.get('nom')

                quartier_value = _normalize_value(row.get(quartier_header)) if quartier_header else None
                nom_value = _normalize_value(row.get(nom_header)) if nom_header else None

                if not nom_value:
                    nom_value = f"SECTEUR_{line_no}"

                quartier_id = None
                if quartier_value:
                    if str(quartier_value).isdigit():
                        matched_quartier = Quartier.objects.filter(pk=int(quartier_value)).first()
                        if matched_quartier:
                            quartier_id = matched_quartier.pk
                    if quartier_id is None:
                        quartier_id = quartier_by_name.get(_normalize_geo_key(quartier_value))
                    if quartier_id is None:
                        matched_quartier = Quartier.objects.filter(nom__iexact=quartier_value).order_by('id').first()
                        if matched_quartier:
                            quartier_id = matched_quartier.pk

                if quartier_id is None:
                    quartier_id = default_quartier_id
                if quartier_id is None:
                    errors.append(_format_import_error(line_no, quartier_header, "aucun quartier disponible pour affectation", quartier_value))
                    continue

                try:
                    model.objects.create(quartier_id=quartier_id, nom=nom_value)
                    created += 1
                except IntegrityError as row_exc:
                    errors.append(_format_import_error(line_no, None, f"doublon ou contrainte invalide: {row_exc}"))
                except Exception as row_exc:
                    errors.append(_format_import_error(line_no, None, str(row_exc)))
                continue

            payload = {}
            line_errors = []
            context_only_fields = set(config.get('context_only_fields', []))

            # Résoudre les champs de contexte en premier pour alimenter la recherche FK
            for ctx_field, ctx_model in config.get('context_field_map', {}).items():
                ctx_header = header_map.get(ctx_field)
                if not ctx_header:
                    continue
                ctx_raw = row.get(ctx_header)
                ctx_norm = _normalize_value(ctx_raw)
                if not ctx_norm:
                    continue
                ctx_obj = ctx_model.objects.filter(nom__iexact=ctx_norm).first()
                if ctx_obj:
                    payload[ctx_field] = ctx_obj.pk

            for field in config['fields']:
                if field == 'id':
                    continue
                if field in context_only_fields:
                    continue  # déjà résolu dans la phase de contexte
                if field == 'quartier_id' and field in payload:
                    continue

                source_header = header_map.get(field)
                if not source_header:
                    continue

                raw_value = row.get(source_header)
                if field in required_headers and _normalize_value(raw_value) is None:
                    line_errors.append(_format_import_error(line_no, source_header, f"champ requis pour '{field}'", raw_value))
                    continue

                resolved, err = _resolve_fk_or_error(
                    model,
                    field,
                    raw_value,
                    payload=payload,
                    source_header=source_header,
                )
                if err:
                    line_errors.append(_format_import_error(line_no, source_header, err, raw_value))
                    continue

                coerced = _coerce_field_value(model, field, resolved)
                if coerced is None and field not in required_headers:
                    continue
                payload[field] = coerced

            if line_errors:
                errors.extend(line_errors)
                continue

            try:
                save_payload = {k: v for k, v in payload.items() if k not in context_only_fields}

                if entity == 'professeurs':
                    save_payload = _normalize_professeur_payload(save_payload)
                    if not save_payload.get('etablissement_id'):
                        if default_professeur_etablissement_id is None:
                            errors.append(_format_import_error(line_no, 'etablissement', "aucun établissement disponible pour affectation automatique"))
                            continue
                        save_payload['etablissement_id'] = default_professeur_etablissement_id
                        auto_assigned_etablissement += 1

                created_obj, import_status = _save_import_row(model, entity, save_payload)
                if import_status == 'created':
                    created += 1
                elif import_status in ('skipped', 'existing'):
                    skipped += 1

            except IntegrityError as row_exc:
                errors.append(_format_import_error(line_no, None, f"doublon ou contrainte invalide: {row_exc}"))
            except Exception as row_exc:
                errors.append(_format_import_error(line_no, None, str(row_exc)))

        if created:
            messages.success(request, f'{created} ligne(s) importée(s) pour {entity}.')
        if skipped:
            messages.warning(request, f'{skipped} ligne(s) ignorée(s) car déjà existantes pour {entity}.')
        if auto_assigned_etablissement:
            messages.info(request, f"{auto_assigned_etablissement} ligne(s) professeurs importée(s) avec établissement par défaut.")
        if errors:
            messages.error(request, f"Import partiel pour {entity}: {len(errors)} erreur(s).")
            for error_message in errors[:10]:
                messages.error(request, error_message)
        if not created and not skipped and not errors:
            messages.warning(request, 'Aucune ligne importée: fichier vide ou lignes non exploitables.')
    except Exception as exc:
        messages.error(request, f'Erreur import {entity}: {exc}')

    return redirect(config.get('list_url', 'enseignants:etablissement_list'))
