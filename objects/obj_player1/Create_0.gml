x_vel = 0;
y_vel = 0;

gun_direction = 90;

last_shot = 0;
reload_time = .200;

just_shot = false;


function shoot(type) {
	var _projectile = instance_create_layer(x, y, "Instances", obj_bullet);
	_projectile.rotation = gun_direction;
	_projectile.shot_speed = 50;
	if (type != "replay") {
		last_shot = global.time;
		just_shot = true;
	}
}