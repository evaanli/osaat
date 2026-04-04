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
	
	x = clamp(x, 30, room_width - 30);
    y = clamp(y, 45, room_height - 45);
    
    if (x == 30 or x == room_width - 30) {
        x_vel = 0;
    }
    if (y == 45 or y == room_height - 45) {
        y_vel = 0;
    }
    
}


// If in replay, check for collision with bullets
if (global.current_state == "replay") {
	if (place_meeting(x, y, obj_bullet)) {
		hp -= 1;
        if (hp <= 0) {
            global.winner = "player2";
            global.current_state = "death_effect";
        }
	}
}