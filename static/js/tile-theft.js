// Tile Theft Interface - Vol de tuiles intuitif pour Pikomino

/**
 * Affiche le message d'aide pour le vol de tuiles
 */
function showStealHelp() {
    const helpArea = document.getElementById('stealHelpArea');
    if (helpArea) {
        helpArea.style.display = 'block';
        
        // Masquer après 5 secondes
        setTimeout(() => {
            if (helpArea) helpArea.style.display = 'none';
        }, 5000);
    }
    
    // Mettre à jour l'affichage des joueurs pour montrer les tuiles volables
    updatePlayersPanel();
    updateCenterTiles();
}

/**
 * Masque le message d'aide
 */
function hideStealHelp() {
    const helpArea = document.getElementById('stealHelpArea');
    if (helpArea) {
        helpArea.style.display = 'none';
    }
}

/**
 * Ajoute un style de curseur pour les éléments cliquables
 */
function addClickableStyles() {
    // Ajouter un style CSS pour le curseur pointer
    const style = document.createElement('style');
    style.textContent = `
        .cursor-pointer {
            cursor: pointer !important;
        }
        .stealable-tile {
            animation: stealPulse 2s infinite;
        }
        .stealable-tile:hover {
            transform: scale(1.1);
        }
    `;
    document.head.appendChild(style);
}

/**
 * Met à jour l'interface lors du reset du tour
 */
function resetTurnStateExtended() {
    hideStealHelp();
    
    // Réinitialiser l'état du tour
    currentTurnState = {
        reservedDice: [],
        currentScore: 0,
        hasWorm: false,
        remainingDice: 8,
        usedValues: []
    };
    
    // Réinitialiser l'affichage des dés réservés
    resetDiceDisplay();
    
    // Mettre à jour l'affichage
    updatePlayersPanel();
    updateCenterTiles();
}

/**
 * Réinitialise complètement l'affichage des dés
 */
function resetDiceDisplay() {
    // Zones à réinitialiser
    const diceArea = document.getElementById('diceArea');
    const reservedArea = document.getElementById('reservedArea');
    const reservedDice = document.getElementById('reservedDice');
    const currentScore = document.getElementById('currentScore');
    const wormStatus = document.getElementById('wormStatus');
    const endTurnBtn = document.getElementById('endTurnBtn');
    const rollDiceBtn = document.getElementById('rollDiceBtn');
    const diceChoices = document.getElementById('diceChoices');
    const diceRoll = document.getElementById('diceRoll');
    
    // Cacher et réinitialiser toutes les zones
    if (diceArea) {
        diceArea.style.display = 'none';
    }
    if (reservedArea) {
        reservedArea.style.display = 'none';
    }
    if (reservedDice) {
        reservedDice.innerHTML = '';
    }
    if (currentScore) {
        currentScore.textContent = '0';
    }
    if (wormStatus) {
        wormStatus.textContent = '❌';
        wormStatus.className = 'text-danger';
    }
    if (endTurnBtn) {
        endTurnBtn.style.display = 'none';
    }
    if (rollDiceBtn) {
        rollDiceBtn.style.display = 'inline-block';
    }
    if (diceChoices) {
        diceChoices.innerHTML = '';
    }
    if (diceRoll) {
        diceRoll.innerHTML = '';
    }
}

/**
 * Gère le clic sur une tuile volable
 */
function handleTileSteal(playerName, tileValue) {
    if (!socket || !gameId) {
        console.error('Socket ou gameId non disponible');
        return;
    }
    
    // Confirmer le vol avec une petite animation
    const confirmation = confirm(`Voler la tuile ${tileValue} de ${playerName} ?`);
    if (!confirmation) return;
    
    // Émettre l'événement de vol
    socket.emit('choose_tile', {
        game_id: gameId,
        tile_choice: {
            source: 'player',
            value: tileValue,
            player: playerName
        }
    });
    
    // Réinitialiser l'interface immédiatement
    resetDiceDisplay();
    resetTurnStateExtended();
}

/**
 * Gère le clic sur une tuile du centre
 */
function handleCenterTileClick(tileValue) {
    if (!socket || !gameId) {
        console.error('Socket ou gameId non disponible');
        return;
    }
    
    // Prendre la tuile du centre
    socket.emit('choose_tile', {
        game_id: gameId,
        tile_choice: {
            source: 'center',
            value: tileValue,
            player: null
        }
    });
    
    // Réinitialiser l'interface immédiatement
    resetDiceDisplay();
    resetTurnStateExtended();
}

/**
 * Initialise les styles et événements pour le vol de tuiles
 */
function initializeTileTheft() {
    addClickableStyles();
    
    // Override resetTurnState pour inclure nos extensions
    if (typeof window.originalResetTurnState === 'undefined') {
        window.originalResetTurnState = resetTurnState;
        resetTurnState = resetTurnStateExtended;
    }
}

// Initialiser quand le DOM est prêt
document.addEventListener('DOMContentLoaded', function() {
    initializeTileTheft();
});

/**
 * Fonction appelée quand un tour se termine pour nettoyer l'interface
 */
function onTurnCompleted() {
    resetDiceDisplay();
    hideStealHelp();
    
    // Réinitialiser l'état du tour pour être sûr
    currentTurnState = {
        reservedDice: [],
        currentScore: 0,
        hasWorm: false,
        remainingDice: 8,
        usedValues: []
    };
}

/**
 * Gère la logique des boutons après un lancer de dés (logique de jeu stricte)
 */
function handleDiceRollLogic(diceData) {
    const rollDiceBtn = document.getElementById('rollDiceBtn');
    const endTurnBtn = document.getElementById('endTurnBtn');
    const choices = document.getElementById('diceChoices');
    
    if (!diceData || !choices) return;
    
    // Vérifier s'il y a des choix valides disponibles
    const uniqueValues = [...new Set(diceData.dice)];
    const usedValues = new Set(diceData.used_values || []);
    const hasValidChoices = uniqueValues.some(value => !usedValues.has(value));
    
    if (rollDiceBtn) {
        if (!hasValidChoices) {
            // Aucun choix valide = fin de tour forcée
            rollDiceBtn.style.display = 'none';
            if (endTurnBtn) {
                endTurnBtn.style.display = 'inline-block';
                endTurnBtn.textContent = 'Terminer le tour (obligatoire)';
                endTurnBtn.className = 'btn btn-warning';
            }
        } else {
            // Il y a des choix valides = le joueur DOIT choisir avant de relancer
            rollDiceBtn.style.display = 'none'; // Masqué jusqu'au choix
        }
    }
}

/**
 * Gère la logique après qu'un choix de dé ait été fait
 */
function handleChoiceMade(choiceData) {
    const rollDiceBtn = document.getElementById('rollDiceBtn');
    const endTurnBtn = document.getElementById('endTurnBtn');
    
    if (!choiceData.success) return;
    
    const details = choiceData.details;
    
    // Maintenant que le joueur a choisi, réafficher le bouton "Lancer les dés" s'il reste des dés
    if (rollDiceBtn && details.remaining_dice_count > 0) {
        rollDiceBtn.style.display = 'inline-block';
        rollDiceBtn.textContent = 'Lancer les dés';
        rollDiceBtn.className = 'btn btn-primary';
    }
    
    // Remettre le bouton "Terminer le tour" dans son état normal
    if (endTurnBtn) {
        endTurnBtn.textContent = 'Terminer le tour';
        endTurnBtn.className = 'btn btn-success';
    }
}

// Exporter les fonctions pour utilisation globale
window.showStealHelp = showStealHelp;
window.hideStealHelp = hideStealHelp;
window.handleTileSteal = handleTileSteal;
window.handleCenterTileClick = handleCenterTileClick;
window.onTurnCompleted = onTurnCompleted;
window.resetDiceDisplay = resetDiceDisplay;
window.handleDiceRollLogic = handleDiceRollLogic;
window.handleChoiceMade = handleChoiceMade; 