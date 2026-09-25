"""
seed.py — Données de démarrage d'une base vide

`seed_if_empty` est appelée au démarrage de l'application : si la base ne
contient encore ni notion ni utilisateur, elle y insère le référentiel
(notions et compétences) et un utilisateur par rôle. Sinon, elle ne fait rien.
"""

import uuid
from datetime import datetime

from sqlmodel import Session, select

from mathutrice import models
from mathutrice.fonctions_python.main import REFERENTIEL

# Description de chaque notion du REFERENTIEL, par clé.
NOTION_DESCRIPTIONS = {
    "trigonometrie": "Étude des fonctions trigonométriques, des angles et du cercle trigonométrique.",
    "fractions_puissances_radicaux": "Manipulation des fractions, puissances et radicaux.",
    "logarithme_exponentielle": "Étude des fonctions logarithme et exponentielle.",
    "manipulation_expressions_litterales": "Isolement et manipulation de variables dans des expressions algébriques.",
    "equations_inequations": "Résolution d'équations et d'inéquations du premier et second degré.",
    "polynomes_factorisation": "Étude des polynômes, factorisation et identités remarquables.",
    "analyse_dimensionnelle": "Dimensions, unités et homogénéité des formules physiques.",
}

# (email, nom, rôle) : élève en @epfedu.fr, enseignant et admin en @epf.fr.
SEED_USERS = [
    ("student@epfedu.fr", "Student Demo", "Student"),
    ("teacher@epf.fr", "Teacher Demo", "Teacher"),
    ("admin@epf.fr", "Admin Demo", "Admin"),
]


def seed_if_empty(session: Session) -> bool:
    """
    Insère le référentiel et un utilisateur par rôle si la base est vide.

    La base est vide quand elle ne contient ni notion ni utilisateur.
    Retourne True si des données ont été insérées, False sinon.
    """
    has_notion = session.exec(select(models.Notion.notion_id)).first() is not None
    has_user = session.exec(select(models.User.sso_id)).first() is not None

    if has_notion or has_user:
        return False

    for notion_key, notion_data in REFERENTIEL.items():
        notion = models.Notion(
            notion_id=uuid.uuid4(),
            referentiel_key=notion_key,
            title=notion_data["notion_nom"],
            description=NOTION_DESCRIPTIONS[notion_key],
        )
        session.add(notion)

        for comp in notion_data["competences"]:
            session.add(
                models.Competence(
                    competence_id=uuid.uuid4(),
                    referentiel_code=comp["code"],
                    title=comp["nom"],
                    level=comp["niveau"],
                    notion_id=notion.notion_id,
                )
            )

    now = datetime.utcnow()

    for email, name, role in SEED_USERS:
        session.add(
            models.User(
                sso_id=uuid.uuid4(),
                created_at=now,
                last_active=now,
                role=role,
                email=email,
                name=name,
            )
        )

    session.commit()
    return True
