# EPSI Bot Discord

Un bot Discord pour accéder facilement à votre emploi du temps EPSI directement depuis Discord.

[![Inviter le bot](https://img.shields.io/badge/Inviter%20le%20bot-Discord-7289DA?style=for-the-badge&logo=discord&logoColor=white)](https://discord.com/oauth2/authorize?client_id=1357424188306227451)

## Fonctionnalités

- 📅 Afficher votre emploi du temps EPSI pour une journée spécifique
- 📆 Afficher votre emploi du temps EPSI pour une semaine complète
- 🔄 Enregistrement de votre nom d'utilisateur EPSI
- 🖼️ Option pour afficher l'emploi du temps sous forme d'image
- 📅 Filtrage par date

## Commandes

### `/day` - Afficher l'emploi du temps d'une journée
Affiche votre emploi du temps EPSI pour une journée spécifique.

**Options :**
- `username` : Votre nom d'utilisateur EPSI (optionnel si vous êtes enregistré)
- `date` : Date au format JJ/MM/AAAA (optionnel, utilise la date du jour par défaut)
- `image` : Si activé, envoie l'emploi du temps sous forme d'image

### `/week` - Afficher l'emploi du temps d'une semaine
Affiche votre emploi du temps EPSI pour une semaine complète.

**Options :**
- `username` : Votre nom d'utilisateur EPSI (optionnel si vous êtes enregistré)
- `date` : Date au format JJ/MM/AAAA (optionnel, utilise la date du jour pour trouver la semaine actuelle)
- `image` : Si activé, envoie l'emploi du temps sous forme d'image

### `/settings` - Gérer vos paramètres et enregistrement
Permet d'enregistrer ou de supprimer votre nom d'utilisateur EPSI et de gérer les préférences de notifications.

Sous-commandes / options disponibles :
- `register` : Enregistrer ou mettre à jour votre nom d'utilisateur EPSI (ex : `/settings register username:mon_identifiant`).
- `unregister` : Supprimer votre enregistrement (ex : `/settings unregister`).
- `daily` : Activer/Désactiver les notifications quotidiennes (choix : Activer / Désactiver).
- `weekly` : Activer/Désactiver les notifications hebdomadaires (choix : Activer / Désactiver).

Exemples :
- Enregistrer un nom d'utilisateur : `/settings register mon_identifiant`
- Désenregistrer : `/settings unregister`
- Activer les notifications quotidiennes : `/settings daily Activer`

## Installation

1. Cliquez sur le bouton "Inviter le bot" ci-dessus
2. Sélectionnez le serveur où vous souhaitez ajouter le bot
3. Autorisez les permissions nécessaires
4. Le bot est maintenant prêt à être utilisé !

## Configuration

Pour utiliser le bot, vous pouvez enregistrer votre nom d'utilisateur EPSI avec la sous-commande `/settings register` (ou fournir `username` chaque fois que vous faites la commande `/day` ou `/week`). Une fois enregistré, vous pourrez utiliser les commandes `/day` et `/week` sans avoir à spécifier votre nom d'utilisateur à chaque fois.

## Support

Si vous rencontrez des problèmes ou si vous avez des questions, n'hésitez pas à contacter le développeur du bot.

## Développement

Ce bot est développé avec :
- Python 3.x
- discord.py
- Autres dépendances listées dans `requirements.txt`

Pour contribuer au développement, n'hésitez pas à ouvrir une issue ou à proposer une pull request.