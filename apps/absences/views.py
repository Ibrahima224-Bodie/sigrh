from django.shortcuts import render, redirect, get_object_or_404
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView, View
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.urls import reverse, reverse_lazy
from django.db.models import Q
from django.utils import timezone
from django.core.exceptions import PermissionDenied
from django.http import HttpResponseForbidden
from django.contrib import messages
from config.pagination import AdjustablePaginationMixin
from apps.comptes.permissions import (
    CONGE_REQUEST_PERMISSION,
    CongeRequestMixin,
    user_can_approve_conge_directeur,
    user_can_request_conge,
    user_can_validate_conge_drh,
)
from .models import Conge, CommentaireConge
from .forms import CommentaireCongeForm, ApprobationDirecteurForm, ApprobationDRHForm
from .forms_auto import CongeAutoForm
from apps.agents.models import Agent
from apps.enseignants.models import Professeur, Etablissement


def _get_directeur_etablissement(user):
    """Trouve l'établissement rattaché au directeur connecté."""
    if not user or not user.is_authenticated:
        return None

    full_name = f"{user.first_name} {user.last_name}".strip()

    if user.email:
        etablissement = Etablissement.objects.filter(email__iexact=user.email).first()
        if etablissement:
            return etablissement

    if full_name:
        etablissement = Etablissement.objects.filter(directeur__iexact=full_name).first()
        if etablissement:
            return etablissement

    if getattr(user, 'structure_id', None) and user.structure and user.structure.nom:
        etablissement = Etablissement.objects.filter(nom__iexact=user.structure.nom).first()
        if etablissement:
            return etablissement

    return None


def _can_directeur_approve_conge(user, conge):
    if not user_can_approve_conge_directeur(user):
        return False
    if user_can_validate_conge_drh(user):
        return True
    etablissement = _get_directeur_etablissement(user)
    return bool(etablissement and conge.etablissement_id == etablissement.id)


def _user_can_access_conge(user, conge):
    if not user or not user.is_authenticated:
        return False
    if conge.user_demandeur_id == user.id:
        return True
    if user_can_validate_conge_drh(user):
        return True
    if _can_directeur_approve_conge(user, conge):
        return True
    return user.has_perm('absences.view_conge')


def _user_can_comment_conge(user, conge):
    return (
        conge.statut not in ('refuse', 'approuve_drh')
        and (user.has_perm('absences.commenter_conge') or user.has_perm('absences.add_commentaireconge'))
        and _user_can_access_conge(user, conge)
    )


def _first_if_single(queryset):
    """Retourne l'élément si la recherche est non ambiguë, sinon None."""
    ids = list(queryset.values_list('id', flat=True)[:2])
    if len(ids) == 1:
        return queryset.model.objects.get(pk=ids[0])
    return None


def _resolve_agent_for_user(user):
    """Trouve le profil agent correspondant au compte connecté."""
    if not user:
        return None

    email = (user.email or '').strip()
    username = (user.username or '').strip()
    first_name = (user.first_name or '').strip()
    last_name = (user.last_name or '').strip()

    if email:
        agent = Agent.objects.filter(email__iexact=email).first()
        if agent:
            return agent

    if username and '@' in username:
        agent = Agent.objects.filter(email__iexact=username).first()
        if agent:
            return agent

    if username:
        agent = Agent.objects.filter(matricule__iexact=username).first()
        if agent:
            return agent

    if first_name and last_name:
        agent = _first_if_single(
            Agent.objects.filter(nom__iexact=last_name, prenom__iexact=first_name)
        )
        if agent:
            return agent

        agent = _first_if_single(
            Agent.objects.filter(nom__iexact=first_name, prenom__iexact=last_name)
        )
        if agent:
            return agent

    return None


def _resolve_professeur_for_user(user):
    """Trouve le profil professeur correspondant au compte connecté."""
    if not user:
        return None

    email = (user.email or '').strip()
    username = (user.username or '').strip()
    first_name = (user.first_name or '').strip()
    last_name = (user.last_name or '').strip()

    if email:
        professeur = _first_if_single(Professeur.objects.filter(email__iexact=email))
        if professeur:
            return professeur

    if username and '@' in username:
        professeur = _first_if_single(Professeur.objects.filter(email__iexact=username))
        if professeur:
            return professeur

    if username:
        professeur = _first_if_single(Professeur.objects.filter(matricule__iexact=username))
        if professeur:
            return professeur

    if first_name and last_name:
        professeur = _first_if_single(
            Professeur.objects.filter(nom__iexact=last_name, prenom__iexact=first_name)
        )
        if professeur:
            return professeur

        professeur = _first_if_single(
            Professeur.objects.filter(nom__iexact=first_name, prenom__iexact=last_name)
        )
        if professeur:
            return professeur

    return None

class CongeListView(LoginRequiredMixin, AdjustablePaginationMixin, ListView):
    model = Conge
    template_name = 'absences/conge_list.html'
    context_object_name = 'conges'
    paginate_by = 10

    def get_queryset(self):
        user = self.request.user
        queryset = Conge.objects.select_related('agent', 'professeur', 'user_demandeur', 'etablissement')

        agent = _resolve_agent_for_user(user)
        professeur = _resolve_professeur_for_user(user)

        if user_can_validate_conge_drh(user) or user.has_perm('absences.view_conge'):
            queryset = queryset.all()
        else:
            access_filter = Q(user_demandeur=user)

            if user_can_approve_conge_directeur(user):
                etablissement = _get_directeur_etablissement(user)
                if etablissement:
                    access_filter |= Q(statut='demande', etablissement=etablissement)

            if not (user_can_request_conge(user) and (agent or professeur)):
                queryset = queryset.filter(access_filter)
            else:
                queryset = queryset.filter(access_filter)

        statut = (self.request.GET.get('statut') or '').strip()
        if statut:
            queryset = queryset.filter(statut=statut)
        
        search = self.request.GET.get('search')
        if search:
            queryset = queryset.filter(
                Q(agent__nom__icontains=search) |
                Q(agent__prenom__icontains=search) |
                Q(professeur__nom__icontains=search) |
                Q(professeur__prenom__icontains=search) |
                Q(type_conge__icontains=search)
            )
        return queryset.order_by('-id')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        agent = _resolve_agent_for_user(user)
        professeur = _resolve_professeur_for_user(user)
        context['search'] = (self.request.GET.get('search') or '').strip()
        context['selected_statut'] = (self.request.GET.get('statut') or '').strip()
        context['statut_choices'] = Conge.STATUT_CHOICES
        context['can_create_conge'] = user_can_request_conge(user) and bool(agent or professeur)
        context['is_directeur_scope_user'] = user_can_approve_conge_directeur(user) and not user_can_validate_conge_drh(user)
        if context['is_directeur_scope_user']:
            directeur_etablissement = _get_directeur_etablissement(user)
            context['directeur_etablissement'] = directeur_etablissement
            context['directeur_etablissement_non_lie'] = directeur_etablissement is None
        else:
            context['directeur_etablissement'] = None
            context['directeur_etablissement_non_lie'] = False
        return context

class CongeDetailView(LoginRequiredMixin, DetailView):
    model = Conge
    template_name = 'absences/conge_detail.html'
    context_object_name = 'conge'

    def get_object(self, queryset=None):
        obj = super().get_object(queryset)
        if not _user_can_access_conge(self.request.user, obj):
            raise PermissionDenied("Vous n'avez pas accès à cette demande de congé.")
        return obj

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        conge = context['conge']
        if conge.agent_id:
            context['beneficiaire_detail_url'] = reverse('agent-detail', args=[conge.agent_id])
        elif conge.professeur_id:
            context['beneficiaire_detail_url'] = reverse('enseignants:professeur_detail', args=[conge.professeur_id])
        else:
            context['beneficiaire_detail_url'] = None
        
        context['commentaires'] = conge.commentaires.all()
        context['commentaire_form'] = CommentaireCongeForm()
        context['peut_commenter'] = _user_can_comment_conge(self.request.user, conge)

        user = self.request.user
        context['peut_approuver_directeur'] = (
            conge.statut == 'demande'
            and user_can_approve_conge_directeur(user)
            and _can_directeur_approve_conge(user, conge)
        )
        context['peut_approuver_drh'] = (
            conge.statut == 'approuve_directeur' and user_can_validate_conge_drh(user)
        )
        
        return context

class CongeCreateView(CongeRequestMixin, CreateView):
    """
    Vue pour créer une demande de congé.
    Les agents et professeurs ne peuvent créer que pour eux-mêmes.
    Les informations personnelles sont pré-remplies automatiquement.
    """
    model = Conge
    form_class = CongeAutoForm
    template_name = 'absences/conge_form.html'
    success_url = reverse_lazy('conge-list')

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['current_user'] = self.request.user
        return kwargs
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user

        agent = None
        professeur = None
        etablissement = None

        agent = _resolve_agent_for_user(user)
        professeur = _resolve_professeur_for_user(user)
        if professeur:
            etablissement = professeur.etablissement
        
        context['agent'] = agent
        context['professeur'] = professeur
        context['etablissement'] = etablissement
        context['user_role'] = user.role
        context['user_full_name'] = f"{user.first_name} {user.last_name}".strip() or user.username
        
        return context
    
    def form_valid(self, form):
        user = self.request.user
        conge = form.save(commit=False)
        conge.user_demandeur = user
        # La demande est automatiquement soumise au directeur dès l'enregistrement.
        conge.statut = 'demande'
        
        conge.save()
        self.object = conge
        messages.success(self.request, "✓ Votre demande de congé a été enregistrée et soumise au directeur d'école pour validation.")
        return redirect(self.get_success_url())

class CongeUpdateView(LoginRequiredMixin, UpdateView):
    model = Conge
    form_class = CongeAutoForm
    template_name = 'absences/conge_form.html'
    success_url = reverse_lazy('conge-list')
    
    def get_queryset(self):
        # Seul le demandeur peut éditer sa demande si elle est en statut "demande"
        return Conge.objects.filter(user_demandeur=self.request.user, statut='demande')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        conge = self.object
        context['user_role'] = self.request.user.role
        context['user_full_name'] = self.request.user.get_full_name() or self.request.user.username
        if conge.agent:
            context['agent'] = conge.agent
        elif conge.professeur:
            context['professeur'] = conge.professeur
            context['etablissement'] = conge.professeur.etablissement
        elif conge.etablissement:
            context['etablissement'] = conge.etablissement
        return context

class CongeDeleteView(LoginRequiredMixin, DeleteView):
    model = Conge
    template_name = 'absences/conge_confirm_delete.html'
    success_url = reverse_lazy('conge-list')
    
    def get_queryset(self):
        # Seul le demandeur peut supprimer sa demande si elle est en attente
        return Conge.objects.filter(user_demandeur=self.request.user, statut='demande')


class ApprobationDirecteurView(LoginRequiredMixin, UserPassesTestMixin, View):
    """Vue pour le directeur d'école pour approuver/refuser une demande de congé"""
    
    def test_func(self):
        return user_can_approve_conge_directeur(self.request.user)
    
    def get(self, request, pk):
        conge = get_object_or_404(Conge, pk=pk)
        if conge.statut != 'demande':
            return HttpResponseForbidden("Cette demande ne peut pas être approuvée par le directeur.")
        if not _can_directeur_approve_conge(request.user, conge):
            return HttpResponseForbidden("Vous ne pouvez approuver que les demandes de votre établissement.")
        
        form = ApprobationDirecteurForm()
        return render(request, 'absences/approbation_directeur.html', {
            'conge': conge,
            'form': form,
            'commentaires': conge.commentaires.all(),
        })
    
    def post(self, request, pk):
        conge = get_object_or_404(Conge, pk=pk)
        if conge.statut != 'demande':
            return HttpResponseForbidden("Cette demande ne peut pas être approuvée par le directeur.")
        if not _can_directeur_approve_conge(request.user, conge):
            return HttpResponseForbidden("Vous ne pouvez approuver que les demandes de votre établissement.")
        
        form = ApprobationDirecteurForm(request.POST)
        if form.is_valid():
            action = form.cleaned_data['action']
            commentaire_texte = form.cleaned_data.get('commentaire', '')
            
            if action == 'approuver':
                conge.statut = 'approuve_directeur'
                conge.approuve_directeur_par = request.user
                conge.date_approbation_directeur = timezone.now()
                conge.save()
                status_msg = "La demande a été approuvée par le directeur et sera transmise à la DRH."
            else:
                conge.statut = 'refuse'
                conge.save()
                status_msg = "La demande a été refusée."
            
            # Ajouter un commentaire si fourni
            if commentaire_texte:
                CommentaireConge.objects.create(
                    conge=conge,
                    auteur=request.user,
                    texte=f"[Directeur] {commentaire_texte}"
                )
            
            return redirect('conge-detail', pk=conge.pk)
        
        return render(request, 'absences/approbation_directeur.html', {
            'conge': conge,
            'form': form,
            'commentaires': conge.commentaires.all(),
        })


class ValidationDRHView(LoginRequiredMixin, UserPassesTestMixin, View):
    """Vue pour la DRH pour valider/refuser une demande de congé"""
    
    def test_func(self):
        return user_can_validate_conge_drh(self.request.user)
    
    def get(self, request, pk):
        conge = get_object_or_404(Conge, pk=pk)
        if conge.statut != 'approuve_directeur':
            return HttpResponseForbidden("Cette demande ne peut pas être validée par la DRH.")
        
        form = ApprobationDRHForm()
        return render(request, 'absences/validation_drh.html', {
            'conge': conge,
            'form': form,
            'commentaires': conge.commentaires.all(),
        })
    
    def post(self, request, pk):
        conge = get_object_or_404(Conge, pk=pk)
        if conge.statut != 'approuve_directeur':
            return HttpResponseForbidden("Cette demande ne peut pas être validée par la DRH.")
        
        form = ApprobationDRHForm(request.POST)
        if form.is_valid():
            action = form.cleaned_data['action']
            commentaire_texte = form.cleaned_data.get('commentaire', '')
            
            if action == 'approuver':
                conge.statut = 'approuve_drh'
                conge.approuve_drh_par = request.user
                conge.date_approbation_drh = timezone.now()
                msg = "La demande a été validée par la DRH."
            else:
                conge.statut = 'refuse'
                msg = "La demande a été refusée par la DRH."
            
            conge.save()
            
            # Ajouter un commentaire si fourni
            if commentaire_texte:
                CommentaireConge.objects.create(
                    conge=conge,
                    auteur=request.user,
                    texte=f"[DRH] {commentaire_texte}"
                )
            
            return redirect('conge-detail', pk=conge.pk)
        
        return render(request, 'absences/validation_drh.html', {
            'conge': conge,
            'form': form,
            'commentaires': conge.commentaires.all(),
        })


class AjouterCommentaireView(LoginRequiredMixin, View):
    """Vue pour ajouter un commentaire sur une demande de congé"""
    
    def post(self, request, pk):
        conge = get_object_or_404(Conge, pk=pk)
        if not _user_can_comment_conge(request.user, conge):
            return HttpResponseForbidden("Vous n'avez pas la permission d'ajouter un commentaire sur cette demande.")
        form = CommentaireCongeForm(request.POST)
        
        if form.is_valid():
            commentaire = form.save(commit=False)
            commentaire.conge = conge
            commentaire.auteur = request.user
            commentaire.save()
        
        return redirect('conge-detail', pk=conge.pk)
