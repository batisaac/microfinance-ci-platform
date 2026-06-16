# COFINANCE CI — Plateforme Digitale de Microfinance

Application Django de gestion de microcrédits, d'assurance mobile et de support client en temps réel avec API REST documentée et interface web responsive.

## 1. Fonctionnalités

- **Authentification JWT** — Inscription, connexion, rafraîchissement avec rotation et blacklist
- **Gestion des microcrédits** — Création, workflow de validation (soumise → analyse → approuvée → décaissée), calcul automatique du score d'éligibilité
- **Remboursements** — Enregistrement avec calcul automatique des intérêts (5%) et pénalités (0.5%/jour de retard)
- **Assurance mobile** — Produits d'assurance, souscription, suivi des expirations (< 15 jours)
- **Notifications** — Générées automatiquement par signaux Django (création prêt, changement statut, remboursement, souscription assurance)
- **Chat support temps réel** — WebSocket avec messages, indicateur de saisie, accusés de lecture, assignation automatique d'agent
- **Dashboard admin** — KPIs : volume par statut, taux de recouvrement, souscriptions actives, conversations ouvertes
- **Interface web responsive** — Bootstrap 5.3, 3 rôles (admin/agent/client), sidebar, graphiques Chart.js

## 2. Technologies utilisées

| Technologie | Version |
|------------|---------|
| Python | 3.11+ |
| Django | 5.2 |
| Django REST Framework | 3.17 |
| Django Channels | 4.3 |
| Daphne | 4.2 |
| djangorestframework-simplejwt | 5.5 |
| drf-spectacular | 0.29 |
| Bootstrap | 5.3 |
| Chart.js | 3.9 |
| SQLite (dev) / PostgreSQL (prod) | — |

## 3. Installation

```bash
# 1. Cloner le dépôt
git clone https://github.com/batisaac/microfinance-ci-platform.git
cd microfinance-ci-platform

# 2. Créer l'environnement virtuel
python -m venv .venv

# 3. Activer l'environnement
# Windows :
.venv\Scripts\activate
# Linux/Mac :
source .venv/bin/activate

# 4. Installer les dépendances
pip install -r requirements.txt

# 5. Configurer l'environnement
copy .env.example .env     # Windows
# cp .env.example .env     # Linux/Mac
```

## 4. Variables d'environnement

Fichier `.env` à la racine du projet :

```env
SECRET_KEY=votre_cle_secrete
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1
DATABASE_URL=sqlite:///db.sqlite3
```

Pour la production, remplacer `DATABASE_URL` par une URL PostgreSQL :
```env
DATABASE_URL=postgres://user:password@host:5432/cofinance
```

## 5. Migrations

```bash
python manage.py migrate
```

## 6. Données de démonstration

```bash
python manage.py seed_db
```

Cette commande crée :
- 1 administrateur, 3 agents, 5 clients
- 3 produits d'assurance
- 5 demandes de prêt à différents statuts avec échéanciers
- 3 conversations de démonstration

## 7. Lancement du serveur

```bash
# Avec support WebSocket (recommandé)
daphne -p 8000 config.asgi:application

# Sans WebSocket (développement uniquement)
python manage.py runserver
```

## 8. Accès à l'interface

| Interface | URL |
|-----------|-----|
| Application web | http://localhost:8000/ |
| Documentation API (Swagger) | http://localhost:8000/api/docs/ |
| Schéma OpenAPI | http://localhost:8000/api/schema/ |
| Administration Django | http://localhost:8000/admin/ |
| WebSocket Chat | ws://localhost:8000/ws/chat/{id}/?token={jwt} |

## 9. Comptes de démonstration

| Rôle | Email | Mot de passe |
|------|-------|-------------|
| Admin | admin@cofinance.ci | admin123 |
| Agent 1 | agent1@cofinance.ci | agent123 |
| Agent 2 | agent2@cofinance.ci | agent123 |
| Agent 3 | agent3@cofinance.ci | agent123 |
| Client 1 | client1@cofinance.ci | client123 |
| Client 2 | client2@cofinance.ci | client123 |
| Client 3 | client3@cofinance.ci | client123 |
| Client 4 | client4@cofinance.ci | client123 |
| Client 5 | client5@cofinance.ci | client123 |

## Structure du projet

```
microfinance-ci-platform/
├── config/                     # Configuration Django
│   ├── settings/base.py        # Réglages principaux
│   ├── urls.py                 # Routage central (/api/v1/...)
│   └── asgi.py                 # Point d'entrée ASGI (HTTP + WebSocket)
├── apps/
│   ├── accounts/               # Authentification JWT & utilisateurs
│   ├── credits/                # Gestion des microcrédits
│   ├── repayments/             # Remboursements avec calcul intérêts
│   ├── insurance/              # Assurance mobile
│   ├── notifications/          # Notifications par signaux Django
│   ├── dashboard/              # KPIs admin
│   ├── chat/                   # Chat temps réel (WebSocket)
│   └── frontend/               # Vues web + commande seed_db
├── templates/                  # 8 templates HTML (Bootstrap 5)
├── docs/                       # Documentation (.gitkeep)
├── media/                      # Uploads utilisateurs (.gitkeep)
├── static/                     # Fichiers statiques (.gitkeep)
├── manage.py
├── requirements.txt
├── pytest.ini
└── README.md
```

## API REST

Toutes les routes sous `/api/v1/` :

| Méthode | Route | Description |
|---------|-------|-------------|
| POST | `/auth/register/` | Inscription (rôle client) |
| POST | `/auth/login/` | Connexion JWT |
| POST | `/auth/token/refresh/` | Rafraîchir token |
| GET/PUT | `/auth/profile/` | Profil utilisateur |
| GET/POST | `/loans/` | Lister/créer des prêts |
| GET | `/loans/{id}/` | Détail d'un prêt |
| PATCH | `/loans/{id}/status/` | Changer statut (admin/agent) |
| GET/POST | `/repayments/` | Lister/créer remboursements |
| GET | `/repayments/{id}/` | Détail remboursement |
| GET | `/insurance/plans/` | Produits d'assurance |
| POST | `/insurance/subscribe/` | Souscrire |
| GET/POST | `/insurance/my-policies/` | Mes polices |
| GET | `/insurance/my-policies/{id}/` | Détail police |
| GET | `/notifications/` | Mes notifications |
| PATCH | `/notifications/{id}/read/` | Marquer comme lu |
| GET/POST | `/chat/conversations/` | Conversations |
| PATCH | `/chat/conversations/{id}/assign/` | Assigner agent |
| GET | `/chat/conversations/{id}/messages/` | Messages |
| GET | `/dashboard/` | KPIs admin |

## Tests

```bash
# Lancer tous les tests
python -m pytest -v

# Ou avec Django test runner
python manage.py test

# Tester une application spécifique
python manage.py test apps.accounts
python manage.py test apps.chat
```

## Déploiement production

1. Configurer PostgreSQL et Redis
2. Définir `DATABASE_URL=postgres://...` dans `.env`
3. Modifier `CHANNEL_LAYERS` dans les settings pour utiliser Redis
4. `DEBUG=False`, `ALLOWED_HOSTS= votre-domaine.com`
5. Restreindre `CORS_ALLOWED_ORIGINS`
6. Lancer : `daphne -p 8000 config.asgi:application`
