from flask import Flask, render_template, request, jsonify, session
from flask_socketio import SocketIO, emit, join_room, leave_room
import uuid
from typing import Dict, Optional
import json

from pikomino import (
    Player, PikominoGame, ConservativeStrategy, AggressiveStrategy,
    DiceValue, TurnResult
)

app = Flask(__name__)
app.config['SECRET_KEY'] = 'pikomino-secret-key-for-sessions'
socketio = SocketIO(app, cors_allowed_origins="*")

# Stockage des parties en cours
games: Dict[str, PikominoGame] = {}
game_sessions: Dict[str, str] = {}  # session_id -> game_id


class HumanStrategy:
    """Stratégie pour les joueurs humains via l'interface web"""
    
    def __init__(self):
        self.pending_choice = None
        self.choice_made = False
    
    def choose_dice_value(self, turn_state, player):
        # Cette méthode sera appelée par l'interface web
        return self.pending_choice
    
    def should_continue_turn(self, turn_state, player):
        # Pour l'instant, toujours continuer (sera géré par l'interface)
        return True


@app.route('/')
def index():
    """Page d'accueil"""
    return render_template('index.html')


@app.route('/game/<game_id>')
def game_view(game_id):
    """Vue de jeu"""
    if game_id not in games:
        return "Partie non trouvée", 404
    
    game = games[game_id]
    return render_template('game.html', 
                         game_id=game_id,
                         game_state=game.get_game_state())


@app.route('/api/create_game', methods=['POST'])
def create_game():
    """Crée une nouvelle partie"""
    data = request.json
    player_names = data.get('players', ['Alice', 'Bob', 'Charlie'])
    
    # Créer les joueurs avec des stratégies par défaut
    players = []
    for i, name in enumerate(player_names):
        if i == 0:  # Premier joueur humain
            strategy = HumanStrategy()
        else:  # Autres joueurs IA
            strategy = ConservativeStrategy() if i % 2 == 1 else AggressiveStrategy()
        players.append(Player(name, strategy))
    
    # Créer la partie
    game = PikominoGame(players)
    game_id = str(uuid.uuid4())
    games[game_id] = game
    
    return jsonify({
        'game_id': game_id,
        'game_state': game.get_game_state()
    })


@app.route('/api/game/<game_id>/state')
def get_game_state(game_id):
    """Récupère l'état actuel de la partie"""
    if game_id not in games:
        return jsonify({'error': 'Partie non trouvée'}), 404
    
    game = games[game_id]
    return jsonify(game.get_game_state())


@app.route('/api/game/<game_id>/play_turn', methods=['POST'])
def play_turn(game_id):
    """Joue un tour automatique (pour l'IA)"""
    if game_id not in games:
        return jsonify({'error': 'Partie non trouvée'}), 404
    
    game = games[game_id]
    current_player = game.get_current_player()
    
    # Vérifier si c'est un joueur IA
    if isinstance(current_player.strategy, HumanStrategy):
        return jsonify({'error': 'Tour du joueur humain'}), 400
    
    # Jouer le tour
    result, details = game.play_turn()
    game.next_player()
    
    return jsonify({
        'result': result.value,
        'details': details,
        'game_state': game.get_game_state()
    })


@socketio.on('join_game')
def on_join_game(data):
    """Un joueur rejoint une partie"""
    game_id = data['game_id']
    if game_id in games:
        join_room(game_id)
        game_sessions[session.get('session_id', str(uuid.uuid4()))] = game_id
        emit('game_state', games[game_id].get_game_state())


@socketio.on('leave_game')
def on_leave_game(data):
    """Un joueur quitte une partie"""
    game_id = data['game_id']
    leave_room(game_id)
    session_id = session.get('session_id')
    if session_id in game_sessions:
        del game_sessions[session_id]


@socketio.on('roll_dice')
def on_roll_dice(data):
    """Lance les dés pour le joueur actuel"""
    game_id = data['game_id']
    
    if game_id not in games:
        emit('error', {'message': 'Partie non trouvée'})
        return
    
    game = games[game_id]
    current_player = game.get_current_player()
    
    # Vérifier si c'est un joueur humain
    if not isinstance(current_player.strategy, HumanStrategy):
        emit('error', {'message': 'Ce n\'est pas votre tour'})
        return
    
    # Simuler le lancement de dés (sera intégré dans le système de tour complet)
    from pikomino import Dice
    remaining_dice = data.get('remaining_dice', 8)
    roll = [Dice.roll() for _ in range(remaining_dice)]
    
    emit('dice_rolled', {
        'dice': [die.name for die in roll],
        'remaining': remaining_dice
    }, room=game_id)


@socketio.on('choose_dice_value')
def on_choose_dice_value(data):
    """Le joueur choisit une valeur de dé"""
    game_id = data['game_id']
    chosen_value = data['value']
    
    if game_id not in games:
        emit('error', {'message': 'Partie non trouvée'})
        return
    
    game = games[game_id]
    current_player = game.get_current_player()
    
    if isinstance(current_player.strategy, HumanStrategy):
        # Convertir la valeur string en DiceValue
        try:
            dice_value = DiceValue[chosen_value.upper()]
            current_player.strategy.pending_choice = dice_value
            current_player.strategy.choice_made = True
            
            emit('choice_made', {
                'player': current_player.name,
                'choice': chosen_value
            }, room=game_id)
            
        except KeyError:
            emit('error', {'message': 'Valeur de dé invalide'})


def create_app():
    """Factory pour créer l'application Flask"""
    return app


if __name__ == '__main__':
    socketio.run(app, debug=True, host='0.0.0.0', port=5000) 