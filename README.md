# EPSI Bot Discord

Un bot Discord pour accéder facilement à votre emploi du temps EPSI directement depuis Discord.

[![Inviter le bot](https://img.shields.io/badge/Inviter%20le%20bot-Discord-7289DA?style=for-the-badge&logo=discord&logoColor=white)](https://discord.com/oauth2/authorize?client_id=1357424188306227451)

## Fonctionnalités

- 📅 Afficher votre emploi du temps EPSI
- 🔄 Enregistrement de votre nom d'utilisateur EPSI
- 🖼️ Option pour afficher l'emploi du temps sous forme d'image
- 📅 Filtrage par date (début et fin)

## Commandes

### `/edt` - Afficher l'emploi du temps
Affiche votre emploi du temps EPSI.

**Options :**
- `username` : Votre nom d'utilisateur EPSI (optionnel si vous êtes enregistré)
- `start_time` : Date de début au format JJ/MM/AAAA (optionnel)
- `end_time` : Date de fin au format JJ/MM/AAAA (optionnel)
- `image` : Si activé, envoie l'emploi du temps sous forme d'image

### `/register` - S'enregistrer
Enregistre votre nom d'utilisateur EPSI pour une utilisation plus rapide.

**Options :**
- `username` : Votre nom d'utilisateur EPSI

### `/unregister` - Se désenregistrer
Supprime votre enregistrement EPSI.

## Installation

1. Cliquez sur le bouton "Inviter le bot" ci-dessus
2. Sélectionnez le serveur où vous souhaitez ajouter le bot
3. Autorisez les permissions nécessaires
4. Le bot est maintenant prêt à être utilisé !

## Configuration

Pour utiliser le bot, vous devez d'abord vous enregistrer avec la commande `/register` en spécifiant votre nom d'utilisateur EPSI. Une fois enregistré, vous pourrez utiliser la commande `/edt` sans avoir à spécifier votre nom d'utilisateur à chaque fois.

## Support

Si vous rencontrez des problèmes ou si vous avez des questions, n'hésitez pas à contacter le développeur du bot.

## Développement

Ce bot est développé avec :
- Python 3.x
- discord.py
- Autres dépendances listées dans `requirements.txt`

Pour contribuer au développement, n'hésitez pas à ouvrir une issue ou à proposer une pull request. 