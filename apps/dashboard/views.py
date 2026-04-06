import json
import re
import unicodedata
from collections import Counter

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Count
from django.http import JsonResponse
from django.shortcuts import redirect, render
from django.urls import NoReverseMatch, reverse
from django.views.decorators.http import require_POST

from apps.absences.models import Conge
from apps.agents.models import Agent
from apps.carrieres.models import Carriere
from apps.comptes.permissions import user_has_any_permission
from apps.enseignants.models import Etablissement, Filiere, Module, Programme, Professeur
from apps.formations.models import Formation

from .chatbot_service import answer_question


DASHBOARD_ACCESS_PERMISSION = "dashboard.access_dashboard"
AI_ASSISTANT_PERMISSION = "assistant_ia.use_ai_assistant"


def _normalize_text(value):
  text = (value or "").strip().lower()
  normalized = unicodedata.normalize("NFKD", text)
  return "".join(ch for ch in normalized if not unicodedata.combining(ch))


def _detect_navigation_action(question, user):
  q = _normalize_text(question)

  asks_navigation = bool(re.search(r"\b(ouvre|ouvrir|affiche|afficher|va|aller|navigue|naviguer|redirige|rediriger|montre|liste)\b", q))
  asks_list_style = bool(re.search(r"\bliste\s+(des|de|du|d)\b", q))
  if not asks_navigation and not asks_list_style:
    return None

  targets = [
    {"pattern": r"dashboard|tableau de bord|accueil", "url_name": "dashboard", "label": "le tableau de bord", "perm": None},
    {"pattern": r"agents?", "url_name": "agent-list", "label": "la liste des agents", "perm": "agents.view_agent"},
    {"pattern": r"conge|conges", "url_name": "conge-list", "label": "la liste des conges", "perm": "absences.view_conge"},
    {"pattern": r"carriere|carrieres", "url_name": "carriere-list", "label": "la liste des carrieres", "perm": "carrieres.view_carriere"},
    {"pattern": r"formation|formations", "url_name": "formation-list", "label": "la liste des formations", "perm": "formations.view_formation"},
    {"pattern": r"certificat|certificats", "url_name": "certificat-list", "label": "la liste des certificats", "perm": "formations.view_certificat"},
    {"pattern": r"direction|directions", "url_name": "direction-list", "label": "la liste des directions", "perm": "directions.view_direction"},
    {"pattern": r"organigramme|structure|structures", "url_name": "structure-list", "label": "la liste de l'organigramme", "perm": "organigramme.view_structure"},
    {"pattern": r"utilisateur|utilisateurs|comptes?|users?", "url_name": "user-list", "label": "la liste des utilisateurs", "perm": "comptes.view_user"},
    {"pattern": r"roles?|role", "url_name": "role-list", "label": "la liste des roles", "perm": "auth.view_group"},
    {"pattern": r"permissions?", "url_name": "permission-list", "label": "la liste des permissions", "perm": "auth.view_permission"},
    {"pattern": r"professeur|professeurs|enseignant|enseignants", "url_name": "enseignants:professeur_list", "label": "la liste des professeurs", "perm": "enseignants.view_professeur"},
    {"pattern": r"affectation|affectations", "url_name": "enseignants:affectation_list", "label": "la liste des affectations", "perm": "enseignants.view_affectation"},
    {"pattern": r"besoin|besoins", "url_name": "enseignants:besoin_list", "label": "la liste des besoins", "perm": "enseignants.view_module"},
    {"pattern": r"module|modules|modul", "url_name": "enseignants:module_list", "label": "la liste des modules", "perm": "enseignants.view_module"},
    {"pattern": r"programme|programmes", "url_name": "enseignants:programme_list", "label": "la liste des programmes", "perm": "enseignants.view_programme"},
    {"pattern": r"filiere|filieres", "url_name": "enseignants:filiere_list", "label": "la liste des filieres", "perm": "enseignants.view_filiere"},
    {"pattern": r"etablissement|etablissements|ecole|ecoles", "url_name": "enseignants:etablissement_list", "label": "la liste des etablissements", "perm": "enseignants.view_etablissement"},
    {"pattern": r"region|regions", "url_name": "enseignants:region_list", "label": "la liste des regions", "perm": "enseignants.view_region"},
    {"pattern": r"prefecture|prefectures", "url_name": "enseignants:prefecture_list", "label": "la liste des prefectures", "perm": "enseignants.view_prefecture"},
    {"pattern": r"commune|communes", "url_name": "enseignants:commune_list", "label": "la liste des communes", "perm": "enseignants.view_commune"},
    {"pattern": r"quartier|quartiers", "url_name": "enseignants:quartier_list", "label": "la liste des quartiers", "perm": "enseignants.view_quartier"},
    {"pattern": r"secteur|secteurs", "url_name": "enseignants:secteur_list", "label": "la liste des secteurs", "perm": "enseignants.view_secteur"},
  ]

  for target in targets:
    if not re.search(target["pattern"], q):
      continue

    required_perm = target.get("perm")
    if required_perm and not (user.is_superuser or user.has_perm(required_perm)):
      return {
        "type": "permission_denied",
        "label": target["label"],
      }

    try:
      url = reverse(target["url_name"])
    except NoReverseMatch:
      return None

    return {
      "type": "navigate",
      "url": url,
      "label": target["label"],
    }

  return None


def _can_view(user, *permissions):
  return user_has_any_permission(user, permissions)


@login_required
def dashboard(request):
  if not user_has_any_permission(request.user, [DASHBOARD_ACCESS_PERMISSION]):
    messages.error(request, "Vous n'avez pas la permission d'accéder au tableau de bord.")
    return redirect("profile")

  can_view_agents = _can_view(request.user, "dashboard.view_dashboard_agents_section")
  can_view_formations = _can_view(request.user, "dashboard.view_dashboard_formations_section")
  can_view_conges = _can_view(request.user, "dashboard.view_dashboard_conges_section")
  can_view_carrieres = _can_view(request.user, "dashboard.view_dashboard_carrieres_section")
  can_view_professeurs = _can_view(request.user, "dashboard.view_dashboard_professeurs_section")
  can_view_filieres = _can_view(request.user, "dashboard.view_dashboard_filieres_section")
  can_view_programmes = _can_view(request.user, "dashboard.view_dashboard_programmes_section")
  can_view_modules = _can_view(request.user, "dashboard.view_dashboard_modules_section")
  can_view_etablissements = _can_view(request.user, "dashboard.view_dashboard_etablissements_section")

  can_view_any_dashboard_section = any([
    can_view_agents,
    can_view_formations,
    can_view_conges,
    can_view_carrieres,
    can_view_professeurs,
    can_view_filieres,
    can_view_programmes,
    can_view_modules,
    can_view_etablissements,
  ])

  total_agents = Agent.objects.count() if can_view_agents else None
  total_formations = Formation.objects.count() if can_view_formations else None
  total_filieres = Filiere.objects.count() if can_view_filieres else None
  total_programmes = Programme.objects.count() if can_view_programmes else None
  total_modules = Module.objects.count() if can_view_modules else None
  total_etablissements = Etablissement.objects.count() if can_view_etablissements else None
  total_professeurs = Professeur.objects.count() if can_view_professeurs else None

  service_labels = json.dumps([])
  service_data = json.dumps([])
  if can_view_agents:
    agents_for_chart = Agent.objects.select_related("service").all()
    services = [a.service.nom if a.service else "Non défini" for a in agents_for_chart]
    agents_par_service = dict(Counter(services))
    service_labels = json.dumps(list(agents_par_service.keys()))
    service_data = json.dumps(list(agents_par_service.values()))

  org_labels = json.dumps([])
  org_data = json.dumps([])
  if can_view_etablissements:
    etabs_par_region = (
      Etablissement.objects.select_related("region")
      .values("region__nom")
      .annotate(total=Count("id"))
      .order_by("region__nom")
    )
    org_labels = json.dumps([
      row["region__nom"] if row["region__nom"] else "Non defini"
      for row in etabs_par_region
    ])
    org_data = json.dumps([row["total"] for row in etabs_par_region])

  agents = Agent.objects.all().order_by("-id")[:5] if can_view_agents else []
  formations = Formation.objects.all().order_by("-id")[:5] if can_view_formations else []
  conges = Conge.objects.select_related("agent", "professeur").order_by("-id")[:5] if can_view_conges else []
  carrieres = Carriere.objects.select_related("agent").order_by("-id")[:5] if can_view_carrieres else []

  context = {
    "can_view_any_dashboard_section": can_view_any_dashboard_section,
    "can_view_agents": can_view_agents,
    "can_view_formations": can_view_formations,
    "can_view_conges": can_view_conges,
    "can_view_carrieres": can_view_carrieres,
    "can_view_professeurs": can_view_professeurs,
    "can_view_filieres": can_view_filieres,
    "can_view_programmes": can_view_programmes,
    "can_view_modules": can_view_modules,
    "can_view_etablissements": can_view_etablissements,
    "total_agents": total_agents,
    "total_formations": total_formations,
    "total_filieres": total_filieres,
    "total_programmes": total_programmes,
    "total_modules": total_modules,
    "total_etablissements": total_etablissements,
    "total_professeurs": total_professeurs,
    "agents": agents,
    "formations": formations,
    "conges": conges,
    "carrieres": carrieres,
    "service_labels": service_labels,
    "service_data": service_data,
    "org_labels": org_labels,
    "org_data": org_data,
  }
  return render(request, "dashboard/dashboard.html", context)


@login_required
@require_POST
def chatbot_query(request):
  if not user_has_any_permission(request.user, [AI_ASSISTANT_PERMISSION]):
    return JsonResponse({"ok": False, "error": "Vous n'avez pas la permission d'utiliser l'assistant."}, status=403)

  try:
    payload = json.loads(request.body.decode("utf-8")) if request.body else {}
  except json.JSONDecodeError:
    return JsonResponse({"ok": False, "error": "JSON invalide."}, status=400)

  question = (payload.get("question") or "").strip()
  if not question:
    return JsonResponse({"ok": False, "error": "Question vide."}, status=400)

  action = _detect_navigation_action(question, request.user)
  if action and action.get("type") == "permission_denied":
    return JsonResponse({
      "ok": True,
      "answer": f"Je ne peux pas ouvrir {action['label']} car vous n'avez pas les droits requis.",
      "action": None,
    })
  if action and action.get("type") == "navigate":
    return JsonResponse({
      "ok": True,
      "answer": f"D'accord, j'ouvre {action['label']}.",
      "action": action,
    })

  answer = answer_question(question)
  return JsonResponse({"ok": True, "answer": answer, "action": None})


