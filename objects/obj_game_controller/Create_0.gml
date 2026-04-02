global.last_recorded_state = [
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
global.player1_recording = [];
global.player2_recording = [];

// Tracking for projectile movements
global.player1_recording_projectiles = [];
global.player2_recording_projectiles = [];

// Replay shot indexes for each player
global.replay_shot_index1 = 0;
global.replay_shot_index2 = 0;

global.time = 0;
global.time_limit = 3;

// Graphics/Decoration variables
transparency_speed = 0.005;

function reset_players() {
	with (obj_player1) {
		x = global.last_recorded_state[0];
		y = global.last_recorded_state[1];
		x_vel = global.last_recorded_state[2];
		y_vel = global.last_recorded_state[3];
		last_shot = last_shot - global.time_limit;
		just_shot = false;
	}

	with (obj_player2) {
		x = global.last_recorded_state[5];
		y = global.last_recorded_state[6];
		x_vel = global.last_recorded_state[7];
		y_vel = global.last_recorded_state[8];
		last_shot = last_shot - global.time_limit;
		just_shot = false;
	}
}