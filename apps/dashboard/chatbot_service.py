import json
import os
import re
import unicodedata
from datetime import datetime
from urllib import error, request
from django.db.models import Q, Sum
from django.conf import settings

from apps.absences.models import Conge
from apps.agents.models import Agent
from apps.carrieres.models import Carriere
from apps.comptes.models import User
from apps.enseignants.models import Affectation, Etablissement, Filiere, Module, Programme, Professeur
from apps.formations.models import Formation


def _normalize_text(value):
    text = (value or "").strip().lower()
    if not text:
        return ""
    normalized = unicodedata.normalize("NFKD", text)
    return "".join(ch for ch in normalized if not unicodedata.combining(ch))


def _tokenize(value):
    return re.findall(r"[a-z0-9]+", _normalize_text(value))


def _find_etablissement_from_question(question_normalized):
    etabs = list(Etablissement.objects.values("id", "nom"))
    if not etabs:
        return None

    stopwords = {
        "de", "du", "des", "la", "le", "les", "a", "au", "aux", "dans",
        "pour", "sur", "et", "en", "d", "l", "il", "y", "combien"
    }
    question_tokens = set(t for t in _tokenize(question_normalized) if t not in stopwords)

    best = None
    best_score = 0.0
    for etab in etabs:
        etab_norm = _normalize_text(etab["nom"])
        if etab_norm and etab_norm in question_normalized:
            return etab

        etab_tokens = [t for t in _tokenize(etab["nom"]) if t not in stopwords]
        if not etab_tokens:
            continue
        inter = len(question_tokens.intersection(etab_tokens))
        score = inter / len(set(etab_tokens))
        if score > best_score:
            best_score = score
            best = etab

    if best and best_score >= 0.5:
        return best
    return None


def _modules_taught_queryset(etablissement_id):
    return Module.objects.filter(
        Q(affectations__actif=True, affectations__etablissement_id=etablissement_id)
        | Q(affectations__actif=True, affectations__filiere__etablissements__id=etablissement_id)
        | Q(affectations__actif=True, affectations__filiere__etablissement_id=etablissement_id)
    ).distinct()


def _modules_expected_queryset(etablissement_id):
    return Module.objects.filter(
        Q(programmes_principaux__filiere__etablissements__id=etablissement_id)
        | Q(programmes_principaux__filiere__etablissement_id=etablissement_id)
    ).distinct()


def _count_modules_taught_in_etablissement(etablissement_id):
    return _modules_taught_queryset(etablissement_id).count()


def _build_data_snapshot():
    return {
        "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "counts": {
            "agents": Agent.objects.count(),
            "formations": Formation.objects.count(),
            "conges": Conge.objects.count(),
            "carrieres": Carriere.objects.count(),
            "utilisateurs": User.objects.count(),
            "professeurs": Professeur.objects.count(),
            "etablissements": Etablissement.objects.count(),
            "filieres": Filiere.objects.count(),
            "programmes": Programme.objects.count(),
            "modules": Module.objects.count(),
        },
        "recent": {
            "agents": list(Agent.objects.order_by("-id").values_list("nom", "prenom")[:5]),
            "etablissements": list(Etablissement.objects.order_by("nom").values_list("nom", flat=True)[:8]),
            "filieres": list(Filiere.objects.order_by("nom").values_list("nom", flat=True)[:8]),
            "modules": list(Module.objects.order_by("nom").values_list("nom", flat=True)[:8]),
            "programmes": list(Programme.objects.order_by("nom").values_list("nom", flat=True)[:8]),
        },
    }


def _simple_local_answer(question, snapshot):
    q = (question or "").strip().lower()
    q_norm = _normalize_text(q)
    counts = snapshot["counts"]

    matched_etab = _find_etablissement_from_question(q_norm)
    if matched_etab:
        etab_id = matched_etab["id"]
        etab_nom = matched_etab["nom"]

        asks_teacher = bool(re.search(r"enseignant|enseignants|professeur|professeurs", q_norm))
        asks_module = bool(re.search(r"module|modules|modul", q_norm))
        asks_taught = bool(re.search(r"enseigne|enseignes|enseigner|enseignee|donne|dispense", q_norm))
        asks_filiere = bool(re.search(r"filiere|filieres", q_norm))
        asks_programme = bool(re.search(r"programme|programmes", q_norm))
        asks_count = bool(re.search(r"combien|nombre|total", q_norm))
        asks_list = bool(re.search(r"liste|quels|quelles|lesquels|lesquelles|qui", q_norm))
        asks_not_taught = bool(re.search(r"non enseigne|pas enseigne|restant|restants|reste", q_norm))
        asks_hours = bool(re.search(r"heure|heures", q_norm))

        if asks_module and asks_not_taught:
            expected_qs = _modules_expected_queryset(etab_id)
            taught_ids = _modules_taught_queryset(etab_id).values_list("id", flat=True)
            remaining_qs = expected_qs.exclude(id__in=taught_ids)
            remaining_count = remaining_qs.count()
            examples = list(remaining_qs.order_by("nom").values_list("nom", flat=True)[:10])
            detail = f" Exemples: {', '.join(examples)}." if examples else ""
            return f"Il reste {remaining_count} module(s) non enseigne(s) a {etab_nom}.{detail}"

        if asks_module and asks_list:
            modules_names = list(
                _modules_taught_queryset(etab_id).order_by("nom").values_list("nom", flat=True)[:30]
            )
            if not modules_names:
                return f"Aucun module enseigne n'a ete trouve a {etab_nom}."
            return f"Modules enseignes a {etab_nom}: {', '.join(modules_names)}."

        if asks_module and (asks_taught or asks_count):
            total_modules = _count_modules_taught_in_etablissement(etab_id)
            modules_names = list(
                _modules_taught_queryset(etab_id)
                .order_by("nom")
                .values_list("nom", flat=True)[:10]
            )
            detail = f" Exemples: {', '.join(modules_names)}." if modules_names else ""
            return f"Il y a actuellement {total_modules} module(s) enseigne(s) a {etab_nom}.{detail}"

        if asks_hours and asks_module:
            total_hours = (
                Affectation.objects.filter(
                    actif=True,
                ).filter(
                    Q(etablissement_id=etab_id)
                    | Q(filiere__etablissements__id=etab_id)
                    | Q(filiere__etablissement_id=etab_id)
                ).aggregate(total=Sum("heures_affectees"))["total"]
            ) or 0
            return f"Le volume horaire affecte sur les modules a {etab_nom} est de {total_hours} heure(s)."

        if asks_teacher:
            total_local = Professeur.objects.filter(etablissement_id=etab_id).count()
            noms = list(
                Professeur.objects.filter(etablissement_id=etab_id)
                .order_by("nom", "prenom")
                .values_list("prenom", "nom")[:10]
            )
            detail = f" Professeurs: {', '.join(f'{p} {n}' for p, n in noms)}." if noms else ""
            return f"Il y a actuellement {total_local} professeur(s) a {etab_nom}.{detail}"

        if asks_filiere:
            total_filieres = Filiere.objects.filter(
                Q(etablissements__id=etab_id) | Q(etablissement_id=etab_id)
            ).distinct().count()
            return f"Il y a actuellement {total_filieres} filiere(s) a {etab_nom}."

        if asks_programme:
            total_programmes = Programme.objects.filter(
                Q(filiere__etablissements__id=etab_id) | Q(filiere__etablissement_id=etab_id)
            ).distinct().count()
            return f"Il y a actuellement {total_programmes} programme(s) a {etab_nom}."

        if asks_count:
            total_professeurs = Professeur.objects.filter(etablissement_id=etab_id).count()
            total_filieres = Filiere.objects.filter(
                Q(etablissements__id=etab_id) | Q(etablissement_id=etab_id)
            ).distinct().count()
            total_programmes = Programme.objects.filter(
                Q(filiere__etablissements__id=etab_id) | Q(filiere__etablissement_id=etab_id)
            ).distinct().count()
            total_modules = _count_modules_taught_in_etablissement(etab_id)
            return (
                f"Pour {etab_nom}: {total_professeurs} professeur(s), {total_filieres} filiere(s), "
                f"{total_programmes} programme(s), {total_modules} module(s) enseigne(s)."
            )

    keyword_map = [
        ("etablissement|ecole|ecoles", "etablissements", "etablissements"),
        ("filiere|filieres", "filieres", "filieres"),
        ("module|modules", "modules", "modules"),
        ("programme|programmes", "programmes", "programmes"),
        ("professeur|professeurs|enseignant|enseignants", "professeurs", "professeurs"),
        ("agent|agents", "agents", "agents"),
        ("formation|formations", "formations", "formations"),
        ("conge|conges", "conges", "conges"),
        ("carriere|carrieres", "carrieres", "carrieres"),
        ("compte|comptes|utilisateur|utilisateurs", "utilisateurs", "utilisateurs"),
    ]

    for pattern, count_key, list_key in keyword_map:
        if re.search(pattern, q):
            items = snapshot["recent"].get(list_key) or []
            if items and isinstance(items[0], tuple):
                preview = ", ".join(f"{nom} {prenom}" for nom, prenom in items)
            else:
                preview = ", ".join(items)
            details = f" Exemples: {preview}." if preview else ""
            return f"Il y a actuellement {counts[count_key]} {count_key}.{details}"

    return (
        "Je n'ai pas pu deduire exactement l'entite demandee. Essayez avec une formulation plus explicite "
        "(ex: combien de modules enseignes a ERAM de Labe)."
    )


def _ask_remote_llm(question, snapshot):
    enable_remote = bool(getattr(settings, "SIGRH_CHATBOT_ENABLE_REMOTE", True))
    if not enable_remote:
        return None

    api_key = (getattr(settings, "OPENAI_API_KEY", "") or os.environ.get("OPENAI_API_KEY", "")).strip()
    if not api_key:
        return None

    payload = {
        "model": getattr(settings, "SIGRH_CHATBOT_MODEL", os.environ.get("SIGRH_CHATBOT_MODEL", "gpt-4o-mini")),
        "messages": [
            {
                "role": "system",
                "content": (
                    "Tu es un assistant SIGRH. Reponds en francais, de maniere concise et factuelle, "
                    "uniquement a partir des donnees fournies. Si une question est complexe, calcule et explique les chiffres "
                    "sans inventer. Si la question depasse les donnees, dis-le clairement."
                ),
            },
            {
                "role": "user",
                "content": (
                    f"Question utilisateur: {question}\n"
                    f"Donnees SIGRH (JSON): {json.dumps(snapshot, ensure_ascii=True)}"
                ),
            },
        ],
        "temperature": 0.2,
    }
    data = json.dumps(payload).encode("utf-8")

    req = request.Request(
        "https://api.openai.com/v1/chat/completions",
        data=data,
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}",
        },
        method="POST",
    )
    try:
        with request.urlopen(req, timeout=20) as resp:
            body = json.loads(resp.read().decode("utf-8"))
        return body["choices"][0]["message"]["content"].strip()
    except (error.URLError, error.HTTPError, KeyError, IndexError, ValueError, TimeoutError):
        return None


def answer_question(question):
    snapshot = _build_data_snapshot()
    remote_answer = _ask_remote_llm(question, snapshot)
    if remote_answer:
        return remote_answer
    return _simple_local_answer(question, snapshot)
