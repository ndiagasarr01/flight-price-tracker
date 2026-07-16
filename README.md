# Flight Price Tracker — Montréal/Québec → Dakar

Vérifie chaque semaine le prix du vol pour plusieurs combinaisons de dates
de départ/retour, et envoie un courriel de rapport listant les 3 offres les
moins chères par combinaison, la meilleure offre globale, la variation
depuis le dernier relevé, et le min/max des 7 derniers relevés.

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
  le plan gratuit inclut 100 recherches/mois.
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
Le workflow tourne automatiquement chaque lundi à 10h00 UTC (~5-6h heure de
Québec). Tu peux aussi le lancer manuellement pour tester : onglet
**Actions** de ton dépôt → « Vérification hebdomadaire du prix du vol » →
**Run workflow**.

## Personnaliser

Modifie ces valeurs dans `.github/workflows/check-prices.yml` (section `env:`) :
- `DEPARTURE_ID` / `ARRIVAL_ID` : codes aéroport (ex. `YQB`, `YUL`, `DSS`)
- `OUTBOUND_DATES` / `RETURN_DATES` : listes de dates séparées par des virgules
  (format `AAAA-MM-JJ`). Le script teste **toutes les combinaisons**
  départ × retour (ex. 3 dates de départ × 4 dates de retour = 12 combinaisons).
- L'heure/fréquence d'exécution : modifie le `cron` dans le fichier (format UTC)

## Limites à connaître
- Le plan gratuit SerpApi est plafonné à 100 requêtes/mois. Chaque combinaison
  de dates = 1 requête. Avec 12 combinaisons et une vérification par semaine,
  ça fait ~48 requêtes/mois — reste une marge, mais évite d'ajouter trop de
  dates ou de repasser en fréquence quotidienne sans réduire les combinaisons.
- Les prix Google Flights peuvent différer légèrement de ce que tu vois en
  navigant directement (taxes, disponibilité en temps réel).
- Si une combinaison de dates échoue (erreur réseau, aucun vol trouvé), elle
  est ignorée et un avertissement est affiché dans les logs — les autres
  combinaisons sont quand même incluses dans le rapport.
