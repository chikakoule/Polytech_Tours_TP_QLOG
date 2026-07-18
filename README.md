# 🎾 Corpo Padel — Application de gestion de tournois

Application web de gestion de tournois de padel inter-entreprises, développée
pour le **TP Qualité, Tests & CI/CD** de Polytech Tours (cycle ingénieur 4A/5A).

> **Votre mission n'est pas de développer cette application, mais de l'éprouver :**
> tests fonctionnels manuels, tests End-to-End (Cypress), tests back-end (pytest),
> et construction d'une pipeline CI/CD. L'application fonctionne… en apparence.

- **Backend** : Python 3.11+ · FastAPI · SQLAlchemy · SQLite · JWT · bcrypt
- **Frontend** : Vue 3 · Vite · Vue Router · Pinia · axios · Tailwind CSS
- **Tests** : pytest + httpx (back) · Cypress (E2E)

---

## 📋 Prérequis

Installez ces outils avant de commencer (toutes plateformes) :

| Outil | Version minimale | Vérifier avec |
|-------|------------------|---------------|
| **Python** | 3.11, 3.12 ou 3.13 — ⚠️ **pas 3.14** | `python --version` |
| **Node.js** | 18+ | `node --version` |
| **npm** | 9+ | `npm --version` |
| **Git** | — | `git --version` |

> 💡 **Windows** : à l'installation de Python, cochez **« Add Python to PATH »**.
> Selon votre système, la commande peut être `python` ou `python3`, et `pip` ou `pip3`.

> ⚠️ **Python 3.14 n'est pas supporté.** Les dépendances épinglées (notamment
> `bcrypt` et `pydantic-core`) n'ont pas encore de paquets pré-compilés pour
> 3.14 : `pip install` tenterait de les compiler depuis les sources et
> échouerait. Utilisez **Python 3.11, 3.12 ou 3.13**.
>
> Si vous avez plusieurs versions installées, ciblez-en une explicitement :
> - **Windows** : `py -3.12 -m venv venv`
> - **macOS / Linux** : `python3.12 -m venv venv`

---

## 🚀 Installation

Clonez le dépôt, puis installez le backend et le frontend (deux terminaux).

```bash
git clone <URL_DU_DEPOT>
cd corpo-padel
```

### 1. Backend (API FastAPI)

<details open>
<summary><b>🪟 Windows (PowerShell)</b></summary>

```powershell
cd backend
python -m venv venv
venv\Scripts\Activate.ps1
pip install -r requirements.txt
copy .env.example .env
```

> Si l'activation est bloquée : `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned`
> (une seule fois), puis relancez `venv\Scripts\Activate.ps1`.
</details>

<details>
<summary><b>🍎 macOS / 🐧 Linux (bash/zsh)</b></summary>

```bash
cd backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```
</details>

### 2. Frontend (application Vue)

Dans un **second terminal**, depuis la racine du projet :

```bash
cd frontend
npm install
```

Créez le fichier d'environnement frontend :

- **Windows (PowerShell)** : `copy .env.example .env`
- **macOS / Linux** : `cp .env.example .env`

---

## 🌱 Jeu de données de test (seed)

Un script crée un jeu de données réaliste et cohérent (entreprises, joueurs,
équipes, poules, matchs passés et à venir) pour pouvoir tester immédiatement.

Depuis le dossier `backend/`, **avec l'environnement virtuel activé** :

```bash
python seed.py
```

> ⚠️ Le script **réinitialise** la base de données (`padel_corpo.db`) :
> toutes les données existantes sont supprimées puis recréées.
> Relancez-le quand vous voulez repartir d'un état propre.

---

## ▶️ Lancement

Deux terminaux, chacun dans son dossier.

### Backend — `backend/` (venv activé)

```bash
uvicorn app.main:app --reload --port 8000
```

➡️ API disponible sur **http://localhost:8000**
➡️ **Documentation interactive (Swagger) : http://localhost:8000/docs**

### Frontend — `frontend/`

```bash
npm run dev
```

➡️ Application disponible sur **http://localhost:5173**

---

## 🔑 Comptes de test

Créés par le script de seed :

| Rôle | Email | Mot de passe |
|------|-------|--------------|
| **Administrateur** | `admin@padel.com` | `Admin@2025!` |
| **Joueur** | `joueur@padel.com` | `Joueur@2025!` |

> Tous les comptes joueurs générés par le seed utilisent le mot de passe `Joueur@2025!`.

---

## 🧪 Tests

Un **squelette** est fourni avec un test d'exemple ; à vous de l'étoffer.

### Back-end (pytest) — depuis `backend/`, venv activé

```bash
pytest                                   # lancer les tests
pytest --cov=app --cov-report=term       # avec couverture (console)
pytest --cov=app --cov-report=html       # rapport HTML (htmlcov/index.html)
```

### End-to-End (Cypress) — depuis `frontend/`

> Le backend **et** le frontend doivent tourner (voir « Lancement »).

```bash
npx cypress open      # mode interactif (sélection des tests dans le navigateur)
npx cypress run       # mode headless (pour la CI)
```

---

## 📂 Structure du projet

```
corpo-padel/
├── backend/                # API FastAPI
│   ├── app/
│   │   ├── routers/        # endpoints (auth, players, teams, pools, events, matches, results, profile, admin)
│   │   ├── services/       # logique métier (classement, sérialisation)
│   │   ├── models.py       # modèles SQLAlchemy
│   │   ├── schemas.py      # schémas Pydantic (validation)
│   │   ├── security.py     # JWT, hachage, dépendances d'auth
│   │   ├── auth.py         # login + anti-brute force
│   │   ├── validators.py   # validations métier
│   │   └── main.py         # point d'entrée FastAPI
│   ├── tests/              # 👈 vos tests pytest
│   ├── seed.py             # jeu de données de test
│   └── requirements.txt
├── frontend/               # application Vue 3
│   ├── src/
│   │   ├── views/          # pages (accueil, planning, matchs, résultats, profil, admin…)
│   │   ├── components/     # composants réutilisables
│   │   ├── stores/         # état Pinia (auth)
│   │   ├── router/         # routes + gardes par rôle
│   │   └── api/            # client axios
│   └── cypress/            # 👈 vos tests E2E
├── .github/workflows/
│   └── ci.yml.example      # 👈 amorce de pipeline CI/CD (à compléter)
└── docs/                   # plan de test, fiches d'anomalies (à produire)
```

---

## 🆘 Dépannage

| Problème | Solution |
|----------|----------|
| `pip install` échoue (erreur de compilation, `Rust`, `maturin`, `error: could not build wheels`) | Vous êtes probablement en **Python 3.14**, non supporté. Recréez le venv avec 3.11/3.12/3.13 : `py -3.12 -m venv venv` (Windows) ou `python3.12 -m venv venv`. |
| `uvicorn: command not found` | L'environnement virtuel n'est pas activé. Réactivez-le (voir Installation). |
| Port 8000 ou 5173 déjà utilisé | Fermez l'autre processus, ou changez le port (`--port`, `npm run dev -- --port 5174`). |
| Le frontend n'atteint pas l'API | Vérifiez que le backend tourne et que `frontend/.env` contient `VITE_API_BASE_URL=http://localhost:8000/api/v1`. |
| Erreurs CORS | Vérifiez `ALLOWED_ORIGINS` dans `backend/.env` (par défaut `http://localhost:5173`). |
| Repartir d'une base propre | Relancez `python seed.py` depuis `backend/`. |

### Lint & CI

| Problème | Solution |
|----------|----------|
| `npm run lint` remonte des centaines d'erreurs | Vérifiez que `frontend/.eslintignore` existe : sans lui, ESLint analyse `dist/` (code minifié) et génère un bruit énorme. Ne lintez jamais les artefacts de build. |
| `'cy' is not defined` / `'describe' is not defined` | Les globales Cypress ne sont définies que dans les tests E2E. La config `.eslintrc.cjs` les active via `overrides` sur `cypress/**` et `*.cy.js`. |
| « pytest ne passe pas en CI » | Vérifiez **quel step** a échoué : lint et tests sont indépendants (flake8 n'influence pas pytest). Un step en échec arrête le job — si le lint précède les tests, ceux-ci ne s'exécutent jamais. |
| `flake8: command not found` | `flake8` est dans `requirements.txt` : faites `pip install -r requirements.txt`. La config (longueur de ligne) est dans `backend/setup.cfg`. |
| Cypress échoue au démarrage en CI | Le backend et le frontend doivent être démarrés **et** joignables : utilisez `npx wait-on` sur les deux URL avant `cypress run`. |

---

## 📚 Ressources

- FastAPI — https://fastapi.tiangolo.com/
- Vue 3 — https://vuejs.org/
- pytest — https://docs.pytest.org/
- Cypress — https://docs.cypress.io/
- GitHub Actions — https://docs.github.com/actions
- OWASP Top 10 — https://owasp.org/www-project-top-ten/

---

*Projet pédagogique — Polytech Tours — Qualité, Test & Sécurité.*
