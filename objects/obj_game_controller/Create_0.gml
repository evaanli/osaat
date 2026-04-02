global.gamestate = [
	100, // player 1 x
	200, // player 1 y
	0,   // player 1 xvel
	0,   // player 1 yvel
	90,  // player 1 gun direction
	1200,// player 2 x
	200, // player 2 y
	0,   // player 2 xvel
	0,   // player 2 yvel
	270  // player 2 gun direction
]

global.current_state = "record1t";

// Tracking for player movements
global.record1 = [];
global.record2 = [];

// Tracking for projectile movements
global.record1_projectiles = [];
global.record2_projectiles = [];

// Replay shot indexes for each player
global.replay_shot_index1 = 0;
global.replay_shot_index2 = 0;

global.time = 0;
global.time_limit = 3;

function reset_players() {
	with (obj_player1) {
		x = global.gamestate[0];
		y = global.gamestate[1];
		x_vel = global.gamestate[2];
		y_vel = global.gamestate[3];
	
	}

	with (obj_player2) {
		x = global.gamestate[5];
		y = global.gamestate[6];
		x_vel = global.gamestate[7];
		y_vel = global.gamestate[8];
	}
}