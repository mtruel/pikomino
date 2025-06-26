#!/usr/bin/env python3
"""
Analyse pour déterminer la stratégie optimale au Pikomino
"""

from pikomino import simulate_game, DiceValue
from strategies import (
    ConservativeStrategy, AggressiveStrategy, BalancedStrategy, 
    TargetedStrategy, RandomStrategy
)
import statistics
from collections import defaultdict

def analyze_tile_values():
    """Analyse la distribution des vers par tuile"""
    print("📊 ANALYSE DES VALEURS DES TUILES")
    print("=" * 50)
    
    # Mapping exact des tuiles Pikomino
    tile_mapping = {
        21: 1, 22: 1, 23: 1, 24: 1,    # 4 tuiles à 1 ver
        25: 2, 26: 2, 27: 2, 28: 2,    # 4 tuiles à 2 vers  
        29: 3, 30: 3, 31: 3, 32: 3,    # 4 tuiles à 3 vers
        33: 4, 34: 4, 35: 4, 36: 4,    # 4 tuiles à 4 vers
    }
    
    print("Distribution des tuiles:")
    for value, worms in tile_mapping.items():
        print(f"  Tuile {value}: {worms} vers")
    
    print("\nObservations clés:")
    print("  • 4 tuiles faciles (21-24): 1 ver chacune = 4 vers total")
    print("  • 4 tuiles moyennes (25-28): 2 vers chacune = 8 vers total") 
    print("  • 4 tuiles difficiles (29-32): 3 vers chacune = 12 vers total")
    print("  • 4 tuiles très difficiles (33-36): 4 vers chacune = 16 vers total")
    print("  • TOTAL: 40 vers disponibles dans le jeu")
    
    # Calcul du seuil de rentabilité
    print("\n💡 SEUILS STRATÉGIQUES:")
    print("  • Score 21-24: Accès aux tuiles de base (faible récompense)")
    print("  • Score 25-28: Accès aux tuiles moyennes (bon rapport)")  
    print("  • Score 29-32: Accès aux tuiles hautes (très bon rapport)")
    print("  • Score 33-36: Accès aux tuiles maximum (excellent rapport)")
    
    return tile_mapping

def analyze_dice_probabilities():
    """Analyse les probabilités des dés"""
    print("\n🎲 ANALYSE DES PROBABILITÉS DE DÉS")
    print("=" * 50)
    
    # Chaque dé a 6 faces avec probabilité 1/6 chacune
    dice_values = {
        "1": (1, 1/6),
        "2": (2, 1/6), 
        "3": (3, 1/6),
        "4": (4, 1/6),
        "5": (5, 1/6),
        "VER": (5, 1/6),  # Le ver vaut 5 points
    }
    
    print("Valeurs et probabilités:")
    for face, (points, prob) in dice_values.items():
        print(f"  {face}: {points} points, {prob:.3f} probabilité")
    
    # Espérance de gain par dé
    expected_value = sum(points * prob for points, prob in dice_values.values())
    print(f"\nEspérance par dé: {expected_value:.2f} points")
    print(f"Espérance 8 dés: {expected_value * 8:.1f} points")
    
    print("\n💡 OBSERVATIONS:")
    print("  • Les vers sont OBLIGATOIRES mais valent seulement 5 points")
    print("  • Optimal théorique: réserver vers + 5s en priorité") 
    print("  • Mais fréquence compte: 3 dés 'ONE' = 3 points vs 1 dé 'FIVE' = 5 points")

def analyze_risk_reward():
    """Analyse du rapport risque/récompense"""
    print("\n⚖️ ANALYSE RISQUE/RÉCOMPENSE")
    print("=" * 50)
    
    print("RÉCOMPENSES (prendre une tuile):")
    print("  • Tuile 21-24: +1 ver (gain faible)")
    print("  • Tuile 25-28: +2 vers (gain moyen)")
    print("  • Tuile 29-32: +3 vers (gain élevé)")
    print("  • Tuile 33-36: +4 vers (gain maximum)")
    print("  • VOL: +X vers PLUS enlever X vers à l'adversaire (double impact!)")
    
    print("\nRISQUES (rater un tour):")
    print("  • Perte de sa meilleure tuile (perte variable)")
    print("  • Retrait de la plus haute tuile du centre (perte collective)")
    print("  • Réduction des options futures")
    
    print("\n💡 SEUILS OPTIMAUX THÉORIQUES:")
    print("  • Score 21-24: Risque élevé, récompense faible -> PRENDRE")
    print("  • Score 25-28: Équilibre correct -> ÉVALUER")
    print("  • Score 29-32: Très bon rapport -> VISER si possible")
    print("  • Score 33+: Excellent mais très risqué -> Situation dépendante")

def test_optimal_strategy_theory():
    """Test des hypothèses de stratégie optimale"""
    print("\n🧪 TEST DES HYPOTHÈSES STRATÉGIQUES")
    print("=" * 50)
    
    # Créer une stratégie optimale théorique
    class OptimalStrategy(ConservativeStrategy):  # Héritage pour structure de base
        def choose_dice_value(self, turn_state, player):
            available_values = [
                v for v in turn_state.current_roll 
                if turn_state.can_reserve_value(v)
            ]
            
            if not available_values:
                return None
            
            # PRIORITÉ 1: Assurer un ver si pas encore obtenu
            if DiceValue.WORM in available_values and not turn_state.has_worm():
                return DiceValue.WORM
            
            # PRIORITÉ 2: Si peu de dés restants, maximiser la valeur  
            if turn_state.remaining_dice <= 3:
                return max(available_values, key=lambda v: v.value if v != DiceValue.WORM else 5)
            
            # PRIORITÉ 3: Équilibrer fréquence et valeur
            scores = {}
            for value in available_values:
                count = turn_state.current_roll.count(value)
                points = value.value if value != DiceValue.WORM else 5
                # Formule: fréquence × valeur avec bonus pour fréquence élevée
                scores[value] = count * points + (count - 1)  # Bonus fréquence
                
            return max(scores.keys(), key=lambda v: scores[v])
        
        def should_continue_turn(self, turn_state, player):
            score = turn_state.get_total_score()
            
            # Ne peut pas continuer sans dés
            if turn_state.remaining_dice == 0:
                return False
                
            # Doit continuer si ne peut pas prendre de tuile
            if score < 21 or not turn_state.has_worm():
                return True
            
            # SEUILS ADAPTATIFS basés sur les dés restants
            if turn_state.remaining_dice >= 5:
                target = 28  # Viser tuiles moyennes avec beaucoup de dés
            elif turn_state.remaining_dice >= 3:
                target = 25  # Seuil conservateur avec dés moyens
            else:
                target = 21  # Sécuriser avec peu de dés
                
            return score < target
        
        def choose_target_tile(self, score, has_worm, center_tiles, stealable_tiles, current_player):
            if not has_worm:
                return None
            
            # PRIORITÉ 1: VOL si ratio intéressant
            if stealable_tiles:
                # Calculer l'impact du vol (gain + perte adversaire)
                best_steal = max(stealable_tiles, key=lambda x: x[0].worms)
                steal_impact = best_steal[0].worms * 2  # Double impact
                
                # Comparer avec la meilleure tuile du centre
                if center_tiles:
                    best_center = max(center_tiles, key=lambda t: t.worms)
                    if steal_impact >= best_center.worms:
                        return best_steal[0]  # Vol plus intéressant
                else:
                    return best_steal[0]  # Pas d'alternative au centre
            
            # PRIORITÉ 2: Maximiser les vers du centre
            if center_tiles:
                return max(center_tiles, key=lambda t: t.worms)
                
            return None
    
    return OptimalStrategy

def run_strategy_tournament():
    """Tournament entre toutes les stratégies pour identifier la meilleure"""
    print("\n🏆 TOURNAMENT DES STRATÉGIES")
    print("=" * 50)
    
    OptimalStrategy = test_optimal_strategy_theory()
    
    strategies = {
        "Optimal": OptimalStrategy(),
        "Conservative": ConservativeStrategy(),
        "Aggressive": AggressiveStrategy(), 
        "Balanced": BalancedStrategy(),
        "TargetHigh": TargetedStrategy(min_target_value=29),
        "Random": RandomStrategy(0.5),
    }
    
    num_games = 100
    results = defaultdict(lambda: {"wins": 0, "scores": [], "avg_score": 0})
    
    print(f"Simulation de {num_games} parties à 4 joueurs chacune...")
    
    for game_num in range(num_games):
        # Partie à 4 joueurs avec stratégies variées
        player_names = list(strategies.keys())[:4]  # 4 premiers
        game_strategies = [strategies[name] for name in player_names]
        
        result = simulate_game(player_names, game_strategies)
        
        # Enregistrer les résultats
        for name in player_names:
            score = result["final_scores"][name]
            results[name]["scores"].append(score)
            if result["winner"] == name:
                results[name]["wins"] += 1
    
    # Calculer les moyennes
    for name in results:
        results[name]["avg_score"] = statistics.mean(results[name]["scores"])
    
    # Afficher les résultats triés
    print("\n📊 RÉSULTATS DU TOURNAMENT:")
    sorted_strategies = sorted(results.items(), key=lambda x: x[1]["avg_score"], reverse=True)
    
    for i, (name, data) in enumerate(sorted_strategies):
        position = ["🥇", "🥈", "🥉", "4️⃣", "5️⃣", "6️⃣"][i]
        win_rate = (data["wins"] / num_games) * 100
        print(f"{position} {name:12}: {win_rate:5.1f}% victoires, {data['avg_score']:5.2f} vers/partie")
    
    return sorted_strategies[0][0]  # Retourner le nom de la meilleure stratégie

def main():
    """Analyse complète pour déterminer la stratégie optimale"""
    print("🎯 RECHERCHE DE LA STRATÉGIE OPTIMALE PIKOMINO")
    print("=" * 60)
    
    # Analyses théoriques
    analyze_tile_values()
    analyze_dice_probabilities()
    analyze_risk_reward()
    
    # Test pratique
    best_strategy = run_strategy_tournament()
    
    print(f"\n🏆 CONCLUSION:")
    print(f"   La stratégie '{best_strategy}' performe le mieux!")
    print(f"\n💡 STRATÉGIE OPTIMALE RECOMMANDÉE:")
    print(f"   1. 🎲 Assurer un ver en priorité")
    print(f"   2. ⚖️ Équilibrer fréquence × valeur des dés")
    print(f"   3. 📈 Adapter les seuils selon les dés restants")
    print(f"   4. 🥷 Privilégier le vol si impact double supérieur")
    print(f"   5. 🎯 Viser les tuiles 25-32 (meilleur rapport)")

if __name__ == "__main__":
    main() 