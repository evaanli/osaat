global.dt = delta_time / game_get_speed(gamespeed_microseconds);
if (global.current_state == "replaya") {
	// Slowly make the characters more transparent
	obj_player1.image_alpha -= transparency_speed;
	obj_player2.image_alpha -= transparency_speed;
	obj_arena_parent.image_alpha -= transparency_speed;
	
	// If the player becomes fully transparent then move to the next state
	if (obj_player1.image_alpha <= 0) {
		global.current_state = "record1t";
	}
} else if (global.current_state == "record1t") {
    reset_players(); // Reset the players to previous state
	// Reset the image transparency to full
	obj_player1.image_alpha = 1;
	obj_player2.image_alpha = 1;
    obj_arena_parent.image_alpha = 1;
	// Create a ready button if there isn't one already
	if (!instance_exists(obj_ready_button)) {
		instance_create_layer(room_width / 2, room_height / 2, "User_Interface", obj_ready_button);
	}
	
	// Waits for the button to be pressed
	
	// Resets the time
    global.time = 0;
} else if (global.current_state == "record1") {
    // Record x, y, velocity and time for player 1 INCLUDING IF CURRENTLY SHOOTING
	array_push(global.player1_recording, [obj_player1.x, obj_player1.y, obj_player1.x_vel, obj_player1.y_vel, obj_player1.just_shot, global.time]);
	
	// Add time with deltatime
    global.time += global.dt * 1/60;
	
	// Check if the time is over/equal the time limit
	if (global.time >= global.time_limit) {
		// If so, set the current state to the next transition (player2)
        global.current_state = "record1a";
		
        // show_debug_message(global.player1_recording);
    }
} else if (global.current_state == "record1a") {
	// Slowly make the characters more transparent
	obj_player1.image_alpha -= transparency_speed;
	obj_player2.image_alpha -= transparency_speed;
    obj_arena_parent.image_alpha -= transparency_speed;
	
	// If the player becomes fully transparent then move to the next state
	if (obj_player1.image_alpha <= 0) {
		global.current_state = "record2t";
	}
} else if (global.current_state == "record2t")  {
	
    reset_players(); // Reset the players to previous state
	// Reset the image transparency to full
	obj_player1.image_alpha = 1;
	obj_player2.image_alpha = 1;
    obj_arena_parent.image_alpha = 1;
	// Create a ready button if there isn't one already
	if (!instance_exists(obj_ready_button)) {
		instance_create_layer(room_width / 2, room_height / 2, recording, obj_ready_button);
	}
	
	// Waits for the button to be pressed
	
	// Resets the time
    global.time = 0;
} else if (global.current_state == "record2") {
    // Record x, y, velocity and time
	array_push(global.player2_recording, [obj_player2.x, obj_player2.y, obj_player2.x_vel, obj_player2.y_vel, obj_player2.just_shot, global.time]);
    
	// Add time with deltatime
	global.time += global.dt * 1/60;
	
	// Check if time is over/equal to the time limit
	if (global.time >= global.time_limit) {
		// If so, set the current state to the next transition (replay)
        global.current_state = "record2a";
        
		//show_debug_message(global.player2_recording);
    }
} else if (global.current_state == "record2a") {
	// Slowly make the characters more transparent
	obj_player1.image_alpha -= transparency_speed;
	obj_player2.image_alpha -= transparency_speed;
    obj_arena_parent.image_alpha -= transparency_speed;
	
	// If the player becomes fully transparent then move to the next state
	if (obj_player1.image_alpha <= 0) {
		global.current_state = "replayt";
	}
} else if (global.current_state == "replayt") {
    reset_players(); // Reset the players to previous state
	// Reset the image transparency to full
	obj_player1.image_alpha = 1;
	obj_player2.image_alpha = 1;
    obj_arena_parent.image_alpha = 1;
	// Create a ready button if there isn't one already
	if (!instance_exists(obj_ready_button)) {
		instance_create_layer(room_width / 2, room_height / 2, recording, obj_ready_button);
	}
	
	// Waits for the button to be pressed
	
	// Resets the time
    global.time = 0;
	
	global.replay_shot_index1 = 0;
	global.replay_shot_index2 = 0;
	global.previous_replay_time = 0;
} else if (global.current_state == "replay") {
	global.previous_replay_time = global.time - global.dt * 1/60;
    // Add time with deltatime
    if (flashing_player == noone) {
        global.time += global.dt * 1/60;
    }
    
    // Interpolate player 1's position and velocity
    var _rec1 = global.player1_recording; // Simplicity and also optimization
    var _len1 = array_length(_rec1); // Check if the player has anything, otherwise don't do anything
    
	// Only interpolate if there is anything recorded
	if (_len1 > 0)
    {
        // Find the index of the first recorded frame whose timestamp is >= global.time
		// This gives us the "future" frame relative to the current replay time
        var _idx = 0;
        while (_idx < _len1 && _rec1[_idx][5] < global.time)   // [5] is the stored time
        {
            _idx++; // Loop through the recording
        }
		
		// Determine the two frames to interpolate between (p1 = earlier, p2 = later)
        var _p1, _p2;
        if (_idx == 0) // If the index is the first frame, just use the timestamps data
        {
            _p1 = _rec1[0];
            _p2 = _rec1[0];
            var _t = 0;
        }
        else if (_idx >= _len1) // If the timestamp is after the length of the recording it stops
        {
            // After last frame: use last frame's data
            _p1 = _rec1[_len1-1];
            _p2 = _rec1[_len1-1];
            var _t = 1;
        }
        else
        {
            // Between two frames: interpolation
            _p1 = _rec1[_idx-1]; // Previous frame (before global.time)
            _p2 = _rec1[_idx]; // Next frame (after global.time)
            var _t1 = _p1[5];  // Timestamp of previous frame ===================CHANGE=============================
            var _t2 = _p2[5];  // Timestamp of next frame ===================CHANGE=============================
            var _t = (global.time - _t1) / (_t2 - _t1); // Calculate the interpolation factor based on time difference
            _t = clamp(_t, 0, 1); // If somehow the difference is more than 1 or less than zero, we clamp it to the safe range
        }
        
        // Linear interpolation for position and velocity
        obj_player1.x = lerp(_p1[0], _p2[0], _t); // Lerp the x value
        obj_player1.y = lerp(_p1[1], _p2[1], _t); // Lerp the y value
        obj_player1.x_vel = lerp(_p1[2], _p2[2], _t); // Lerp the x velocity
        obj_player1.y_vel = lerp(_p1[3], _p2[3], _t); // Lerp the y velocity
	
		// Calculate gun direction
		obj_player1.gun_direction = point_direction(obj_player1.x, obj_player1.y, obj_player1.x+obj_player1.x_vel, obj_player1.y-obj_player1.y_vel);
    }
    
    // ----- Player 2 interpolation (same logic) -----
    var _rec2 = global.player2_recording;
    var _len2 = array_length(_rec2);
    if (_len2 > 0)
    {
        var _idx = 0;
        while (_idx < _len2 && _rec2[_idx][5] < global.time) // CHANGE HERE!!!!!!!!!!!!!!!!!!
        {
            _idx++;
        }
        
        var _p1, _p2;
        if (_idx == 0)
        {
            _p1 = _rec2[0];
            _p2 = _rec2[0];
            var _t = 0;
        }
        else if (_idx >= _len2)
        {
            _p1 = _rec2[_len2-1];
            _p2 = _rec2[_len2-1];
            var _t = 1;
        }
        else
        {
            _p1 = _rec2[_idx-1];
            _p2 = _rec2[_idx];
            var _t1 = _p1[5]; // CHANGE HERE!!!!!!!!!!!!!!!!!!!!!!!!!!!
            var _t2 = _p2[5]; // CHANGE HERE!!!!!!!!!!!!!!!!!!!!!!!!!!!
            var _t = (global.time - _t1) / (_t2 - _t1);
            _t = clamp(_t, 0, 1);
        }
        
	    obj_player2.x = lerp(_p1[0], _p2[0], _t);
	    obj_player2.y = lerp(_p1[1], _p2[1], _t);
	    obj_player2.x_vel = lerp(_p1[2], _p2[2], _t);
	    obj_player2.y_vel = lerp(_p1[3], _p2[3], _t);
	
		// Calculate gun direction
		obj_player2.gun_direction = point_direction(obj_player2.x, obj_player2.y, obj_player2.x+obj_player2.x_vel, obj_player2.y-obj_player2.y_vel);
    }
		
	// ----- Player 1 shots -----
	var _shot_idx = global.replay_shot_index1;
	while (_shot_idx < _len1 && _rec1[_shot_idx][5] <= global.time)   // use [5] for time
	{
	    // Only trigger if this frame's time is >= the previous replay time
	    if (_rec1[_shot_idx][5] >= global.previous_replay_time)
	    {
	        if (_rec1[_shot_idx][4])   // just_shot is at index 4
	        {
	            obj_player1.shoot("replay");
	        }
	    }
	    _shot_idx++;
	}
	global.replay_shot_index1 = _shot_idx;   // <-- crucial: save progress

	// ----- Player 2 shots (same logic) -----
	var _shot_idx2 = global.replay_shot_index2;   // use a different variable name
	while (_shot_idx2 < _len2 && _rec2[_shot_idx2][5] <= global.time)
	{
	    if (_rec2[_shot_idx2][5] >= global.previous_replay_time)
	    {
	        if (_rec2[_shot_idx2][4])
	        {
	            obj_player2.shoot("replay");
	        }
	    }
	    _shot_idx2++;
	}
    
    if (flashing_player == noone) {
        flashing_player = noone;
        with (obj_player1) { 
            var _bullets_hit_by_enemy = false;
            with (obj_bullet) {
                if (place_meeting(x, y, other.id) && from_player != 1) {
                    _bullets_hit_by_enemy++;
                    obj_game_controller.flashing_player = obj_player1;
                    instance_destroy();
                }
            }
            if (_bullets_hit_by_enemy) {
                hp -= 1;
                if (hp <= 0) {
                    global.winner = "player2";
                    global.current_state = "death_effect";
                    obj_game_controller.flashing_player = noone;
                }
            }
        }
        with (obj_player2) {
            // If in replay, check for collision with bullets
            var _bullets_hit_by_enemy = 0;
            with (obj_bullet) {
                if (place_meeting(x, y, other.id) && from_player != 2) {
                    _bullets_hit_by_enemy++;
                    obj_game_controller.flashing_player = obj_player2;
                    instance_destroy();
                }
            }
            if (_bullets_hit_by_enemy > 0) {
                hp -= 1;
                if (hp <= 0) {
                    global.winner = "player1";
                    global.current_state = "death_effect";
                    obj_game_controller.flashing_player = noone;
                }
            }
        }
    }
    
    
    if (flashing_player != noone) {
        if (alarm[7] = -1) {
            alarm[7] = 15;
            // Not adding flashed variable here because it's added in alarm 7
            // so that it adds after it finishes flashing then right as its waiting to flash back
        }
        if (flashed == 4) {
            flashing_player = noone;
            flashed = 0;
        }
    }
	global.replay_shot_index2 = _shot_idx2;
    if (global.time >= global.time_limit)
    {
		// Update the gamestate variable
        global.last_recorded_state[0] = array_last(global.player1_recording)[0]; // Last X position
		global.last_recorded_state[1] = array_last(global.player1_recording)[1]; // Last Y position
		global.last_recorded_state[2] = array_last(global.player1_recording)[2]; // Last x velocity
		global.last_recorded_state[3] = array_last(global.player1_recording)[3]; // Last y velocity

        global.last_recorded_state[5] = array_last(global.player2_recording)[0]; // Last X position
		global.last_recorded_state[6] = array_last(global.player2_recording)[1]; // Last Y position
		global.last_recorded_state[7] = array_last(global.player2_recording)[2]; // Last x velocity
		global.last_recorded_state[8] = array_last(global.player2_recording)[3]; // Last y velocity
		
		// Clear out the old recordings
		global.player1_recording = [];
		global.player2_recording = [];
		
		// Restart the gameplay loop
		global.current_state = "replaya";
		
		// Move to the recording room
		room_goto(recording);
    }
    //show_debug_message(global.time);
} else if (global.current_state == "death_effect") {
    if (alarm[3] == -1) {
        alarm[3] = 10;
        flashed++;
    }
    
    if (flashed == 7) {
        global.current_state = "game_over";
        flashed = 0;
    }
} else if(global.current_state == "game_over") {
    if (alarm[4] == -1 and show_game_over_text == false) {
        alarm[4] = 60;
    }
    if (show_game_over_text) {
        if (alarm[5] == -1) {
            alarm[5] = 120;
        }
    }
    
} else if (global.current_state == "award") {
    if (alarm[6] == -1) {
        alarm[6] = 180;
    }
} else if (global.current_state == "re_play") { 
    if (!instance_exists(obj_replay_button)) {
        instance_create_layer(room_width/2, room_height/2 + 100, "User_Interface", obj_replay_button);
    }
}