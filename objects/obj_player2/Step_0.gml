

// Use global.dt from the controller
var _dt = global.dt;
if (global.current_state == "record2") {
	
	// ---- W key ----
	if (keyboard_check(vk_up)) {
	    y_vel += 1 * _dt;
	}
    
	// ---- A key ----
	if (keyboard_check(vk_left)) {
	    x_vel -= 2 * _dt
	}
    
	// ---- D key ----
	if (keyboard_check(vk_right)) {
	    x_vel += 2 * _dt
	}
	
	y_vel -= .3 * _dt;                           // gravity
	x_vel *= .8;              // friction
	y_vel = clamp(y_vel, -30, 30);              // speed limit
	
	// Update position
	x += x_vel * _dt;
	y -= y_vel * _dt;
}

