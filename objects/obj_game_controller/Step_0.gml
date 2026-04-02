global.dt = delta_time / game_get_speed(gamespeed_microseconds);
if (global.current_state == "replaya") {
	// Slowly make the characters more transparent
	obj_player1.image_alpha -= transparency_speed;
	obj_player2.image_alpha -= transparency_speed;
	
	// If the player becomes fully transparent then move to the next state
	if (obj_player1.image_alpha <= 0) {
		global.current_state = "record1t";
	}
} else if (global.current_state == "record1t") {
    reset_players(); // Reset the players to previous state
	// Reset the image transparency to full
	obj_player1.image_alpha = 1;
	obj_player2.image_alpha = 1;
	// Create a ready button if there isn't one already
	if (!instance_exists(obj_ready_button)) {
		instance_create_layer(room_width / 2, room_height / 2, recording, obj_ready_button);
	}
	
	// Waits for the button to be pressed
	
	// Resets the time
    global.time = 0;
} else if (global.current_state == "record1") {
    // Record x, y, velocity and time for player 1 INCLUDING IF CURRENTLY SHOOTING
	array_push(global.record1, [obj_player1.x, obj_player1.y, obj_player1.x_vel, obj_player1.y_vel, obj_player1.just_shot, global.time]);
	
	// Add time with deltatime
    global.time += global.dt * 1/60;
	
	// Check if the time is over/equal the time limit
	if (global.time >= global.time_limit) {
		// If so, set the current state to the next transition (player2)
        global.current_state = "record1a";
		
        // show_debug_message(global.record1);
    }
} else if (global.current_state == "record1a") {
	// Slowly make the characters more transparent
	obj_player1.image_alpha -= transparency_speed;
	obj_player2.image_alpha -= transparency_speed;
	
	// If the player becomes fully transparent then move to the next state
	if (obj_player1.image_alpha <= 0) {
		global.current_state = "record2t";
	}
} else if (global.current_state == "record2t")  {
	
    reset_players(); // Reset the players to previous state
	// Reset the image transparency to full
	obj_player1.image_alpha = 1;
	obj_player2.image_alpha = 1;
	// Create a ready button if there isn't one already
	if (!instance_exists(obj_ready_button)) {
		instance_create_layer(room_width / 2, room_height / 2, recording, obj_ready_button);
	}
	
	// Waits for the button to be pressed
	
	// Resets the time
    global.time = 0;
} else if (global.current_state == "record2") {
    // Record x, y, velocity and time
	array_push(global.record2, [obj_player2.x, obj_player2.y, obj_player2.x_vel, obj_player2.y_vel, obj_player2.just_shot, global.time]);
    
	// Add time with deltatime
	global.time += global.dt * 1/60;
	
	// Check if time is over/equal to the time limit
	if (global.time >= global.time_limit) {
		// If so, set the current state to the next transition (replay)
        global.current_state = "record2a";
        
		//show_debug_message(global.record2);
    }
} else if (global.current_state == "record2a") {
	// Slowly make the characters more transparent
	obj_player1.image_alpha -= transparency_speed;
	obj_player2.image_alpha -= transparency_speed;
	
	// If the player becomes fully transparent then move to the next state
	if (obj_player1.image_alpha <= 0) {
		global.current_state = "replayt";
	}
} else if (global.current_state == "replayt") {
    reset_players(); // Reset the players to previous state
	// Reset the image transparency to full
	obj_player1.image_alpha = 1;
	obj_player2.image_alpha = 1;
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
    global.time += global.dt * 1/60;
    
    // Interpolate player 1's position and velocity
    var _rec1 = global.record1; // Simplicity and also optimization
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
    var _rec2 = global.record2;
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
	global.replay_shot_index2 = _shot_idx2;
    if (global.time >= global.time_limit)
    {
		// Update the gamestate variable
        global.gamestate[0] = array_last(global.record1)[0]; // Last X position
		global.gamestate[1] = array_last(global.record1)[1]; // Last Y position
		global.gamestate[2] = array_last(global.record1)[2]; // Last x velocity
		global.gamestate[3] = array_last(global.record1)[3]; // Last y velocity

        global.gamestate[5] = array_last(global.record2)[0]; // Last X position
		global.gamestate[6] = array_last(global.record2)[1]; // Last Y position
		global.gamestate[7] = array_last(global.record2)[2]; // Last x velocity
		global.gamestate[8] = array_last(global.record2)[3]; // Last y velocity
		
		// Clear out the old recordings
		global.record1 = [];
		global.record2 = [];
		
		// Restart the gameplay loop
		global.current_state = "replaya";
		
		// Move to the recording room
		room_goto(recording);
    }
}