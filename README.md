# EPSI Bot

[![Python](https://img.shields.io/badge/Python-3.11+-3776AB?style=flat-square&logo=python&logoColor=white)](https://www.python.org/) [![Package Manager](https://img.shields.io/badge/uv-astral-DE5FE9?style=flat-square)](https://docs.astral.sh/uv/) [![Docker](https://img.shields.io/badge/Docker-Multi--arch-2496ED?style=flat-square&logo=docker&logoColor=white)](https://github.com/enzomtpYT/EPSI-Bot/pkgs/container/epsi-bot) [![CI](https://img.shields.io/badge/CI-Automated-success?style=flat-square&logo=githubactions&logoColor=white)](https://github.com/enzomtpYT/EPSI-Bot/actions)

EPSI Bot est une application combinant un bot Discord et un portail web moderne (FastAPI / PWA) pour consulter et partager en temps réel les emplois du temps de l'école EPSI via le flux iCal officiel d'Hyperplanning.

---

## Sommaire

- [EPSI Bot](#epsi-bot)
  - [Sommaire](#sommaire)
  - [Fonctionnalités](#fonctionnalités)
  - [Commandes Discord](#commandes-discord)
    - [`/day` et `/daily`](#day-et-daily)
    - [`/week` et `/weekly`](#week-et-weekly)
    - [`/now`](#now)
    - [`/settings`](#settings)
    - [`/share`](#share)
  - [Portail Web \& PWA](#portail-web--pwa)
  - [Choix techniques et architecture](#choix-techniques-et-architecture)
  - [Guide d'installation et auto-hébergement](#guide-dinstallation-et-auto-hébergement)
    - [1. Configuration Discord Developer Portal](#1-configuration-discord-developer-portal)
    - [2. Variables d'environnement](#2-variables-denvironnement)
    - [3. Démarrage local avec uv](#3-démarrage-local-avec-uv)
    - [4. Déploiement Docker \& Docker Compose](#4-déploiement-docker--docker-compose)
      - [Option A : Image Docker autonome](#option-a--image-docker-autonome)
      - [Option B : Docker Compose (avec PostgreSQL)](#option-b--docker-compose-avec-postgresql)
  - [Qualité de code et tests](#qualité-de-code-et-tests)

---

## Fonctionnalités

- **Synchronisation Hyperplanning automatique** : intégration directe des flux iCal avec cache en mémoire pour un temps de réponse instantané.
- **Rendu graphique fidèle (Pillow)** : génération d'images de planning quotidiennes et hebdomadaires à échelle proportionnelle calquée sur le portail officiel d'EPSI.
- **Support des fuseaux horaires (IANA)** : conversion automatique vers n'importe quel fuseau horaire mondial (`America/New_York`, `Asia/Tokyo`, etc.) avec adaptation dynamique des bornes horaires de la grille.
- **Partage sécurisé** : partage d'emploi du temps par lien web tokenisé ou par liste blanche d'utilisateurs Discord. Masquage strict des liens Microsoft Teams pour les tiers.
- **Jours fériés et alternance** : injection automatique des jours fériés légaux français et génération des journées en entreprise sur les jours ouvrés sans cours.
- **Portail Web & PWA** : consultation hors Discord avec thèmes clair/sombre, mode hors-ligne et authentification Discord OAuth2.
- **Rappels programmés** : notifications quotidiennes et hebdomadaires facultatives en message privé à 06h00.

---

## Commandes Discord

Le bot supporte l'installation sur serveur ainsi que l'installation utilisateur (*User App*, accessible partout sur Discord sans inviter le bot sur un serveur).

### `/day` et `/daily`

Affiche l'emploi du temps détaillé pour une journée spécifique (par défaut : aujourd'hui).

| Paramètre | Type | Valeur par défaut | Description |
| :--- | :--- | :--- | :--- |
| `date` | Texte | Date du jour | Date cible au format `JJ/MM/AAAA` (ex: `15/10/2026`). |
| `image` | Booléen | Choix du profil | `True` pour forcer le rendu image, `False` pour l'embed texte. |
| `url` | Texte | URL du profil | URL iCal directe temporaire (sans enregistrement préalable). |
| `user` | Utilisateur | Vous-même | Utilisateur Discord dont vous souhaitez consulter le planning (nécessite une autorisation via `/share`). |

**Sortie et interactions :**
- **Mode Image** : carte sombre Pillow affichant chaque cours avec badge horaire, matière, salle, intervenant et badge Teams visuel.
- **Mode Embed** : liste chronologique détaillée Discord avec timestamps dynamiques `<t:timestamp:t>`.
- **Boutons interactifs** : *Jour précédent*, *Jour suivant*, *Image / Embed* et bouton d'action *Rejoindre Teams* (affiché uniquement si le demandeur est propriétaire du planning).

### `/week` et `/weekly`

Affiche la grille complète du lundi au vendredi de la semaine demandée.

| Paramètre | Type | Valeur par défaut | Description |
| :--- | :--- | :--- | :--- |
| `date` | Texte | Semaine courante | N'importe quelle date comprise dans la semaine (`JJ/MM/AAAA`). |
| `image` | Booléen | Choix du profil | Rendu grille image proportionnelle (`True`) ou texte (`False`). |
| `url` | Texte | URL du profil | URL iCal ponctuelle. |
| `user` | Utilisateur | Vous-même | Ami Discord vous ayant accordé l'accès à son planning. |

**Sortie et interactions :**
- **Mode Image** : grille 5 colonnes (lundi au vendredi) avec découpage horaire proportionnel à la durée des blocs, colorimétrie dynamique par matière et adaptation aux décalages de fuseaux horaires.
- **Boutons interactifs** : *Semaine précédente*, *Semaine suivante*, bascule d'affichage et accès direct Teams.

### `/now`

Indique le statut en temps réel :
- Cours ou activité en cours d'exécution (avec salle, professeur et lien Teams direct).
- Liste des 4 prochains cours prévus dans les jours à venir.

### `/settings`

Gère la configuration de votre profil et vos préférences de notification.

- `/settings register <ical_url>` : enregistre votre lien Hyperplanning personnel.
- `/settings timezone <timezone>` : définit votre fuseau horaire IANA (ex: `Europe/Paris`, `America/New_York`).
- `/settings daily [enabled]` : active ou désactive le rappel quotidien à 06h00.
- `/settings weekly [enabled]` : active ou désactive le récapitulatif du lundi matin à 06h00.
- `/settings work_days [enabled]` : active ou désactive l'affichage des blocs "Entreprise" les jours sans cours.
- `/settings default_format [format]` : définit votre format d'affichage par défaut (`Image` ou `Embed`).
- `/settings language [lang]` : bascule la langue du bot (`Français` ou `English`).
- `/settings unregister` : supprime l'intégralité de vos données de la base de données.

### `/share`

Contrôle le partage de votre emploi du temps avec d'autres étudiants.

- `/share allow <user>` : accorde à un membre Discord l'autorisation de consulter votre planning avec `/day user:@ami` et `/week user:@ami`.
- `/share revoke <user>` : révoque immédiatement l'accès d'un utilisateur.
- `/share list` : affiche la liste complète des personnes actuellement autorisées.
- `/share link` : génère ou régénère votre lien secret pour le partage web (`https://domaine/share/<token>`).

---

## Portail Web & PWA

L'application intègre un serveur web FastAPI accessible sur le port 8080.

- **Interface Responsive** : optimisée pour mobiles, tablettes et ordinateurs de bureau.
- **Installation PWA** : peut être installée comme une application autonome sur Android et iOS.
- **Connexion Discord OAuth2** : permet de se connecter avec son compte Discord pour synchroniser automatiquement son URL iCal et ses préférences avec le bot Discord.
- **Navigation partagée** : menu déroulant permettant de basculer en un clic entre son planning personnel et les plannings des étudiants qui vous ont autorisé.
- **Mode Invité** : permet à toute personne sans compte Discord de coller une URL iCal, celle-ci étant conservée localement dans le navigateur (`localStorage`).

---

## Choix techniques et architecture

1. **Boucle asynchrone unifiée (FastAPI + discord.py)**
   Le serveur web Uvicorn et le bot Discord s'exécutent simultanément sur la même boucle d'événements `asyncio` (`asyncio.gather` dans `main.py`). Cela élimine le besoin d'un broker de messages (Redis/RabbitMQ) ou de processus séparés tout en partageant les mêmes pools de connexions et caches mémoire.

2. **Génération d'images en pur Python (Pillow)**
   Le rendu graphique s'appuie sur la bibliothèque standard `Pillow` et la police `Roboto` embarquée, sans dépendance vers des bibliothèques C système comme Cairo, Pango ou Weasyprint. Le déploiement est ainsi immédiat, sans compilation native lourde.

3. **Isolation stricte des bornes horaires**
   Le calcul de l'amplitude horaire (`start_hour` / `end_hour`) de la grille hebdomadaire s'isole exclusivement sur les cours tombant du lundi au vendredi. Les événements journée entière (jours fériés de week-end, vacances) ne peuvent pas dilater artificiellement la grille vers 00h00 ou 23h00.

4. **Sécurité et durcissement anti-SSRF**
   - **Protection contre le DNS Rebinding (TOCTOU)** : toutes les requêtes de récupération d'iCal passent par un résolveur personnalisé (`SafeResolver`) qui inspecte l'adresse IP résolue immédiatement avant la connexion et bloque les adresses locales, privées (RFC 1918), link-local et multicast.
   - **Protection anti-déni de service (DoS / OOM)** : cache en mémoire borné (`cachetools.TTLCache`, 64 entrées max) et téléchargement des flux iCal bridé à 5 Mo maximum.
   - **Assainissement XSS** : aucune insertion de contenu externe via `innerHTML` dans le frontend ; manipulation stricte par `textContent` ou échappement HTML.

5. **Persistance flexible (SQLModel / SQLAlchemy)**
   Support natif de PostgreSQL via le driver asynchrone `asyncpg` pour la production, avec repli automatique sur SQLite local (`aiosqlite`) lorsqu'aucune base PostgreSQL n'est spécifiée.

---

## Guide d'installation et auto-hébergement

### 1. Configuration Discord Developer Portal

1. Rendez-vous sur le [Discord Developer Portal](https://discord.com/developers/applications) et cliquez sur **New Application**.
2. Dans l'onglet **Bot** :
   - Cliquez sur **Add Bot** ou **Reset Token** pour copier votre `DISCORD_TOKEN`.
   - Activez l'option **Direct Messages** si nécessaire. Aucun *Privileged Intent* (comme Message Content ou Server Members) n'est requis.
3. Dans l'onglet **OAuth2** :
   - Copiez le `Client ID` (`DISCORD_CLIENT_ID`) et générez un `Client Secret` (`DISCORD_CLIENT_SECRET`).
   - Ajoutez l'URL de redirection sous **Redirects** : `http://localhost:8080/auth/callback` (ou `https://votre-domaine.com/auth/callback` en production).

### 2. Variables d'environnement

Créez un fichier `.env` à la racine du projet en vous basant sur les paramètres suivants :

| Variable | Obligatoire | Valeur par défaut | Description |
| :--- | :--- | :--- | :--- |
| `DISCORD_TOKEN` | Oui (pour le bot) | `""` | Jeton d'authentification du bot Discord. |
| `DISCORD_CLIENT_ID` | Recommandé | `""` | Identifiant client de l'application OAuth2. |
| `DISCORD_CLIENT_SECRET` | Recommandé | `""` | Secret client OAuth2 pour la connexion web. |
| `DISCORD_REDIRECT_URI` | Recommandé | `http://localhost:8080/auth/callback` | URL de retour après connexion Discord. |
| `WEB_HOST` | Non | `0.0.0.0` | Adresse d'écoute du serveur web FastAPI. |
| `WEB_PORT` | Non | `8080` | Port d'écoute du serveur web. |
| `WEB_BASE_URL` | Non | `http://localhost:8080` | URL publique du site web. |
| `SESSION_SECRET` | Non | Clé aléatoire | Clé secrète de chiffrement des sessions utilisateur. |
| `POSTGRES_HOST` | Non | `""` | Hôte PostgreSQL (si omis, bascule sur SQLite). |
| `POSTGRES_PORT` | Non | `5432` | Port de la base de données PostgreSQL. |
| `POSTGRES_DB` | Non | `""` | Nom de la base PostgreSQL. |
| `POSTGRES_USER` | Non | `""` | Utilisateur PostgreSQL. |
| `POSTGRES_PASSWORD` | Non | `""` | Mot de passe PostgreSQL. |
| `SQLITE_PATH` | Non | `bot_data.sqlite3` | Chemin du fichier de base de données SQLite local. |
| `BOT_TIMEZONE` | Non | `Europe/Paris` | Fuseau horaire par défaut du système. |

*Note : si `DISCORD_TOKEN` est omis, l'application démarre automatiquement en mode WebUI autonome.*

### 3. Démarrage local avec uv

Le gestionnaire de paquets [uv](https://docs.astral.sh/uv/) est recommandé pour sa rapidité d'exécution.

```bash
# 1. Cloner le dépôt
git clone https://github.com/enzomtpYT/EPSI-Bot.git
cd epsi-bot

# 2. Installer les dépendances
uv sync

# 3. Lancer l'application (Bot + WebUI)
uv run python src/main.py
```

L'interface web est alors accessible sur `http://localhost:8080`.

### 4. Déploiement Docker & Docker Compose

Le projet inclut un fichier `docker-compose.yml` prêt à l'emploi utilisant directement l'image multi-architecture pré-compilée sur GitHub Container Registry (`ghcr.io/enzomtpyt/epsi-bot:latest`) ainsi qu'une base de données PostgreSQL 16 configurée. Aucun besoin de compiler le projet sur votre serveur.

#### Démarrage rapide avec Docker Compose (Recommandé)

```bash
# 1. Cloner le projet
git clone https://github.com/enzomtpYT/EPSI-Bot.git
cd epsi-bot

# 2. Copier et renseigner votre fichier d'environnement
cp .env.example .env
nano .env  # Renseignez au minimum votre DISCORD_TOKEN

# 3. Lancer les conteneurs en arrière-plan (télécharge l'image GHCR automatiquement)
docker compose up -d
```

L'application attend automatiquement que PostgreSQL soit prêt (`service_healthy`) avant de démarrer. L'interface web est immédiatement disponible sur `http://localhost:8080`.

*(Optionnel) Si vous préférez compiler l'image depuis vos fichiers locaux plutôt que d'utiliser l'image GHCR, décommentez le bloc `build: .` dans `docker-compose.yml` ou lancez `docker compose up -d --build`.*

Pour consulter les journaux en direct :
```bash
docker compose logs -f
```

Pour arrêter les services :
```bash
docker compose down
```

#### Option alternative : Image Docker autonome

Si vous utilisez déjà votre propre serveur de base de données ou préférez le mode SQLite local :

```bash
# Construction de l'image
docker build -t epsi-bot .

# Lancement du conteneur
docker run -d \
  --name epsi-bot \
  -p 8080:8080 \
  -v bot_data:/app/data \
  --env-file .env \
  --restart unless-stopped \
  epsi-bot
```

---

## Qualité de code et tests

Le projet applique les standards stricts définis dans [AGENTS.md](AGENTS.md) :

```bash
# Exécution de la suite de tests unitaires (pytest)
uv run pytest

# Analyse statique et formatage (Ruff)
uv run ruff check . --fix
uv run ruff format .

# Vérification du typage statique (ty / pyright)
uv run ty check

# Audit de sécurité des dépendances (CVE)
uvx pip-audit
```