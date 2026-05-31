"""Script de seed — jeu de données réaliste et cohérent pour la recette manuelle.

Crée :
  - le compte administrateur de test ;
  - 12 entreprises, 24 joueurs (chacun avec un compte JOUEUR) ;
  - 12 équipes (binômes d'une même entreprise) ;
  - 2 poules de 6 équipes (Poule A, Poule B) ;
  - des matchs PASSÉS (statut TERMINE, avec scores valides) et À VENIR (A_VENIR),
    répartis sur plusieurs dates, créneaux et pistes.

Usage (depuis backend/, venv activé) :
    python seed.py

Le script RÉINITIALISE la base : toutes les tables sont supprimées puis recréées.

Comptes de test :
    Admin   : admin@padel.com   / Admin@2025!
    Joueur  : joueur@padel.com  / Joueur@2025!
    (tous les comptes joueurs créés par le seed utilisent Joueur@2025!)
"""
import random
from datetime import date, timedelta

from app.database import Base, SessionLocal, engine, init_db
from app.models import Event, LoginAttempt, Match, Player, Pool, Team, User
from app.security import hash_password
from app.validators import validate_score

random.seed(42)

ADMIN_EMAIL = "admin@padel.com"
ADMIN_PASSWORD = "Admin@2025!"
PLAYER_PASSWORD = "Joueur@2025!"
TEST_PLAYER_EMAIL = "joueur@padel.com"

# 12 entreprises, 2 joueurs chacune. Le 1er joueur de "Tech Corp" est le compte
# de test joueur@padel.com (membre d'une équipe → utile pour la recette).
COMPANIES = [
    ("Tech Corp", [("Jean", "Joueur", TEST_PLAYER_EMAIL), ("Marie", "Lefevre", "marie.lefevre@techcorp.fr")]),
    ("Innov Ltd", [("Paul", "Moreau", "paul.moreau@innov.fr"), ("Sophie", "Girard", "sophie.girard@innov.fr")]),
    ("DataFlow", [("Lucas", "Bernard", "lucas.bernard@dataflow.fr"), ("Emma", "Dubois", "emma.dubois@dataflow.fr")]),
    ("CloudNine", [("Hugo", "Petit", "hugo.petit@cloudnine.fr"), ("Lea", "Roux", "lea.roux@cloudnine.fr")]),
    ("NextGen", [("Louis", "Fontaine", "louis.fontaine@nextgen.fr"), ("Chloe", "Mercier", "chloe.mercier@nextgen.fr")]),
    ("ByteForge", [("Nathan", "Blanc", "nathan.blanc@byteforge.fr"), ("Camille", "Faure", "camille.faure@byteforge.fr")]),
    ("PixelPro", [("Theo", "Garnier", "theo.garnier@pixelpro.fr"), ("Manon", "Chevalier", "manon.chevalier@pixelpro.fr")]),
    ("NetWave", [("Gabriel", "Robin", "gabriel.robin@netwave.fr"), ("Jade", "Masson", "jade.masson@netwave.fr")]),
    ("CodeCraft", [("Raphael", "Simon", "raphael.simon@codecraft.fr"), ("Alice", "Lemoine", "alice.lemoine@codecraft.fr")]),
    ("LogiTeam", [("Arthur", "Henry", "arthur.henry@logiteam.fr"), ("Ines", "Rousseau", "ines.rousseau@logiteam.fr")]),
    ("SmartSys", [("Adam", "Mathieu", "adam.mathieu@smartsys.fr"), ("Louise", "Clement", "louise.clement@smartsys.fr")]),
    ("WebSphere", [("Jules", "Gauthier", "jules.gauthier@websphere.fr"), ("Anna", "Perrin", "anna.perrin@websphere.fr")]),
]

# Résultats de set valides pour le vainqueur (l'autre côté est l'opposé).
VALID_WIN_SETS = [(6, 0), (6, 1), (6, 2), (6, 3), (6, 4), (7, 5), (7, 6)]
EVENT_TIMES = ["18:00", "18:30", "19:00", "19:30", "20:00", "20:30"]


def reset_database() -> None:
    Base.metadata.drop_all(bind=engine)
    init_db()


def make_score() -> tuple[str, str]:
    """Génère un score valide (team1 vainqueur) : (score_team1, score_team2)."""
    if random.random() < 0.6:
        # Victoire 2-0
        s1, s2 = random.choice(VALID_WIN_SETS), random.choice(VALID_WIN_SETS)
        sets_t1 = [f"{s1[0]}-{s1[1]}", f"{s2[0]}-{s2[1]}"]
    else:
        # Victoire 2-1 (team1 gagne set 1 et 3, perd set 2)
        a1, a2, a3 = (random.choice(VALID_WIN_SETS) for _ in range(3))
        sets_t1 = [f"{a1[0]}-{a1[1]}", f"{a2[1]}-{a2[0]}", f"{a3[0]}-{a3[1]}"]

    score_t1 = ", ".join(sets_t1)
    # Miroir : "6-4" -> "4-6"
    score_t2 = ", ".join(
        f"{s.split('-')[1]}-{s.split('-')[0]}" for s in sets_t1
    )
    assert validate_score(score_t1), f"score_t1 invalide: {score_t1}"
    assert validate_score(score_t2), f"score_t2 invalide: {score_t2}"
    return score_t1, score_t2


def seed() -> None:
    reset_database()
    db = SessionLocal()
    try:
        # ── Compte administrateur ──
        admin = User(
            email=ADMIN_EMAIL,
            password_hash=hash_password(ADMIN_PASSWORD),
            role="ADMINISTRATEUR",
            is_active=True,
            must_change_password=False,
        )
        db.add(admin)
        db.flush()
        db.add(
            Player(
                first_name="Admin",
                last_name="Sys",
                company="Corpo Padel",
                license_number="L000001",
                email=ADMIN_EMAIL,
                user_id=admin.id,
            )
        )

        # ── Joueurs + comptes + équipes ──
        teams: list[Team] = []
        license_counter = 100001
        for company, members in COMPANIES:
            player_objs = []
            for first, last, email in members:
                user = User(
                    email=email,
                    password_hash=hash_password(PLAYER_PASSWORD),
                    role="JOUEUR",
                    is_active=True,
                    must_change_password=False,
                )
                db.add(user)
                db.flush()
                player = Player(
                    first_name=first,
                    last_name=last,
                    company=company,
                    license_number=f"L{license_counter:06d}",
                    email=email,
                    user_id=user.id,
                    birth_date=date(1990, 1, 1) + timedelta(days=random.randint(0, 4000)),
                )
                license_counter += 1
                db.add(player)
                db.flush()
                player_objs.append(player)

            team = Team(
                company=company,
                player1_id=player_objs[0].id,
                player2_id=player_objs[1].id,
            )
            db.add(team)
            db.flush()
            teams.append(team)

        # ── Poules : 6 premières équipes en A, 6 suivantes en B ──
        pool_a = Pool(name="Poule A")
        pool_b = Pool(name="Poule B")
        db.add_all([pool_a, pool_b])
        db.flush()
        for t in teams[:6]:
            t.pool_id = pool_a.id
        for t in teams[6:]:
            t.pool_id = pool_b.id

        pools_teams = {pool_a.id: teams[:6], pool_b.id: teams[6:]}

        # ── Matchs PASSÉS (TERMINE) ──
        today = date.today()
        termine_count = 0
        # 6 événements passés, espacés d'une semaine, 2 matchs chacun (12 matchs).
        for week in range(6, 0, -1):
            ev_date = today - timedelta(weeks=week)
            ev = Event(event_date=ev_date, event_time=random.choice(EVENT_TIMES))
            db.add(ev)
            db.flush()
            pool_id = pool_a.id if week % 2 == 0 else pool_b.id
            pool_teams = pools_teams[pool_id][:]
            random.shuffle(pool_teams)
            quartet = pool_teams[:4]
            for court, (ta, tb) in enumerate([(quartet[0], quartet[1]), (quartet[2], quartet[3])], start=1):
                # Vainqueur aléatoire : on échange éventuellement les scores.
                s1, s2 = make_score()
                if random.random() < 0.5:
                    team1, team2, sc1, sc2 = ta, tb, s1, s2
                else:
                    team1, team2, sc1, sc2 = ta, tb, s2, s1
                db.add(
                    Match(
                        event_id=ev.id,
                        team1_id=team1.id,
                        team2_id=team2.id,
                        court_number=court,
                        status="TERMINE",
                        score_team1=sc1,
                        score_team2=sc2,
                    )
                )
                termine_count += 1

        # ── Matchs À VENIR (A_VENIR) ──
        avenir_count = 0
        # 6 événements futurs dans les 30 prochains jours, 2 matchs chacun.
        for i, day_offset in enumerate([3, 7, 10, 14, 21, 28]):
            ev_date = today + timedelta(days=day_offset)
            ev = Event(event_date=ev_date, event_time=random.choice(EVENT_TIMES))
            db.add(ev)
            db.flush()
            pool_id = pool_a.id if i % 2 == 0 else pool_b.id
            pool_teams = pools_teams[pool_id][:]
            random.shuffle(pool_teams)
            quartet = pool_teams[:4]
            for court, (ta, tb) in enumerate([(quartet[0], quartet[1]), (quartet[2], quartet[3])], start=1):
                db.add(
                    Match(
                        event_id=ev.id,
                        team1_id=ta.id,
                        team2_id=tb.id,
                        court_number=court,
                        status="A_VENIR",
                    )
                )
                avenir_count += 1

        # ── Un match ANNULE pour illustrer le statut ──
        ev = Event(event_date=today + timedelta(days=5), event_time="19:00")
        db.add(ev)
        db.flush()
        db.add(
            Match(
                event_id=ev.id,
                team1_id=teams[0].id,
                team2_id=teams[1].id,
                court_number=3,
                status="ANNULE",
            )
        )

        db.commit()

        # ── Récapitulatif ──
        print("Base de données initialisée avec succès.")
        print(f"  Utilisateurs   : {db.query(User).count()} (1 admin + 24 joueurs)")
        print(f"  Joueurs        : {db.query(Player).count()}")
        print(f"  Équipes        : {db.query(Team).count()}")
        print(f"  Poules         : {db.query(Pool).count()} (Poule A, Poule B de 6 équipes)")
        print(f"  Événements     : {db.query(Event).count()}")
        print(f"  Matchs TERMINE : {termine_count}")
        print(f"  Matchs A_VENIR : {avenir_count}")
        print(f"  Matchs ANNULE  : 1")
        print()
        print("Comptes de test :")
        print(f"  Admin  : {ADMIN_EMAIL} / {ADMIN_PASSWORD}")
        print(f"  Joueur : {TEST_PLAYER_EMAIL} / {PLAYER_PASSWORD}")
        print(f"  (tous les comptes joueurs utilisent le mot de passe {PLAYER_PASSWORD})")
    finally:
        db.close()


if __name__ == "__main__":
    seed()
