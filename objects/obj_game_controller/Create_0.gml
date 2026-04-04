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

global.player1_max_hp = 3;
global.player2_max_hp = 3;

function reset_game() {
    global.map = "circles";
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
  
    // Game variables
    global.time = 0;
    global.time_limit = 3;
    global.winner = noone;
    
    obj_player1.hp = global.player1_max_hp;
    obj_player2.hp = global.player1_max_hp;
}

reset_game();

// Graphics/Decoration variables
transparency_speed = 0.005;
flashed = 0; // Counter for player flashes
show_game_over_text = false;

// Custom fonts
game_over_font = font_add("fnt_game_over.ttf", 30, false, false, 32, 126);

function reset_players() {
	with (obj_player1) {
		x = global.last_recorded_state[0];
		y = global.last_recorded_state[1];
		x_vel = global.last_recorded_state[2];
		y_vel = global.last_recorded_state[3];
		last_shot = last_shot - global.time_limit;
		just_shot = false;
        
        image_alpha = 1;
	}

	with (obj_player2) {
		x = global.last_recorded_state[5];
		y = global.last_recorded_state[6];
		x_vel = global.last_recorded_state[7];
		y_vel = global.last_recorded_state[8];
		last_shot = last_shot - global.time_limit;
		just_shot = false;
        
        image_alpha = 1;
	}
    
    with (obj_arena_parent) {
        obj_arena_parent.image_alpha = 1;
    }
}