global.dt = delta_time / game_get_speed(gamespeed_microseconds);

if (global.current_state == "record1t") {
	// Goes to the recording room
    room_goto(recording);
	
	// Sets the waiting time if it isn't set
    if (not alarm[0] > 0) {
        alarm[0] = 180;
    }
	
	// Resets the time
    global.time = 0;
} else if (global.current_state == "record1") {
    // Record x, y, velocity and time for player 1
	array_push(global.record1, [obj_player1.x, obj_player1.y, obj_player1.x_vel, obj_player1.y_vel, global.time]);
	
	// Add time with deltatime
    global.time += global.dt * 1/60;
	
	// Check if the time is over/equal the time limit
	if (global.time >= global.time_limit) {
		// If so, set the current state to the next transition (player2)
        global.current_state = "record2t";
		
        // show_debug_message(global.record1);
    }
} else if (global.current_state == "record2t") {
	// Sets the waiting time if it isn't set
    if (alarm[1] == -1) {
        alarm[1] = 180;
    }
	
	// Resets the time
    global.time = 0;
} else if (global.current_state == "record2") {
    // Record x, y, velocity and time
	array_push(global.record2, [obj_player2.x, obj_player2.y, obj_player2.x_vel, obj_player2.y_vel, global.time]);
    
	// Add time with deltatime
	global.time += global.dt * 1/60;
	
	// Check if time is over/equal to the time limit
	if (global.time >= global.time_limit) {
		// If so, set the current state to the next transition (replay)
        global.current_state = "replayt";
        
		//show_debug_message(global.record2);
    }
} else if (global.current_state == "replayt") {
	// Sets the transition time if not already set
    if (alarm[2] == -1) {
        alarm[2] = 180;
    }
	
	// Resets the time variable
    global.time = 0;
} else if (global.current_state == "replay") {
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
        while (_idx < _len1 && _rec1[_idx][4] < global.time)   // [4] is the stored time
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
            var _t1 = _p1[4];  // Timestamp of previous frame
            var _t2 = _p2[4];  // Timestamp of next frame
            var _t = (global.time - _t1) / (_t2 - _t1); // Calculate the interpolation factor based on time difference
            _t = clamp(_t, 0, 1); // If somehow the difference is more than 1 or less than zero, we clamp it to the safe range
        }
        
        // Linear interpolation for position and velocity
        obj_player1.x = lerp(_p1[0], _p2[0], _t); // Lerp the x value
        obj_player1.y = lerp(_p1[1], _p2[1], _t); // Lerp the y value
        obj_player1.x_vel = lerp(_p1[2], _p2[2], _t); // Lerp the x velocity
        obj_player1.y_vel = lerp(_p1[3], _p2[3], _t); // Lerp the y velocity
    }
    
    // ----- Player 2 interpolation (same logic) -----
    var _rec2 = global.record2;
    var _len2 = array_length(_rec2);
    if (_len2 > 0)
    {
        var _idx = 0;
        while (_idx < _len2 && _rec2[_idx][4] < global.time)
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
            var _t1 = _p1[4];
            var _t2 = _p2[4];
            var _t = (global.time - _t1) / (_t2 - _t1);
            _t = clamp(_t, 0, 1);
        }
        
        obj_player2.x = lerp(_p1[0], _p2[0], _t);
        obj_player2.y = lerp(_p1[1], _p2[1], _t);
        obj_player2.x_vel = lerp(_p1[2], _p2[2], _t);
        obj_player2.y_vel = lerp(_p1[3], _p2[3], _t);
    }
    if (global.time >= global.time_limit)
    {
		// Update the gamestate variable
        global.gamestate[0] = array_last(global.record1)[0];
		global.gamestate[1] = array_last(global.record1)[1];
		global.gamestate[2] = array_last(global.record1)[2];
		global.gamestate[3] = array_last(global.record1)[3];

        global.gamestate[5] = array_last(global.record2)[0];
		global.gamestate[6] = array_last(global.record2)[1];
		global.gamestate[7] = array_last(global.record2)[2];
		global.gamestate[8] = array_last(global.record2)[3];
		
		// Clear out the old recordings
		global.record1 = [];
		global.record2 = [];
		
		// Restart the gameplay loop
		global.current_state = "record1t"
    }
}