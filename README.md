# Pikomino : Simulateur de jeu

Un simulateur complet du jeu de société **Pikomino** avec interface web interactive et système d'IA pour tester différentes stratégies.

## 🎲 Caractéristiques

- **Interface web moderne** avec Flask et Socket.IO pour jouer en temps réel
- **Moteur de jeu complet** respectant toutes les règles du Pikomino
- **Système d'IA avancé** avec différentes stratégies (conservative, agressive, équilibrée)
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

### Déroulement d'un tour
1. **Lancer les 8 dés** (faces 1-5 et symbole ver)
2. **Choisir une valeur** apparaissant sur au moins un dé
3. **Mettre de côté tous les dés** de cette valeur
4. **Relancer les dés restants** (si possible)
5. **Répéter** avec une valeur différente à chaque fois

### Conditions pour prendre une tuile
- Avoir **au moins un ver** mis de côté
- Avoir un **score total ≥** à la valeur de la tuile
- Les vers valent **5 points** chacun

### Cas d'échec
Si vous ne pouvez pas choisir une nouvelle valeur :
- Vous perdez votre tuile du dessus
- La tuile la plus haute du centre est retirée du jeu

## 🤖 Stratégies d'IA disponibles

### ConservativeStrategy
- S'arrête dès qu'elle peut prendre une tuile
- Privilégie la sécurité over les gros scores
- Bonne pour éviter les échecs

### AggressiveStrategy
- Vise les tuiles de haute valeur (30+ points)
- Prend plus de risques
- Peut gagner gros ou échouer

### BalancedStrategy
- Adapte son comportement selon le contexte
- Équilibre entre sécurité et ambition
- Stratégie polyvalente

### WormFocusedStrategy
- Se concentre sur obtenir des vers rapidement
- S'arrête dès qu'elle a un ver et 21+ points
- Stratégie minimaliste

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
        return turn_state.get_total_score() < 25
```

### Lancer des tests

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
- **Design responsive** : Compatible mobile et desktop
- **Animations fluides** : Expérience utilisateur optimisée

## 🤝 Contribution

Les contributions sont les bienvenues ! N'hésitez pas à :

1. Fork le projet
2. Créer une branche pour votre fonctionnalité
3. Implémenter vos modifications
4. Ajouter des tests si nécessaire
5. Soumettre une pull request

## 📜 Licence

Ce projet est sous licence MIT. Voir le fichier LICENSE pour plus de détails.

## 🎯 Prochaines fonctionnalités

- [ ] Mode multijoueur en ligne
- [ ] Sauvegarde/reprise de parties
- [ ] Statistiques avancées des joueurs
- [ ] Tournois automatisés
- [ ] Export des résultats en CSV
- [ ] API REST pour l'intégration

---

**Amusez-vous bien avec Pikomino !** 🐛🎲
     