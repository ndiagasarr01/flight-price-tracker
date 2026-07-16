# Flight Price Tracker — Montréal/Québec → Dakar

Vérifie le prix du vol tous les jours et envoie un courriel de rapport
(prix du jour, variation depuis hier, min/max des 7 derniers jours).

## Comment ça marche

Un « robot » ne peut pas tourner tout seul indéfiniment — il a besoin d'un
endroit où s'exécuter chaque jour. Ici, c'est **GitHub Actions** (gratuit
pour un usage personnel) qui joue ce rôle : GitHub lance le script
automatiquement selon l'horaire défini, même si ton ordinateur est éteint.

## Étapes de mise en place (environ 15 minutes)

### 1. Créer un dépôt GitHub
- Va sur [github.com/new](https://github.com/new), crée un dépôt (peut être privé).
- Mets-y ces fichiers (`flight_price_tracker.py`, `requirements.txt`,
  `price_history.json`, `.github/workflows/check-prices.yml`).

### 2. Obtenir une clé SerpApi (accès aux données Google Flights)
- Crée un compte gratuit sur [serpapi.com](https://serpapi.com/) —
  le plan gratuit inclut 100 recherches/mois, largement assez pour 1
  vérification par jour.
- Copie ta clé API (« API Key ») depuis ton tableau de bord SerpApi.

### 3. Créer un mot de passe d'application Gmail (pour l'envoi du courriel)
- Si tu utilises Gmail : va dans ton compte Google → Sécurité →
  Validation en deux étapes (doit être activée) → Mots de passe des applications.
- Génère un mot de passe d'application (16 caractères) — **ce n'est pas ton
  mot de passe Gmail habituel**.
- (Tu peux utiliser un autre fournisseur SMTP si tu préfères — ajuste
  `SMTP_HOST`/`SMTP_PORT` dans le script.)

### 4. Ajouter les secrets dans GitHub
Dans ton dépôt : Settings → Secrets and variables → Actions → New repository secret.
Ajoute :

| Nom du secret | Valeur |
|---|---|
| `SERPAPI_KEY` | ta clé SerpApi |
| `EMAIL_ADDRESS` | ton adresse Gmail (celle qui envoie) |
| `EMAIL_APP_PASSWORD` | le mot de passe d'application généré à l'étape 3 |
| `EMAIL_TO` | l'adresse où tu veux recevoir les alertes (peut être la même) |

### 5. C'est tout !
Le workflow tourne automatiquement chaque jour à 10h00 UTC (~5-6h heure de
Québec). Tu peux aussi le lancer manuellement pour tester : onglet
**Actions** de ton dépôt → « Vérification quotidienne du prix du vol » →
**Run workflow**.

## Personnaliser

Modifie ces valeurs dans `.github/workflows/check-prices.yml` (section `env:`) :
- `DEPARTURE_ID` / `ARRIVAL_ID` : codes aéroport (ex. `YQB`, `YUL`, `DSS`)
- `OUTBOUND_DATE` / `RETURN_DATE` : format `AAAA-MM-JJ`
- L'heure d'exécution : modifie le `cron` dans le fichier (format UTC)

## Limites à connaître
- Le plan gratuit SerpApi est plafonné à 100 requêtes/mois — 1 vérification/jour
  = ~30/mois, donc large marge.
- Les prix Google Flights peuvent différer légèrement de ce que tu vois en
  navigant directement (taxes, disponibilité en temps réel).
- Si tu veux suivre plusieurs trajets ou dates en même temps, il faudra
  dupliquer les variables d'environnement ou adapter le script en boucle.
