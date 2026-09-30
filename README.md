# EPSI Bot Discord (v2.0)

Un bot Discord moderne et réactif pour consulter votre emploi du temps EPSI directement depuis Discord grâce au flux officiel iCal Hyperplanning.

[![Inviter le bot](https://img.shields.io/badge/Inviter%20le%20bot-Discord-7289DA?style=for-the-badge&logo=discord&logoColor=white)](https://discord.com/oauth2/authorize?client_id=1357424188306227451)

---

## ✨ Nouveautés & Fonctionnalités v2.0

- 🌐 **Interface Web & PWA intégrée (FastAPI)** : portail web responsive servi en parallèle du bot, avec mode hors-ligne, thèmes clair/sombre, sélecteur de semaine et grille horaire dynamique.
- 🔐 **Connexion Discord OAuth2** : connectez-vous directement sur le site web pour modifier votre lien iCal, basculer vos notifications et synchroniser vos préférences avec Discord en un clic.
- 🇫🇷 🇬🇧 **Bilingue complet (Français / Anglais)** : bot et site web entièrement traduits avec bascule dynamique dans les paramètres.
- 🎆 **Jours fériés légaux & Jours en entreprise (Alternance)** :
  - Détection automatique des 11 jours fériés français via l'API officielle de l'État (`api.gouv.fr`) avec calcul local Meeus de secours.
  - Génération automatique des journées en entreprise (09h00 - 17h00) sur les jours de semaine sans cours.
  - Option d'activation/désactivation configurable via `/settings work_days` ou dans le modal de paramètres du site web.
- 💾 **Double persistance Locale & PostgreSQL** : les utilisateurs invités peuvent sauvegarder leur URL dans leur navigateur (localStorage) sans connexion, tandis que les utilisateurs connectés synchronisent directement avec la base de données PostgreSQL / SQLite.
- 🔗 **Support direct des flux iCal Hyperplanning** : synchronisation en temps réel avec cache intelligent (5 min).
- 🖼️ **Génération d'images moderne et légère (Pillow)** : grille horaire proportionnelle (08h00 - 19h00) fidèle à l'interface Hyperplanning, cartes au thème sombre Discord épurées, typographie Roboto avec support complet des accents français. Suppression totale des dépendances C lourdes (Cairo).
- 🔘 **Composants interactifs Discord** : boutons *Jour précédent*, *Jour suivant*, *Semaine précédente/suivante* et bascule directe *Image / Embed*.
- ⏱️ **Commande `/now`** : aperçu instantané du cours en cours (ou journée en entreprise/fériée) et des 4 prochains cours avec liens directs visio Teams si disponibles.
- 🗄️ **Base de données polyvalente (SQLModel & SQLAlchemy Async)** : support de PostgreSQL ou repli automatique sur SQLite local sans aucune configuration externe requise.
- ⏰ **Rappels automatiques (Cron jobs)** :
  - **Quotidien** : envoi en message privé chaque matin à 06h00.
  - **Hebdomadaire** : envoi en message privé chaque lundi matin à 06h00.
- ⚡ **Stack ultra-rapide** : packagé et géré avec `uv`, typé avec `ty`, formaté et analysé avec `ruff`.

---

## 🚀 Commandes Slash

### `/settings` — Configurer votre compte
- `register` : Enregistrer votre URL d'export iCal Hyperplanning (ex: `https://...hyperplanning.fr/hp/...Edt.ics?...`).
- `daily` : Activer ou désactiver les rappels quotidiens à 06:00.
- `weekly` : Activer ou désactiver le récapitulatif hebdomadaire le lundi à 06:00.
- `work_days` : Activer ou désactiver l'affichage des journées en entreprise (Alternance) lors des jours sans cours.
- `default_format` : Choisir entre format visuel *Image* ou *Embed texte*.
- `language` : Choisir la langue du bot (*Français* ou *English*).
- `unregister` : Supprimer vos données et votre lien enregistré.

### `/day` — Emploi du temps du jour
- Affiche le planning de la journée sélectionnée (par défaut : aujourd'hui).
- Inclut des boutons interactifs pour feuilleter les jours.
- Options : `date` (format `JJ/MM/AAAA`), `image` (True/False), `url` (pour une consultation ponctuelle sans être enregistré).

### `/week` — Emploi du temps de la semaine
- Affiche un planning complet de 5 jours (du lundi au vendredi).
- Inclut des boutons interactifs pour naviguer de semaine en semaine.
- Options : `date` (format `JJ/MM/AAAA`), `image` (True/False), `url`.

### `/now` — Cours en cours et suivants
- Indique immédiatement si un cours a lieu en ce moment (avec la salle, l'intervenant et le lien Teams éventuel) ainsi que les prochains cours à venir.

---

## 🛠️ Développement & Qualité de code

### Prérequis
- Python 3.11+
- [uv](https://docs.astral.sh/uv/) installé

### Commandes utiles

```bash
# Installer les dépendances
uv sync

# Lancer la suite de tests unitaires
uv run pytest

# Vérifier et formater le code avec ruff
uv run ruff check . --fix
uv run ruff format .

# Vérification des types
uv run ty check src

# Lancer le bot
uv run python src/main.py
```

---

## 🐳 Déploiement Docker

Le projet dispose d'un `Dockerfile` multi-stage optimisé avec `uv` :

```bash
docker build -t epsi-bot .
docker run -d -p 8080:8080 --env-file .env --name epsi-bot epsi-bot
```