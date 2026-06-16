# COFINANCE CI — Document de Passation Complet

## Vue d'ensemble

Plateforme Django de microfinance numérique (prêts, assurance mobile, chat support temps réel).

- **Backend** : Django 5.2.15 + DRF 3.17
- **Auth** : JWT (simplejwt 5.5, access 2h / refresh 7j, rotation + blacklist)
- **WebSocket** : Channels 4.3 + Daphne 4.2 (chat temps réel)
- **Base de données** : SQLite (dev), PostgreSQL (prod via `DATABASE_URL`)
- **API docs** : drf-spectacular 0.29 (Swagger `/api/docs/`)
- **Stockage** : Local (dev), S3-ready (django-storages + boto3)

---

## Structure des dossiers

```
microfinance-ci-platform/           # Racine du dépôt = racine Django
├── .env.example                    # Template variables d'environnement
├── .gitignore                      # Un seul .gitignore à la racine
├── HANDOFF.md                      # Document de passation
├── manage.py                       # Point d'entrée Django
├── pytest.ini                      # Configuration pytest
├── README.md                       # Documentation projet
├── requirements.txt                # Dépendances Python
├── apps/                           # Applications Django
│   ├── accounts/                  # Utilisateurs & auth JWT
│   ├── credits/                   # Gestion des prêts
│   ├── repayments/                # Remboursements
│   ├── insurance/                 # Assurance mobile
│   ├── notifications/             # Notifications (signaux + REST)
│   ├── chat/                      # Chat support (WebSocket + REST)
│   ├── dashboard/                 # KPIs admin
│   └── frontend/                  # Vues template + seed_db
├── config/                         # Configuration Django
│   ├── asgi.py                    # Point d'entrée ASGI (HTTP + WS)
│   ├── wsgi.py
│   ├── urls.py                    # Routage racine
│   └── settings/
│       └── base.py                # Configuration principale
├── docs/                           # Documentation
│   └── .gitkeep
├── media/                          # Uploads utilisateurs (.gitkeep)
├── static/                         # Fichiers statiques source (.gitkeep)
├── staticfiles/                    # Collectstatic (.gitkeep)
└── templates/                      # 8 templates HTML
    ├── base.html                  # Layout principal (502 lignes)
    ├── login.html                 # Page connexion standalone
    ├── dashboard.html             # Tableau de bord
    ├── loans_list.html            # Liste des prêts
    ├── loan_detail.html           # Détail d'un prêt + graphique
    ├── insurance_list.html        # Assurance
    ├── notifications.html         # Notifications
    └── chat.html                  # Chat support WebSocket
```

---

## Modèles de données (11 tables)

| App | Tables | Clés |
|-----|--------|------|
| accounts | `User` | email (unique), phone (unique), rôle (client/agent/admin), région |
| credits | `Loan`, `LoanDocument`, `LoanSchedule` | Loan: client, montant, statut, score, durée, taux |
| repayments | `Repayment` | Loan, agent, montant, méthode (cash/orange_money/mtn_momo/wave/bank) |
| insurance | `InsurancePlan`, `InsuranceSubscription` | Plan: couverture, prime. Subscription: client, plan, dates |
| notifications | `Notification` | Destinataire, titre, body, type, lien, is_read |
| chat | `Conversation`, `Message` | Conversation: client, agent, statut. Message: contenu, is_read |

---

## API REST (19 endpoints, préfixe `/api/v1/`)

### Authentification
- `POST auth/register/` — Inscription (rôle=client forcé)
- `POST auth/login/` — Connexion JWT
- `POST auth/token/refresh/` — Rafraîchir token
- `GET/PUT/PATCH auth/profile/` — Profil utilisateur

### Prêts (credits)
- `GET/POST loans/` — Lister/créer des prêts
- `GET loans/<id>/` — Détail d'un prêt
- `PATCH loans/<id>/status/` — Changer statut (admin/agent)

### Remboursements
- `GET/POST repayments/` — Lister/créer (POST: admin/agent)
- `GET repayments/<id>/` — Détail

### Assurance
- `GET insurance/plans/` — Plans actifs
- `POST insurance/subscribe/` — Souscrire
- `GET/POST insurance/my-policies/` — Mes polices
- `GET insurance/my-policies/<id>/` — Détail police

### Notifications
- `GET notifications/` — Lister (filtre `?unread=true`)
- `PATCH notifications/<id>/read/` — Marquer comme lu

### Chat
- `GET/POST chat/conversations/` — Lister/créer conversation
- `PATCH chat/conversations/<id>/assign/` — Assigner agent
- `GET chat/conversations/<id>/messages/` — Messages

### Dashboard
- `GET dashboard/` — KPIs admin (filtres: date_from, date_to, agent, région)

---

## WebSocket

- `ws/chat/<conversation_id>/?token=<jwt_access>` — Chat temps réel
- Types de messages : `message`, `typing`, `mark_read`
- Auth via JWT en query string

---

## Machine à états — Workflow prêt

```
soumise → en_analyse → approuvee → decaissée
   ↓          ↓
 rejetee    rejetee
```

Seuls admin/agent peuvent transitionner.

---

## Règles métier clés

- **Score éligibilité** : ratio montant/durée (≤50k→100, ≤100k→75, etc.)
- **Remboursement** : auto-répartition intérêts (5%) / pénalité (0.5%/jour de retard) / principal
- **Assignation agent** : round-robin (agent avec le moins de conversations ouvertes)
- **Notifications** : signaux Django automatiques sur création/changement de statut prêt, remboursement, souscription assurance

---

## Templates HTML — Architecture

### `base.html`
- Layout SPA : sidebar navigation, topbar, contenu principal
- CDN : Bootstrap 5.3, Chart.js 3.9.1, Bootstrap Icons, Google Fonts Inter
- Framework JS : gestion tokens JWT (localStorage), `apiFetch()` avec auto-refresh 401, fonctions utilitaires (formatCurrency, statusBadge, showToast), `loadNotifCount()` polling 30s

### `login.html` (standalone)
- Connexion via API, stockage tokens + user_data
- Boutons de démo pour les 3 rôles
- Auto-redirect si déjà connecté

### `dashboard.html`
- Admin : 4 cartes stats, graphique barres (statuts), donut (recouvrement), tableau derniers prêts, notifications récentes
- Client : stats basiques de ses prêts

### `loans_list.html`
- Tableau filtrable (statut, recherche)
- Modal nouveau prêt (montant, objet, durée)
- Pagination

### `loan_detail.html`
- Panel infos, donut score éligibilité, tableau échéancier, boutons actions (workflow)

### `insurance_list.html`
- Cartes produits, tableau souscriptions actives, indicateur expiration (<15 jours)
- Modal souscription

### `notifications.html`
- Filtre tout/non-lu, marquer lu individuel/tout

### `chat.html`
- Interface WebSocket temps réel : liste conversations (badge non-lus), fenêtre chat, indicateur typing
- Responsive mobile
- Auto-connect/déconnect WebSocket

---

## Tests (~85 tests, pytest)

| App | Nb tests |
|-----|----------|
| accounts | ~25 |
| credits | ~12 |
| repayments | ~8 |
| insurance | ~15 |
| notifications | ~10 |
| dashboard | ~14 |
| chat (REST + WS) | ~15 |

---

## Données de démo (commande `seed_db`)

| Rôle | Email | Mot de passe |
|------|-------|-------------|
| Admin | admin@cofinance.ci | admin123 |
| Agent | agent1@cofinance.ci | agent123 |
| Agent | agent2@cofinance.ci | agent123 |
| Agent | agent3@cofinance.ci | agent123 |
| Client | client1@cofinance.ci | client123 |
| Client | client5@cofinance.ci | client123 |

---

## Dépendances Python (requirements.txt)

```
django>=5.0, djangorestframework>=3.15, djangorestframework-simplejwt>=5.3
channels>=4.1, daphne>=4.1
drf-spectacular>=0.27
django-cors-headers>=4.3
python-decouple>=3.8, dj-database-url>=2.1
psycopg2-binary>=2.9, Pillow>=10.0
```

---

## Commandes utiles

```bash
# Activer l'environnement
.venv\Scripts\activate

# Lancer le serveur (WebSocket support)
daphne -p 8000 config.asgi:application

# OU en dev (sans WebSocket)
python manage.py runserver

# Seed base de démo
python manage.py seed_db

# Tests (85 tests, découvrables automatiquement)
python -m pytest -v

# Collection statique
python manage.py collectstatic

# Documentation API
# http://localhost:8000/api/docs/
```

---

## Déploiement production

1. `.env` : `DATABASE_URL=postgres://...`, `DEBUG=False`, `ALLOWED_HOSTS=...`
2. `CHANNEL_LAYERS` : Redis au lieu de InMemoryChannelLayer
3. `CORS_ALLOWED_ORIGINS` : restreindre
4. `python manage.py collectstatic`
5. Démarrer avec `daphne -p 8000 config.asgi:application`

---

## Dernières corrections appliquées

1. **Structure aplatie** : projet sorti du sous-dossier `cofinance/` → `manage.py`, `apps/`, `config/` à la racine du dépôt (structure idéale)
2. **.gitignore unique** : supprimé le doublon `cofinance/.gitignore`, gardé le plus complet à la racine
3. **.gitkeep corrigés** : `docs.gitkeep` → `docs/.gitkeep` (dans le dossier), idem pour media/, static/, staticfiles/
4. **.pytest_cache** : ajouté au `.gitignore` racine
5. **Django 5.2.15** : rétrogradé depuis 6.0.6 pour conformité (le cahier des charges impose Django 5.x)
6. **Chart.js** : v4.4.4 avait une erreur TLD → passé à v3.9.1 via jsdelivr
7. **Chat navigation** : `classList.toggle` → `classList.add` (bug second clic)
8. **Chat badge non-lus** : ajout `mark_read` WebSocket à l'ouverture et à réception message
9. **Chat crash null** : `chatLoading` détruit par `loadMessages` → recréé à chaque `openConversation`
10. **Favicon** : inline SVG + route Django (`/favicon.ico`)
11. **Login** : page standalone (pas d'extension base.html) pour éviter cache CSS `.main-content`
