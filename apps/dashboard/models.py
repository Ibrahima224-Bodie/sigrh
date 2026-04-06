from django.db import models


class DashboardAccess(models.Model):
	class Meta:
		verbose_name = 'accès tableau de bord'
		verbose_name_plural = 'accès tableau de bord'
		default_permissions = ()
		permissions = [
			('access_dashboard', 'Peut accéder au tableau de bord'),
			('view_dashboard_agents_section', 'Peut voir la section Agents du tableau de bord'),
			('view_dashboard_formations_section', 'Peut voir la section Formations du tableau de bord'),
			('view_dashboard_professeurs_section', 'Peut voir la section Enseignants du tableau de bord'),
			('view_dashboard_filieres_section', 'Peut voir la section Filières du tableau de bord'),
			('view_dashboard_programmes_section', 'Peut voir la section Programmes du tableau de bord'),
			('view_dashboard_modules_section', 'Peut voir la section Modules du tableau de bord'),
			('view_dashboard_etablissements_section', 'Peut voir la section Etablissements du tableau de bord'),
			('view_dashboard_conges_section', 'Peut voir la section Congés du tableau de bord'),
			('view_dashboard_carrieres_section', 'Peut voir la section Carrières du tableau de bord'),
		]
