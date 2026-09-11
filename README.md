# Paddock Analytics — Dashboard F1

Dashboard d'analyse Formule 1 construit avec **FastF1**, **Streamlit** et **Plotly**. Aucune clé API requise : toutes les données proviennent de FastF1, qui accède librement à la télémétrie et au chronométrage officiels F1.

> Ce projet a été construit en autonomie complète, sans validation intermédiaire. Toutes les décisions (course par défaut, structure, choix de design, périmètre des fonctionnalités) ont été prises de façon autonome et sont documentées ci-dessous.

## Lancement

```bash
cd f1-dashboard
python -m venv venv
# Windows
venv\Scripts\activate
# macOS/Linux
source venv/bin/activate

pip install -r requirements.txt
streamlit run app/main.py
```

L'app s'ouvre sur `http://localhost:8501`. **Le premier chargement d'une session** (Année → Grand Prix → Session dans la sidebar) télécharge les données depuis les serveurs FastF1 (10 à 40s selon la session, la télémétrie étant la plus lourde). Elles sont ensuite écrites dans `.cache/` à la racine du projet et rechargées instantanément aux visites suivantes — y compris après redémarrage de l'app.

Prévoir une connexion internet au premier chargement de chaque session ; aucune clé, aucun compte, aucune configuration n'est nécessaire.

## Course choisie par défaut

**Abu Dhabi Grand Prix 2024** (dernière manche de la saison 2024, Yas Marina, 8 décembre 2024), session **Course**.

Choisie car :
- Course complète et bien documentée dans FastF1 (télémétrie, positions GPS, stands, messages de direction de course tous disponibles et cohérents — vérifié par un test de fumée avant de construire dessus).
- Dernière manche de la saison : enjeux de championnat constructeurs, forte densité d'événements de course (arrêts aux stands, dégradation pneus sur la durée complète).
- Le sélecteur Année / Grand Prix / Session en sidebar permet de changer de course à tout moment ; n'importe quelle manche de 2018 à aujourd'hui devrait fonctionner (FastF1 fournit une télémétrie fiable à partir de la saison 2018).

## Stack technique

| Couche | Choix | Pourquoi |
|---|---|---|
| Données | [FastF1](https://docs.fastf1.dev/) | Seule librairie donnant un accès gratuit et sans authentification à la télémétrie F1 officielle (vitesse, RPM, freins, position GPS) — contrainte imposée du projet. |
| Interface | Streamlit | Une seule commande pour lancer un dashboard interactif complet, sans maintenir un front séparé. |
| Graphiques | Plotly (`graph_objects`) | Interactivité (zoom, hover, légendes cliquables) native, thème sombre personnalisable finement, contrairement à matplotlib. |
| Couleurs pilotes/équipes | `fastf1.plotting` (`get_driver_color`, `get_team_color`, `get_compound_color`) | Couleurs officielles saison-par-saison fournies nativement par FastF1, avec repli sur une palette maison si l'écurie/le composé n'est pas reconnu. |
| Rafraîchissement live | [`streamlit-autorefresh`](https://pypi.org/project/streamlit-autorefresh/) | Package PyPI public, sans clé ni compte, pour redéclencher un rerun Streamlit léger à intervalle régulier en mode « session en direct » sans recharger la page. |

## Structure du projet

```
f1-dashboard/
├── app/
│   ├── main.py                 # Point d'entrée Streamlit : sidebar, chargement session, onglets
│   ├── theme.py                # Couleurs, palette, styles Plotly partagés
│   ├── style.py                 # CSS injecté (thème "control room" sombre)
│   └── components/              # Un module = une fonctionnalité = un onglet
│       ├── header.py
│       ├── overview.py
│       ├── driver_comparison.py
│       ├── track_map.py
│       ├── tire_strategy.py
│       ├── race_chart.py
│       ├── telemetry.py
│       ├── degradation_heatmap.py
│       ├── quali_vs_race.py
│       └── consistency.py
├── data/
│   ├── loader.py                 # Chargement FastF1, mis en cache (st.cache_resource / st.cache_data)
│   └── processing.py             # Transformation des données brutes FastF1 → structures prêtes pour les graphes
├── .streamlit/config.toml        # Thème Streamlit natif (complète le CSS custom)
├── .cache/                       # Cache disque FastF1 (créé au premier lancement, ignoré par git)
└── requirements.txt
```

Séparation stricte : `data/` ne connaît rien de Streamlit ni de Plotly (fonctions pures pandas/numpy) ; `app/` ne fait aucun calcul de données, uniquement de la présentation. Chaque fonctionnalité vit dans son propre fichier de composant, appelé depuis `app/main.py`.

## Design

- **Thème « control room »** : fond quasi noir en dégradé radial (`#0A0A0C` → `#08080a`), cartes en `#141417` avec bordure fine `#2A2A2E` qui s'illumine en rouge F1 au survol.
- **Rouge F1** (`#E10600`) comme unique accent (liseré de header, titres de section, barres actives) — utilisé avec parcimonie pour rester lisible.
- **Typographie** : `Oswald` (condensée, sportive) pour tous les titres et libellés forts, `Titillium Web` (utilisée par plusieurs équipes F1 dans leur communication) pour le corps de texte. Chargées via Google Fonts, avec repli sans-serif système.
- **Couleurs officielles pilotes/équipes** sur tous les graphiques comparatifs (`fastf1.plotting`), pour que deux pilotes de la même écurie restent reconnaissables (nuances) et que deux écuries différentes soient immédiatement distinguables.
- **Layout en grille** : `st.columns` pour les métriques/cartes podium, `st.container(border=True)` pour transformer chaque bloc de graphique en « card » avec ombre et bordure, plutôt que des widgets Streamlit empilés bruts.
- **Transitions** : `transition` Plotly (350ms, easing cubique) sur tous les graphiques + transitions CSS sur le survol des cartes.
- **Header** stylé avec logo, titre du dashboard, nom de l'événement, circuit, date et vainqueur de la session sélectionnée.

## Passe de raffinement design (Impeccable)

Une passe de finition a été appliquée avec le plugin Claude Code [Impeccable](https://impeccable.style/) (`pbakaus/impeccable`), en mode **raffinement** (l'identité control-room F1 est conservée, pas remplacée — décision confirmée avec l'utilisateur, dashboard destiné à être partagé). Sa checklist qualité (`craft-floor`) a fait remonter deux points concrets, corrigés :

- **Bordures colorées gauche/droite bannies** sur les cartes/callouts (pattern jugé trop générique) : le liseré rouge du header est passé d'un `border-left` à un `box-shadow` inset en bas ; le marqueur des titres de section est passé d'un `border-left` à une puce carrée `::before` distincte.
- **Emoji utilisés comme système d'icônes** (logo, onglets, boutons, badge) : remplacés par de vraies icônes — [Material Symbols](https://fonts.google.com/icons) de Streamlit (`:material/...:`, nativement supporté dans `st.tabs`, `st.button(icon=...)`, `st.markdown` et `page_icon`) pour les onglets/boutons/titre sidebar/favicon, et un SVG authoré à la main (trait unique 1.75px, style Feather) pour le logo du header.
- **Bonus (surfaces navigateur)** : theming de `::selection`, des scrollbars WebKit et des anneaux de focus (`:focus-visible`) sur la palette du site, plus `font-variant-numeric: tabular-nums` sur les valeurs chiffrées (stats, métriques) pour un alignement propre des colonnes de chiffres.

Une sauvegarde du code source (hors `venv/`/`.cache/`) a été prise dans `../f1-dashboard_backup_pre_impeccable` avant cette passe (pas de dépôt git existant à ce stade pour servir de filet de sécurité).

## Bilinguisme FR/EN

Le dashboard est bilingue français/anglais, ajouté suite à la critique de design (le public FastF1 est majoritairement international alors que l'app était 100% en français) :

- **Sélecteur de langue** en haut de la sidebar (`st.segmented_control`, FR/EN), au-dessus des sélecteurs Année/Grand Prix/Session. Le français reste la langue par défaut et la source de vérité des textes.
- **Persisté dans le lien** comme le reste de la sélection (`?lang=en` dans l'URL), via le même mécanisme `st.query_params` que l'année/le Grand Prix/la session/la catégorie d'onglet/le pilote suivi — un lien partagé rouvre dans la langue où il a été copié.
- **`app/i18n.py`** : module minimal sans dépendance externe — un dictionnaire `TRANSLATIONS["fr"|"en"][clé] -> texte`, une fonction `t(clé, **kwargs)` qui résout la langue courante, retombe sur le français si la clé manque dans la langue active, puis sur la clé brute en dernier recours (ne plante jamais sur une traduction manquante), et supporte l'interpolation (`.format(**kwargs)`) pour les textes avec valeurs dynamiques (nom de pilote, numéro de tour...).
- Chaque chaîne visible par l'utilisateur — libellés de la sidebar, titres de section, messages d'erreur/info, titres et axes des graphiques Plotly, en-têtes de colonnes des tableaux — passe par `t()`, dans `app/main.py`, `app/components/header.py` et les 9 fichiers de `app/components/`.
- **Volontairement non traduits** : abréviations pilotes (VER, HAM...), noms d'écuries (McLaren, Ferrari...), noms de composés pneus (SOFT/MEDIUM/HARD...) et « Safety Car » / « Virtual Safety Car » — vocabulaire FastF1/F1 utilisé tel quel dans les deux langues, pas du texte applicatif.
- Le seul texte utilisateur généré côté `data/` (le statut « Tour N » / « Lap N » du classement provisoire en direct, dans `get_live_classification`) prend un paramètre `lang` explicite plutôt que d'importer `app.i18n` — `data/` reste sans dépendance vers Streamlit ou la couche de présentation.

## Photos pilotes, voitures et logos écuries

Ajoutés sans nouvelle dépendance ni clé — tout est hotlink direct vers les sources officielles, jamais téléchargé/redistribué (`app/media.py`) :

- **Photo du pilote sélectionné** : sur les 4 onglets avec un sélecteur de pilote (Comparaison, Télémétrie, Carte du circuit, Stratégie pneus — dégradation), une petite carte apparaît sous le sélecteur avec la photo, le nom complet et le logo de l'écurie. La photo vient directement de `HeadshotUrl`, un champ que FastF1 fournit déjà (sourcé du média officiel F1) — pas de recherche ni de scraping.
- **Logos écurie** : sur le podium (Vue d'ensemble) et à côté du nom d'écurie dans chaque carte pilote.
- **Image de la voiture** : sur Carte du circuit et Stratégie pneus, à côté du pilote sélectionné.
- **Source** : le CDN média public de Formula1.com (`media.formula1.com`), avec une table de correspondance `TeamId` (fourni par FastF1) → slug CDN, couverte pour la grille actuelle (2023+ : McLaren, Ferrari, Mercedes, Red Bull, Alpine, Haas, Aston Martin, Williams, RB, Kick Sauber). **Limitation assumée** : les écuries plus anciennes ou renommées (Alfa Romeo, Racing Point, Toro Rosso, AlphaTauri, Renault...) ne sont pas dans cette table — logo/voiture omis silencieusement pour ces saisons plutôt que de deviner une URL et risquer une image cassée.
- **Robustesse** : chaque `<img>` porte un `onerror` qui masque l'image si le lien est mort ou expiré — jamais d'icône d'image cassée visible.

## Commentaire IA (optionnel, nécessite une clé payante)

Chaque onglet peut afficher un court commentaire généré par Google Gemini (`gemini-3.8-flash`), basé strictement sur les chiffres déjà calculés pour cet onglet (podium, écarts de temps, stratégie pneus, etc.) — jamais sur des données brutes non vérifiées, pour limiter le risque d'invention.

**Gemini a été choisi spécifiquement pour son vrai niveau gratuit permanent** (aucune carte bancaire requise, contrairement à l'API Anthropic envisagée initialement) — ça garde tout le projet sans coût, y compris cette fonctionnalité.

- **Activation** : copier `.streamlit/secrets.toml.example` vers `.streamlit/secrets.toml` (fichier gitignored, jamais commité) et y renseigner `GEMINI_API_KEY` avec une clé créée sur [aistudio.google.com/api-keys](https://aistudio.google.com/api-keys) (gratuit, juste un compte Google). Sans ce fichier, les cartes de commentaire n'apparaissent simplement pas — le reste du dashboard fonctionne à l'identique.
- **Modèle** : `gemini-3.8-flash`, thinking désactivé (`thinking_budget=0` — texte court et factuel, pas de raisonnement complexe nécessaire), `max_output_tokens=300`.
- **Cache pour rester dans les limites gratuites** : chaque commentaire est mis en cache 20 minutes (`st.cache_data`, clé = saison + Grand Prix + session + onglet + sélections pertinentes comme les pilotes comparés) — un onglet consulté plusieurs fois dans cette fenêtre, par n'importe quel visiteur, ne déclenche qu'un seul appel. Ce délai est volontairement plus long que l'intervalle de rafraîchissement live (15-60s) pour rester confortablement sous les limites de requêtes/minute du niveau gratuit et éviter un texte qui change à chaque tick.
- **Portée** : un commentaire par onglet (9 maximum), pas par graphique individuel — chaque prompt n'envoie que quelques chiffres déjà agrégés, jamais de télémétrie brute, ce qui garde les appels courts.
- **Robustesse** : `app/ai_commentary.py` échoue silencieusement (pas de carte affichée) si la clé est absente, le SDK `google-genai` n'est pas installé, ou l'appel API échoue (ex. limite de requêtes atteinte) — jamais d'erreur visible côté utilisateur pour cette fonctionnalité optionnelle.

## Grands Prix en direct

Le sélecteur ne se limite plus aux week-ends terminés : un Grand Prix en cours (essais, qualifs ou course) est sélectionnable dès qu'une de ses sessions a démarré, et le dashboard passe alors en **mode direct** :

- **Sélecteur élargi** (`get_selectable_event_names`) : un événement apparaît dès que son week-end est proche (jusqu'à 3 jours avant la course) ou déjà en cours, pas seulement une fois entièrement terminé.
- **Sessions filtrées** (`get_available_session_codes`) : seules les sessions dont l'heure de départ officielle (issue du calendrier FastF1, fuseau UTC) est déjà passée sont proposées — impossible de sélectionner par erreur une session qui n'a pas encore commencé.
- **Détection « en direct »** (`is_session_live`) : une session est considérée en direct dans une fenêtre de 4h après son heure de départ officielle (marge volontairement large pour absorber retards/drapeaux rouges). Un badge rouge pulsé « 🔴 EN DIRECT » apparaît alors dans le header et la sidebar.
- **Rafraîchissement automatique** : en mode direct, le cache FastF1 est contourné (`fastf1.Cache.disabled()`) et la session est rechargée depuis le réseau toutes les 15 à 60 secondes (réglable), via `streamlit-autorefresh` (rerun léger, sans recharger la page ni perdre les sélections). Un bouton « Actualiser maintenant » force un rafraîchissement immédiat. Hors mode direct, le comportement (cache long, aucun rechargement réseau) est inchangé.
- **Classement provisoire** : tant que la classification officielle FastF1 n'est pas encore renseignée (typique en cours de session), le podium, le tableau de classement et l'onglet Qualifs vs course retombent automatiquement sur un classement dérivé du dernier tour connu de chaque pilote (`get_live_classification`), avec un badge « Classement provisoire » explicite. Dès que la classification officielle est disponible, elle reprend le dessus automatiquement.

**Limitations du mode direct** (à ne pas présenter comme du live timing professionnel) :
- Ce n'est pas un flux temps réel seconde par seconde : les données viennent du même backend FastF1 que pour l'historique (archives de la télémétrie live F1, republiées avec un léger différé, de l'ordre de quelques dizaines de secondes à quelques minutes selon la charge des serveurs F1) — pas du flux SignalR bas-niveau (`fastf1.livetiming`), qui nécessiterait un processus d'enregistrement tournant en continu pendant toute la session et n'a pas pu être testé en conditions réelles faute de session live disponible pendant le développement.
- `fastf1.Cache.disabled()` est un état global non thread-safe côté FastF1 ; avec plusieurs utilisateurs simultanés sur la même instance du dashboard, deux rafraîchissements concomitants pourraient théoriquement interférer. Sans impact pour un usage personnel/local (cas d'usage visé ici).
- La logique de détection (`is_session_live`, `get_available_session_codes`, `get_selectable_event_names`) a été validée par un test dédié (`live_smoke_test.py`) qui simule différents instants (avant le week-end / pendant la course / longtemps après) sur les vraies données de calendrier 2024 ; le rafraîchissement réseau réel pendant une session live n'a en revanche pas pu être observé en conditions réelles.

## Fonctionnalités implémentées

Toutes les 10 fonctionnalités demandées sont implémentées et fonctionnelles :

1. **Sélecteur Année / Grand Prix / Session** (sidebar) — année 2018-2025, liste des GP filtrée aux manches déjà disputées, 7 types de session (Course, Qualifs, Sprint, Sprint Qualifs, EL1-3).
2. **Vue d'ensemble** — cartes podium (couleur or/argent/bronze), pole position, meilleur tour, température piste, badges des périodes Safety Car / VSC (détectées via `session.track_status`), tableau du classement complet.
3. **Comparaison 2 pilotes** — temps au tour superposés, delta cumulé (via `fastf1.utils.delta_time`, référence = meilleur tour du pilote A), temps par secteur en barres groupées.
4. **Carte du circuit colorée par vitesse** — tracé du meilleur tour, points colorés par vitesse instantanée (dégradé gris → bleu → rouge → jaune), numéros de virage superposés via `session.get_circuit_info()`, métriques vitesse max/moyenne.
5. **Stratégie pneus** — diagramme de Gantt des relais par pilote (composé + tours), pente de dégradation estimée par régression linéaire (temps au tour vs âge du train de pneus) par relais, nuage de points avec droites de régression par relais pour un pilote sélectionné.
6. **Race chart** — évolution des positions tour par tour, sélection multiple de pilotes, axe des positions inversé (P1 en haut).
7. **Comparaison télémétrie brute** — vitesse, accélérateur, frein, rapport de vitesse, RPM superposés pour 2 pilotes sur un tour choisi indépendamment par pilote, 5 sous-graphiques synchronisés sur la distance.
8. **Heatmap de dégradation** — écart de chaque tour au temps médian du pilote, matrice pilote × tour, échelle bleu (rapide) → rouge (lent).
9. **Qualifs vs course** — places gagnées/perdues entre la grille de qualification et l'arrivée (barres vert/rouge), rythme de course médian par pilote, tableau détaillé.
10. **Classement par régularité** — écart-type des temps au tour hors tours sous drapeau jaune/SC/VSC et tours d'entrée/sortie des stands, coloré du plus régulier (vert) au moins régulier (rouge).

## Choix techniques notables / décisions prises en autonomie

- **Un seul script multi-onglets plutôt qu'une app multipage Streamlit** : les 9 fonctionnalités de contenu (hors sélecteur) partagent le même objet `session` déjà chargé ; les onglets (`st.tabs`) évitent de recharger/re-sélectionner l'état à chaque navigation, contrairement à une multipage app où chaque page est un script indépendant.
- **`st.cache_resource` pour les objets `Session` FastF1** (et non `st.cache_data`) : ces objets contiennent un état interne complexe qui ne se sérialise pas proprement — `cache_resource` les garde en mémoire tels quels au lieu de tenter un pickle.
- **Isolation des erreurs par onglet** (`safe_render` dans `main.py`) : si une fonctionnalité échoue pour une session particulière (ex. pas de données de position sur une séance d'essais libres), seul cet onglet affiche une erreur lisible — le reste du dashboard continue de fonctionner.
- **Filtrage de régularité approximatif** : l'exclusion des tours « sous drapeau » se fait sur la colonne `TrackStatus` de FastF1 (contient un ou plusieurs codes concaténés par tour) plutôt que sur un recoupement seconde-par-seconde avec `track_status` — suffisant pour classer les pilotes entre eux, mais peut inclure quelques tours de transition en bord de fenêtre SC/VSC.
- **Dégradation pneus = régression linéaire simple** (temps au tour vs âge du train de pneus) par relais, pas un modèle physique — volontairement lisible et robuste plutôt que prédictif.
- **Couleurs avec repli** : `theme.driver_color` / `theme.team_color` / `theme.compound_color` retombent sur une palette maison si `fastf1.plotting` ne reconnaît pas le pilote/l'écurie (saisons très anciennes, pilotes remplaçants, etc.).

## Limitations connues

- Les saisons antérieures à ~2018 ont une télémétrie incomplète ou absente côté FastF1 (limitation de la source de données, pas du dashboard) — le sélecteur les exclut par défaut.
- La carte du circuit n'applique pas la rotation d'affichage officielle (`circuit_info.rotation`) : le tracé est correct mais son orientation à l'écran ne correspond pas nécessairement à une carte « nord en haut ».
- « Qualifs vs course » compare uniquement Qualifications → Course ; il ne gère pas les week-ends Sprint (Sprint Qualifying / Sprint) comme référence de grille.
- Le delta cumulé de l'onglet « Comparaison pilotes » utilise `fastf1.utils.delta_time`, que FastF1 marque lui-même comme approximatif (pas de meilleure alternative native à ce jour) — à recouper avec les temps par secteur affichés juste à côté en cas de doute.
- Aucun test automatisé (pytest) n'a été ajouté faute de temps — la validation s'est faite par un script de fumée (`smoke_test.py`) exécutant chaque fonction de traitement de données sur une vraie session, et par `streamlit.testing.v1.AppTest` pour valider le rendu de bout en bout sans navigateur.
- Le cache FastF1 (`.cache/`) grossit avec chaque nouvelle session consultée ; aucune purge automatique n'est mise en place.

## Fichiers de développement (non nécessaires à l'exécution)

Scripts de validation utilisés pendant le développement, à la racine du projet — peuvent être supprimés ou conservés pour re-valider après modification :
- `smoke_test.py` : exécute chaque fonction de `data/processing.py` sur une vraie session (Abu Dhabi 2024).
- `apptest_smoke.py` : rend l'app entière via `streamlit.testing.v1.AppTest` (sans navigateur) et vérifie l'absence d'exception et de widget d'erreur.
- `live_smoke_test.py` : valide la détection « session en direct » (`is_session_live`, `get_available_session_codes`, `get_selectable_event_names`) en simulant différents instants sur le vrai calendrier 2024.
- `provisional_smoke_test.py` : valide le classement provisoire de secours (`get_live_classification`, `get_effective_results`) en vidant artificiellement la classification officielle d'une vraie session.
