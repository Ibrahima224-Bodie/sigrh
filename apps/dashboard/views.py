from django.shortcuts import render
from apps.agents.models import Agent
from apps.formations.models import Formation, Certificat
from apps.absences.models import Conge
from apps.carrieres.models import Carriere
from apps.comptes.models import User
from apps.organigramme.models import Structure

def dashboard(request):

    total_agents = Agent.objects.count()
    total_formations = Formation.objects.count()
    total_conges = Conge.objects.count()
    total_carrieres = Carriere.objects.count()
    total_comptes = User.objects.count()
    total_organigramme = Structure.objects.count()

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
    }

    return render(request, "dashboard/dashboard.html", context)


