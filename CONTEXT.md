# MATHutrice

Tuteur pédagogique fondé sur un LLM qui aide les étudiants de première année de l'EPF à travailler les outils mathématiques par notions, compétences et entraînement.

## Langage

### Authentification

**Connexion de développement** (`AUTH_MODE=dev`) :
Connexion sans fournisseur d'identité : on choisit une adresse mail et un rôle (Student, Teacher ou Admin), et on est connecté ainsi, sans preuve d'identité. Elle ne dépend d'aucun utilisateur pré-existant. Elle n'existe que lorsque `AUTH_MODE=dev` et ne doit jamais servir en production.
_À éviter_ : impersonation, usurpation, fake login

**Impersonation** :
Un Admin réellement authentifié consulte l'application en tant qu'un autre utilisateur, puis revient à son propre compte. Elle suppose une vraie connexion derrière, contrairement à la connexion de développement.
_À éviter_ : connexion de développement, dev login
