#!/usr/bin/env python3
"""
Test et validation de la stratégie optimale
"""

from pikomino import simulate_game
from strategies import (
    OptimalStrategy, ConservativeStrategy, AggressiveStrategy, 
    BalancedStrategy, TargetedStrategy, RandomStrategy
)
import statistics
import time

def comprehensive_tournament():
    """Tournament complet entre toutes les stratégies"""
    print("🏆 TOURNAMENT COMPLET DES STRATÉGIES")
    print("=" * 60)
    
    strategies = {
        "OptimalStrategy": OptimalStrategy(),
        "Conservative": ConservativeStrategy(),
        "Aggressive": AggressiveStrategy(), 
        "Balanced": BalancedStrategy(),
        "TargetHigh30": TargetedStrategy(min_target_value=30),
        "TargetHigh32": TargetedStrategy(min_target_value=32),
        "Random50": RandomStrategy(0.5),
        "RandomCautious": RandomStrategy(0.3),
        "RandomRisky": RandomStrategy(0.7),
    }
    
    num_games = 200  # Plus de parties pour plus de précision
    results = {name: {"wins": 0, "scores": [], "total_tiles": []} for name in strategies}
    
    print(f"🎮 Simulation de {num_games} parties avec toutes les stratégies...")
    print("   (Cela peut prendre quelques secondes)")
    
    start_time = time.time()
    
    for game_num in range(num_games):
        if (game_num + 1) % 50 == 0:
            print(f"   Partie {game_num + 1}/{num_games} terminée...")
        
        # Partie à 4 joueurs (rotation pour équité)
        strategy_names = list(strategies.keys())
        selected_names = strategy_names[game_num % len(strategy_names):game_num % len(strategy_names) + 4]
        if len(selected_names) < 4:
            selected_names.extend(strategy_names[:4 - len(selected_names)])
        
        selected_strategies = [strategies[name] for name in selected_names]
        
        result = simulate_game(selected_names, selected_strategies)
        
        # Enregistrer les résultats
        for name in selected_names:
            score = result["final_scores"][name]
            tiles = result["final_tiles"][name]
            
            results[name]["scores"].append(score)
            results[name]["total_tiles"].append(tiles)
            
            if result["winner"] == name:
                results[name]["wins"] += 1
    
    elapsed = time.time() - start_time
    
    # Calculer les statistiques
    for name in results:
        data = results[name]
        if data["scores"]:
            data["avg_score"] = statistics.mean(data["scores"])
            data["avg_tiles"] = statistics.mean(data["total_tiles"])
            data["score_stdev"] = statistics.stdev(data["scores"]) if len(data["scores"]) > 1 else 0
            data["games_played"] = len(data["scores"])
            data["win_rate"] = (data["wins"] / data["games_played"]) * 100 if data["games_played"] > 0 else 0
    
    # Trier par score moyen
    sorted_results = sorted(
        [(name, data) for name, data in results.items() if data["scores"]], 
        key=lambda x: x[1]["avg_score"], 
        reverse=True
    )
    
    print(f"\n📊 RÉSULTATS FINAUX ({elapsed:.1f}s):")
    print("=" * 80)
    print(f"{'Rang':<6} {'Stratégie':<15} {'Victoires':<10} {'Score Moy.':<12} {'Tuiles Moy.':<12} {'Parties':<8}")
    print("-" * 80)
    
    for i, (name, data) in enumerate(sorted_results):
        position = ["🥇", "🥈", "🥉"] + ["  "] * 10
        rank_icon = position[i] if i < len(position) else "  "
        
        print(f"{rank_icon:<6} {name:<15} {data['win_rate']:>6.1f}%   {data['avg_score']:>8.2f}   {data['avg_tiles']:>8.2f}     {data['games_played']:>6}")
    
    return sorted_results

def detailed_analysis():
    """Analyse détaillée de la stratégie optimale"""
    print("\n🔍 ANALYSE DÉTAILLÉE DE LA STRATÉGIE OPTIMALE")
    print("=" * 60)
    
    # Test spécifique OptimalStrategy vs meilleures stratégies existantes
    matchups = [
        ("OptimalStrategy", OptimalStrategy(), "Conservative", ConservativeStrategy()),
        ("OptimalStrategy", OptimalStrategy(), "Aggressive", AggressiveStrategy()),
        ("OptimalStrategy", OptimalStrategy(), "Balanced", BalancedStrategy()),
        ("OptimalStrategy", OptimalStrategy(), "TargetHigh30", TargetedStrategy(min_target_value=30)),
    ]
    
    print("Duels 1v1 avec la stratégie optimale:")
    print("-" * 50)
    
    for name1, strat1, name2, strat2 in matchups:
        wins1 = wins2 = 0
        scores1 = []
        scores2 = []
        
        num_duels = 100
        
        for _ in range(num_duels):
            result = simulate_game([name1, name2], [strat1, strat2])
            
            score1 = result["final_scores"][name1]
            score2 = result["final_scores"][name2]
            
            scores1.append(score1)
            scores2.append(score2)
            
            if score1 > score2:
                wins1 += 1
            elif score2 > score1:
                wins2 += 1
        
        avg1 = statistics.mean(scores1)
        avg2 = statistics.mean(scores2)
        
        print(f"\n{name1} vs {name2} ({num_duels} parties):")
        print(f"  {name1:15}: {wins1:3d} victoires ({wins1/num_duels*100:5.1f}%), {avg1:5.2f} vers/partie")
        print(f"  {name2:15}: {wins2:3d} victoires ({wins2/num_duels*100:5.1f}%), {avg2:5.2f} vers/partie")
        
        if wins1 > wins2:
            advantage = ((wins1 - wins2) / num_duels) * 100
            print(f"  → {name1} domine avec {advantage:.1f}% d'avantage")
        elif wins2 > wins1:
            advantage = ((wins2 - wins1) / num_duels) * 100
            print(f"  → {name2} domine avec {advantage:.1f}% d'avantage")
        else:
            print(f"  → Égalité parfaite!")

def validate_optimality():
    """Validation des principes de la stratégie optimale"""
    print("\n✅ VALIDATION DES PRINCIPES OPTIMAUX")
    print("=" * 50)
    
    principles = [
        "1. 🎲 Assurer un ver en priorité absolue",
        "2. ⚖️ Équilibrer fréquence × valeur + bonus fréquence", 
        "3. 📈 Seuils adaptatifs selon les dés restants",
        "4. 🥷 Vol privilégié si impact double supérieur",
        "5. 🎯 Cibler la zone de rentabilité optimale (25-32)"
    ]
    
    print("Principes de la stratégie optimale:")
    for principle in principles:
        print(f"  {principle}")
    
    print("\n📋 Justifications théoriques:")
    print("  • Ver obligatoire → Priorité absolue pour éviter l'échec")
    print("  • Fréquence importante → Bonus pour groupes de dés identiques")
    print("  • Dés restants → Plus de dés = plus de risque acceptable")
    print("  • Vol = double impact → Gain + perte adversaire")
    print("  • Zone 25-32 → Meilleur rapport risque/récompense")

def main():
    """Exécution complète des tests"""
    print("🎯 VALIDATION COMPLÈTE DE LA STRATÉGIE OPTIMALE")
    print("=" * 70)
    
    # Tournament complet
    tournament_results = comprehensive_tournament()
    
    # Vérifier si OptimalStrategy est effectivement la meilleure
    best_strategy = tournament_results[0][0]
    if best_strategy == "OptimalStrategy":
        print(f"\n🎉 SUCCÈS! OptimalStrategy est effectivement la meilleure!")
    else:
        print(f"\n🤔 SURPRISE! {best_strategy} surpasse OptimalStrategy...")
        print("   → Analyse nécessaire pour améliorer la stratégie")
    
    # Analyse détaillée
    detailed_analysis()
    
    # Validation des principes
    validate_optimality()
    
    print(f"\n🏆 CONCLUSION FINALE:")
    if best_strategy == "OptimalStrategy":
        print("   ✅ La stratégie optimale développée est validée!")
        print("   ✅ Elle surpasse toutes les autres stratégies testées")
        print("   ✅ Les principes théoriques sont confirmés par les résultats")
    else:
        print(f"   ⚠️  {best_strategy} performe mieux qu'OptimalStrategy")
        print("   🔍 Analyse supplémentaire recommandée")
    
    return best_strategy

if __name__ == "__main__":
    best = main()
    print(f"\n🎖️  Meilleure stratégie identifiée: {best}") 