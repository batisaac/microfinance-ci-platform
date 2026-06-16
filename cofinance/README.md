# COFINANCE CI — Plateforme Digitale

Plateforme de gestion de microcrédits, d'assurance mobile et de support client en temps réel.

## Stack technique

- **Backend** : Django 5.x + Django REST Framework
- **Authentification** : JWT (djangorestframework-simplejwt)
- **WebSocket** : Django Channels + Daphne
- **Documentation API** : drf-spectacular (Swagger)
- **Base de données** : SQLite (dev) / PostgreSQL (prod)

## Installation

```bash
# 1. Cloner le dépôt
git clone <url-du-repo>
cd cofinance

# 2. Créer l'environnement virtuel
python -m venv .venv
source .venv/bin/activate  # Linux/Mac
.venv\Scripts\activate      # Windows

# 3. Installer les dépendances
pip install -r requirements.txt

# 4. Configurer l'environnement
cp .env.example .env
# Éditer .env si nécessaire

# 5. Appliquer les migrations
python manage.py migrate

# 6. Générer les données de démonstration
python manage.py seed_db

# 7. Lancer le serveur (avec Daphne pour le WebSocket)
daphne -p 8000 config.asgi:application
```

## Identifiants de démonstration

| Rôle | Email | Mot de passe |
|------|-------|-------------|
| Admin | admin@cofinance.ci | admin123 |
| Agent | agent1@cofinance.ci | agent123 |
| Client | client1@cofinance.ci | client123 |

## Accès à l'interface

- **Interface web** : http://localhost:8000
- **Documentation API** : http://localhost:8000/api/docs/
- **Admin Django** : http://localhost:8000/admin/
- **WebSocket Chat** : ws://localhost:8000/ws/chat/{id}/?token={jwt}

## Structure du projet

```
cofinance/
├── config/                     # Configuration Django
│   ├── settings/
│   │   └── base.py             # Réglages principaux
│   ├── urls.py                 # Routage central
│   └── asgi.py                 # Point d'entrée ASGI
├── apps/
│   ├── accounts/               # Authentification & utilisateurs
│   ├── credits/                # Gestion des microcrédits
│   ├── repayments/             # Remboursements
│   ├── insurance/              # Assurance mobile
│   ├── notifications/          # Notifications internes
│   ├── dashboard/              # Tableau de bord
│   ├── chat/                   # Chat support en temps réel
│   └── frontend/               # Interface web + seed_db
├── templates/                  # Templates HTML
├── manage.py
└── requirements.txt
```

## API REST

Toutes les routes sont préfixées par `/api/v1/` :

| Module | Routes | Description |
|--------|--------|-------------|
| Auth | `/auth/register/`, `/auth/login/`, `/auth/profile/` | Inscription, connexion JWT, profil |
| Crédits | `/loans/`, `/loans/{id}/`, `/loans/{id}/status/` | CRUD prêts, workflow statuts |
| Remboursements | `/repayments/`, `/repayments/{id}/` | Enregistrement et suivi |
| Assurance | `/insurance/plans/`, `/insurance/subscribe/`, `/insurance/my-policies/` | Produits, souscription, polices |
| Notifications | `/notifications/`, `/notifications/{id}/read/` | Alertes, marquage lu |
| Dashboard | `/dashboard/` | Indicateurs clés (admin) |
| Chat | `/chat/conversations/`, `/chat/conversations/{id}/messages/` | Conversations, messages |

## Tests

```bash
pytest -v
# 85 tests — tout doit passer
```

## Production

Pour déployer en production :

1. Configurer PostgreSQL et Redis
2. Définir `DATABASE_URL=postgres://...` dans `.env`
3. Configurer `CHANNEL_LAYERS` avec Redis (dans settings)
4. Définir `DEBUG=False` et `ALLOWED_HOSTS`
5. Restreindre `CORS_ALLOWED_ORIGINS`
