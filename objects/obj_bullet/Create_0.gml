hit_wall = false; // collision flag

saved_speed = 0;

left_angle_debug = 0;
right_angle_debug = 0;

from_player = 0;

function reflect_angle(incident_angle, wall_normal_angle) {
    // Convert angles to direction vectors
    var ix = lengthdir_x(1, incident_angle);
    var iy = lengthdir_y(1, incident_angle);
    var nx = lengthdir_x(1, wall_normal_angle);
    var ny = lengthdir_y(1, wall_normal_angle);
    
    // Dot product
    var dot = ix * nx + iy * ny;
    
    // Reflection vector: v - 2 * (v·n) * n
    var rx = ix - 2 * dot * nx;
    var ry = iy - 2 * dot * ny;
    
    // Convert back to angle
    return point_direction(0, 0, rx, ry);
}