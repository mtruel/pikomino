# Pikomino : Simulateur de jeu

Un simulateur complet du jeu de société **Pikomino** avec interface web interactive et système d'IA pour tester différentes stratégies. Implémentation complète respectant toutes les règles officielles du jeu. Fait entièrement avec Cursor (Test de vibe coding)

## 🎲 Caractéristiques

- **Interface web moderne** avec Flask et Socket.IO pour jouer en temps réel
- **Moteur de jeu complet** respectant toutes les règles du Pikomino avec gestion des cas particuliers
- **Système d'IA avancé** avec différentes stratégies (conservative, agressive, équilibrée)
- **Tests complets** couvrant tous les cas particuliers et scénarios de jeu
- **Simulation de parties** pour analyser l'efficacité des stratégies
- **Interface console** pour les tests rapides

## 🚀 Installation

### Prérequis
- Python 3.13 ou plus récent
- pip (gestionnaire de paquets Python)

### Installation des dépendances

```bash
# Installer les dépendances
pip install flask flask-socketio

# Ou utiliser le fichier pyproject.toml
pip install -e .
```

## 🎮 Utilisation

### Interface Web (Recommandé)

Lancez l'interface web interactive :

```bash
python main.py web
```

Puis ouvrez votre navigateur sur [http://localhost:5000](http://localhost:5000)

### Mode Console

Pour une démonstration rapide en console :

```bash
python main.py demo
```

### Simulation de parties

Pour analyser les stratégies avec des simulations automatiques :

```bash
# Simuler 10 parties (par défaut)
python main.py simulate

# Simuler 100 parties
python main.py simulate --games 100
```

### Tests

Pour lancer la suite de tests complète :

```bash
pytest test_pikomino.py -v
```

### Exemples avancés

Testez des stratégies personnalisées :

```bash
python examples.py
```

## 🏗️ Architecture du projet

```
secondes/
├── main.py                 # Point d'entrée principal
├── pikomino.py            # Moteur de jeu et modèles
├── app.py                 # Application Flask
├── examples.py            # Exemples de stratégies
├── test_pikomino.py       # Tests complets du jeu
├── RULES.md               # Règles détaillées du jeu
├── templates/             # Templates HTML
│   ├── base.html
│   ├── index.html
│   └── game.html
├── static/               # Fichiers statiques
│   └── css/
│       └── style.css
├── pyproject.toml        # Configuration du projet
└── README.md
```

## 🎯 Règles du jeu Pikomino

### Objectif
Collecter le plus de vers possible en récupérant des tuiles Pikomino avec les dés.

### Matériel
- **8 dés** avec faces 1, 2, 3, 4, 5 et symbole "ver"
- **16 tuiles Pikomino** numérotées de 21 à 36 avec différents nombres de vers :
  - Tuiles 21-24 : 1 ver chacune
  - Tuiles 25-28 : 2 vers chacune
  - Tuiles 29-32 : 3 vers chacune
  - Tuiles 33-36 : 4 vers chacune

### Déroulement d'un tour

#### 1. Lancer les 8 dés
À son tour, le joueur lance les 8 dés.

#### 2. Choisir un chiffre ou un ver
- Après chaque lancer, le joueur choisit un nombre ou le symbole "ver" apparaissant sur au moins un dé
- Il met de côté **tous les dés** de cette valeur
- Il relance les dés restants
- **Important** : À chaque lancer suivant, il doit choisir une valeur qu'il n'a pas encore mise de côté lors de ce tour
- Il n'est pas possible de réserver deux fois la même valeur lors du même tour

#### 3. Arrêter ou continuer
- Le joueur peut relancer les dés tant qu'il lui reste des dés et qu'il peut mettre de côté une valeur non encore obtenue
- Dès qu'il ne peut plus mettre de dés de côté avec une valeur nouvelle, son tour s'arrête et il rate ce tour

#### 4. Prendre une tuile/Un Pikomino
Pour prendre une tuile, il faut :
- Que la somme des dés mis de côté (en comptant les dés "vers" comme des 5) soit **égale ou supérieure** à la valeur d'une tuile disponible
- **ET** avoir au moins un "ver" mis de côté

Si ces conditions sont remplies, le joueur prend la tuile correspondante dans la réserve ou éventuellement sur le dessus de la pile d'un autre joueur.

### Cas particuliers et précisions

#### Tour raté - Perte de tuile et retrait du centre
Si un joueur ne peut pas réserver une nouvelle valeur de dés **OU** ne peut pas prendre de tuile car il n'a pas de "ver" ou ne peut atteindre aucune tuile :
- Il perd son tour et doit **remettre sa tuile du dessus** (s'il en a une) face cachée ou dans la réserve
- **En plus**, la **tuile la plus haute du centre** est retirée du jeu
- Ces tuiles retirées ne comptent pas à la fin et ne peuvent plus être prises

#### Vol de tuile chez un autre joueur
- Si le joueur fait le **score exact** du Pikomino du dessus de la pile d'un autre joueur, il lui vole cette tuile
- La tuile volée est placée au-dessus de sa propre pile
- **Important** : Il faut un score exactement égal, pas supérieur

#### Fin de partie
La partie se termine quand il n'y a plus de tuile Pikomino au centre de la table. Les joueurs comptent le nombre de vers sur leurs tuiles et celui qui en a le plus gagne.

#### Règles supplémentaires
- **Valeurs des dés** : Les dés vont de 1 à 5, le symbole "ver" compte comme 5 points, mais il faut au moins un "ver" pour prétendre à une tuile
- **Tuiles retournées** : Les tuiles perdues (face cachée) sont retirées de la partie et ne comptent pas à la fin
- **Obligation de s'arrêter** : Un joueur doit s'arrêter s'il n'a plus de dés à lancer, ou s'il ne peut pas choisir une valeur nouvelle
- **Tuiles déjà retirées** : Lorsqu'une tuile n'est plus présente dans la réserve ni dans les piles des autres (c'est-à-dire déjà retirée), elle ne peut plus être prise

## 🤖 Stratégies d'IA disponibles

### ConservativeStrategy
- S'arrête dès qu'elle peut prendre une tuile (≥21 points avec ver)
- Privilégie la sécurité over les gros scores
- Bonne pour éviter les échecs

### AggressiveStrategy
- Vise les tuiles de haute valeur (continue jusqu'à 30+ points)
- Prend plus de risques pour de meilleures récompenses
- Peut gagner gros ou échouer spectaculairement

## 🧪 Tests et qualité

Le projet inclut une suite de tests complète couvrant :

### Tests des règles de base
- Valeurs des dés et calcul des points
- Création et gestion des tuiles
- États de tour et réservation de dés

### Tests des cas particuliers
- Échec de tour avec perte de tuile du joueur et retrait du centre
- Vol de tuile avec score exact chez un autre joueur
- Impossibilité de réserver la même valeur deux fois
- Obligation d'avoir un ver pour prendre une tuile
- Tuiles retirées du jeu qui ne peuvent plus être prises

### Tests d'intégration
- Scénarios de tours complets réussis
- Différents types d'échecs de tour
- Gestion des stratégies d'IA
- État du jeu et fin de partie

### Lancer les tests

```bash
# Tests complets avec détails
pytest test_pikomino.py -v

# Tests avec couverture
pytest test_pikomino.py --cov=pikomino

# Tests spécifiques
pytest test_pikomino.py::TestGameSpecialCases -v
```

## 🔧 Développement

### Créer une nouvelle stratégie

```python
from pikomino import GameStrategy, TurnState, Player, DiceValue
from typing import Optional

class MaStrategie(GameStrategy):
    def choose_dice_value(self, turn_state: TurnState, player: Player) -> Optional[DiceValue]:
        # Logique pour choisir une valeur de dé
        available_values = [v for v in turn_state.current_roll 
                          if turn_state.can_reserve_value(v)]
        # Retourner le choix
        return available_values[0] if available_values else None
    
    def should_continue_turn(self, turn_state: TurnState, player: Player) -> bool:
        # Logique pour décider si continuer
        # Par exemple : continuer si < 25 points ou pas de ver
        return (turn_state.get_total_score() < 25 or 
                not turn_state.has_worm()) and turn_state.remaining_dice > 0
```

### Tester votre stratégie

```python
from pikomino import simulate_game
from ma_strategie import MaStrategie

# Tester votre stratégie
result = simulate_game(
    ["MaStrategie", "Conservative", "Aggressive"],
    [MaStrategie(), ConservativeStrategy(), AggressiveStrategy()]
)
print(f"Gagnant: {result['winner']}")
```

## 📊 Analyse des performances

Le fichier `examples.py` contient des outils pour :

- **Comparer les stratégies** sur de nombreuses parties
- **Analyser les statistiques** (taux de victoire, score moyen, etc.)
- **Tester des duels** entre stratégies spécifiques
- **Simuler des parties détaillées** avec historique complet

## 🌐 Interface Web

L'interface web offre :

- **Jeu interactif** : Jouez contre l'IA en temps réel
- **Visualisation en direct** : Voir l'état du jeu mis à jour automatiquement
- **Historique des tours** : Suivre le déroulement de la partie
- **Gestion des cas particuliers** : Affichage des tuiles perdues et retirées
- **Design responsive** : Compatible mobile et desktop
- **Animations fluides** : Expérience utilisateur optimisée

## ✅ Conformité aux règles

Cette implémentation respecte scrupuleusement les règles officielles du Pikomino :

- ✅ Gestion correcte des 8 dés avec valeurs 1-5 et symbole ver
- ✅ Tuiles 21-36 avec le bon nombre de vers (1-4)
- ✅ Interdiction de réserver la même valeur deux fois par tour
- ✅ Obligation d'avoir un ver pour prendre une tuile
- ✅ Vol de tuile avec score exact chez les autres joueurs
- ✅ Perte de tuile du joueur ET retrait du centre en cas d'échec
- ✅ Fin de partie quand plus de tuiles au centre
- ✅ Tuiles retirées définitivement du jeu

## 🤝 Contribution

Les contributions sont les bienvenues ! N'hésitez pas à :

1. Fork le projet
2. Créer une branche pour votre fonctionnalité
3. Implémenter vos modifications
4. **Ajouter des tests** pour vos nouvelles fonctionnalités
5. Vérifier que tous les tests passent
6. Soumettre une pull request

## 📜 Licence

Ce projet est sous licence MIT. Voir le fichier LICENSE pour plus de détails.

## 🎯 Prochaines fonctionnalités

- [ ] Statistiques détaillées des parties
- [ ] Stratégies d'IA encore plus sophistiquées
- [ ] Mode multijoueur en ligne
- [ ] Historique des parties sauvegardées
- [ ] Interface de création de stratégies visuelles

---

**Amusez-vous bien avec Pikomino !** 🐛🎲
     