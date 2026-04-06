ACTION_LABELS_FR = {
    "add": "Ajouter",
    "change": "Modifier",
    "delete": "Supprimer",
    "view": "Consulter",
}

CUSTOM_PERMISSION_LABELS_FR = {
    "demander_conge": "Demander un congé",
    "approuver_conge_directeur": "Approuver un congé au niveau directeur",
    "valider_conge_drh": "Valider un congé au niveau DRH",
    "access_dashboard": "Accès général au tableau de bord",
    "view_dashboard_agents_section": "Voir la section Agents du tableau de bord",
    "view_dashboard_formations_section": "Voir la section Formations du tableau de bord",
    "view_dashboard_professeurs_section": "Voir la section Enseignants du tableau de bord",
    "view_dashboard_filieres_section": "Voir la section Filières du tableau de bord",
    "view_dashboard_programmes_section": "Voir la section Programmes du tableau de bord",
    "view_dashboard_modules_section": "Voir la section Modules du tableau de bord",
    "view_dashboard_etablissements_section": "Voir la section Etablissements du tableau de bord",
    "view_dashboard_conges_section": "Voir la section Congés du tableau de bord",
    "view_dashboard_carrieres_section": "Voir la section Carrières du tableau de bord",
    "use_ai_assistant": "Utiliser l'assistant IA",
    "toggle_user_activation": "Activer ou désactiver un utilisateur",
    "manage_role_permissions": "Gérer les permissions des rôles",
    "commenter_conge": "Commenter une demande de congé",
    "view_besoin": "Consulter les besoins d'enseignement",
    "view_besoin_suggestions": "Consulter les suggestions de besoins",
    "export_csv_template": "Télécharger les modèles CSV",
    "export_csv_data": "Exporter les données CSV",
    "import_csv_data": "Importer des données CSV",
    "access_geo_filters": "Utiliser les filtres géographiques",
    "filter_filieres_by_etablissement": "Filtrer les filières par établissement",
    "filter_modules_by_filiere": "Filtrer les modules par filière",
    "preview_affectation": "Prévisualiser une affectation",
    "csv_regions": "Import / Export CSV Régions",
    "csv_prefectures": "Import / Export CSV Préfectures",
    "csv_communes": "Import / Export CSV Communes",
    "csv_quartiers": "Import / Export CSV Quartiers",
    "csv_secteurs": "Import / Export CSV Secteurs",
    "csv_programmes": "Import / Export CSV Programmes",
    "csv_modules": "Import / Export CSV Modules",
    "csv_professeurs": "Import / Export CSV Professeurs",
}


def get_model_label_fr(content_type):
    model_class = content_type.model_class()
    if model_class is not None:
        return str(model_class._meta.verbose_name)
    return content_type.model.replace("_", " ")


def get_permission_label_fr(permission):
    codename = permission.codename or ""
    if codename in CUSTOM_PERMISSION_LABELS_FR:
        app_label = permission.content_type.app_label
        return f"{CUSTOM_PERMISSION_LABELS_FR[codename]} [{app_label}]"

    if "_" in codename:
        action_code = codename.split("_", 1)[0]
        action_label = ACTION_LABELS_FR.get(action_code)
        if action_label:
            model_label = get_model_label_fr(permission.content_type)
            app_label = permission.content_type.app_label
            return f"{action_label} {model_label} [{app_label}]"

    app_label = permission.content_type.app_label
    model_label = get_model_label_fr(permission.content_type)
    return f"{permission.name} [{app_label}.{model_label}]"