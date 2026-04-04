x_vel = 0;
y_vel = 0;

previous_x = x; 
previous_y = y;

gun_direction = 90;

last_shot = 0;
reload_time = .200;

just_shot = false;

hp = 3;
max_hp = global.player1_max_hp;


function shoot(type) {
	var _projectile = instance_create_layer(x, y, "Instances", obj_bullet);
    _projectile.from_player = 1;
	_projectile.direction = gun_direction;
	_projectile.image_angle = gun_direction;
	_projectile.speed = 50;
	_projectile.x += lengthdir_x(70, gun_direction);
	_projectile.y += lengthdir_y(70, gun_direction);
	if (type != "replay") {
		last_shot = global.time;
		just_shot = true;
	}
}