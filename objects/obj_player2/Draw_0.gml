draw_self();

if (global.current_state == "replay" or global.current_state == "replaya" or global.current_state == "record2t" or global.current_state == "record2" or global.current_state == "record2a") {
	draw_set_alpha(image_alpha);
    // --- Bobbing arrow (V-shape, two lines) ---
    var dist_base = 70;          // base distance from player
    var bob_amp = 5;             // bobbing amplitude (pixels)
    var bob_speed = 2;           // bobbing cycles per second

    // Bobbing offset using sine of game time
    var bob_offset = sin(global.time * bob_speed * 2 * pi) * bob_amp;
    var dist = dist_base + bob_offset;

    // Apex position (tip of the V)
    var apex_x = x + lengthdir_x(dist, gun_direction);
    var apex_y = y + lengthdir_y(dist, gun_direction);

    // V "wing" length and opening angle
    var wing_len = 12;           // length of each line from apex to base
    var wing_angle = 30;         // degrees between each line and the direction line

    // Calculate left and right base points (ends of the two lines)
    var left_x = apex_x - lengthdir_x(wing_len, gun_direction - wing_angle);
    var left_y = apex_y - lengthdir_y(wing_len, gun_direction - wing_angle);
    var right_x = apex_x - lengthdir_x(wing_len, gun_direction + wing_angle);
    var right_y = apex_y - lengthdir_y(wing_len, gun_direction + wing_angle);

    // Determine color
    var can_shoot = (global.time > last_shot + reload_time);
    draw_set_color(can_shoot ? c_yellow : c_red);

    // Draw the two lines (apex to left, apex to right)
    draw_line(apex_x, apex_y, left_x, left_y);
    draw_line(apex_x, apex_y, right_x, right_y);
}