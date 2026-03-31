// Use global.dt from the controller
var _dt = global.dt;

if (global.current_state == "record1") {
	// ---- W key ----
	if (keyboard_check(ord("W"))) {
	    y_vel += 1 * _dt
	}
    
	// ---- A key ----
	if (keyboard_check(ord("A"))) {
		x_vel -= 2 * _dt
	}
    
	// ---- D key ----
	if (keyboard_check(ord("D"))) {
		x_vel += 2 * _dt
	}
	
	y_vel -= .3 * _dt;                           // gravity
	x_vel *= .9;              // friction
	y_vel = clamp(y_vel, -30, 30);              // speed limit
	
	// Update position
	x += x_vel * _dt;
	y -= y_vel * _dt;
	
	if (x <= 0) {
		x_vel += 50;
	}
	
	if (y <= 0) {
		y_vel *= -1;
	}
	
	if (x >= room_width) {
		x_vel -= 50;
	}
	
	if (y >= room_height) {
		y_vel *= -1;
	}
}


