from django.shortcuts import render
from apps.agents.models import Agent
from apps.formations.models import Formation, Certificat
from apps.absences.models import Conge
from apps.carrieres.models import Carriere
from apps.comptes.models import User
from apps.organigramme.models import Structure
from collections import Counter
import json

def dashboard(request):

    total_agents = Agent.objects.count()
    total_formations = Formation.objects.count()
    total_conges = Conge.objects.count()
    total_carrieres = Carriere.objects.count()
    total_comptes = User.objects.count()
    total_organigramme = Structure.objects.count()



  # --- Agents par service ---
    agents = Agent.objects.select_related('service').all()
    services = [a.service.nom if a.service else "Non défini" for a in agents]
    agents_par_service = dict(Counter(services))

    service_labels = json.dumps(list(agents_par_service.keys()))
    service_data = json.dumps(list(agents_par_service.values()))

    # --- Organigramme hiérarchique ---
    directions_count = Structure.objects.filter(type_structure='direction').count()
    divisions_count = Structure.objects.filter(type_structure='division').count()
    services_count = Structure.objects.filter(type_structure='service').count()
    sections_count = Structure.objects.filter(type_structure='section').count()

    org_labels = json.dumps(['Directions', 'Divisions', 'Services', 'Sections'])
    org_data = json.dumps([directions_count, divisions_count, services_count, sections_count])




    # Listes récentes pour affichage dans le dashboard
    agents = Agent.objects.all().order_by('-id')[:5]
    formations = Formation.objects.all().order_by('-id')[:5]
    conges = Conge.objects.all().order_by('-id')[:5]
    carrieres = Carriere.objects.all().order_by('-id')[:5]


    context = {
        "total_agents": total_agents,
        "total_formations": total_formations,
        "total_conges": total_conges,
        "total_carrieres": total_carrieres,
        "total_comptes": total_comptes,
        "total_organigramme": total_organigramme,
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


