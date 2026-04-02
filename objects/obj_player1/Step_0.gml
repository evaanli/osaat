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
	
	just_shot = false;
	if (keyboard_check(vk_up) and global.time > last_shot + reload_time) {
		shoot("record");
	}
	
	y_vel -= .3 * _dt;                           // gravity
	x_vel *= .9;              // friction
	y_vel = clamp(y_vel, -30, 30);              // speed limit
	
	// Calculate gun direction
	gun_direction = point_direction(x, y, x+x_vel*_dt, y-y_vel*_dt);
	
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


// If in replay, check for collision with bullets
if (global.current_state == "replay") {
	if (place_meeting(x, y, obj_bullet)) {
		hp -= 1;
	}
}