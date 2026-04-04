// Store original direction
var _original_dir = direction;

// 1. Backtrack out of wall
var _back_dir = _original_dir + 180;
var _limit = 100;
var _count = 0;
while (place_meeting(x, y, obj_arena_parent) && _count < _limit) {
    x += lengthdir_x(1, _back_dir);
    y += lengthdir_y(1, _back_dir);
    _count++;
}

// 2. Sweep left to find last colliding angle
var _max_sweep = 90;
var _precision = 2;
var _dist = 60;
var _left_angle = _original_dir;
for (var a = _precision; a <= _max_sweep; a += _precision) {
    var _test_angle = (_original_dir - a + 360) mod 360;
    var _x2 = x + lengthdir_x(_dist, _test_angle);
    var _y2 = y + lengthdir_y(_dist, _test_angle);
    if (collision_line(x, y, _x2, _y2, obj_arena_parent, true, true) != noone) {
        _left_angle = _test_angle;
    } else {
        break;
    }
}

// 3. Sweep right to find last colliding angle
var _right_angle = _original_dir;
for (var a = _precision; a <= _max_sweep; a += _precision) {
    var _test_angle = (_original_dir + a) mod 360;
    var _x2 = x + lengthdir_x(_dist, _test_angle);
    var _y2 = y + lengthdir_y(_dist, _test_angle);
    if (collision_line(x, y, _x2, _y2, obj_arena_parent, true, true) != noone) {
        _right_angle = _test_angle;
    } else {
        break;
    }
}

// 4. Compute bounce direction
if (_left_angle != _original_dir || _right_angle != _original_dir) {
    // Average the two edge angles
    var _diff = angle_difference(_right_angle, _left_angle);
    var _mid = _left_angle + _diff / 2;
    direction = (_mid + 180) mod 360;
} else {
    // No wall found? fallback to reverse
    direction = (_original_dir + 180) mod 360;
}

// Compute the wall's inward normal (points from bullet into the wall)
var _inward_normal = (_left_angle + _right_angle) / 2;
// The outward normal (points from wall toward bullet) is opposite
var _outward_normal = _inward_normal + 180;

// Reflect the original direction across the outward normal
direction = reflect_angle(_original_dir, _outward_normal);
image_angle = direction;

left_angle_debug = _left_angle;
right_angle_debug = _right_angle;