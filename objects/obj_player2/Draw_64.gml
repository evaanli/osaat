if (global.current_state == "replay" or global.current_state == "replaya" or global.current_state == "replayt" or global.current_state == "replaya" or global.current_state == "record2" or global.current_state == "record2t") {
	// Draw a simple health bar
	var bar_width = 300;      // total width of the bar in pixels
	var bar_height = 36;      // height of the bar
	var bar_x = room_width - 50 - bar_width;       // very left side
	var bar_y = 50;       // at the top

	// Set the draw set
	draw_set_valign(fa_top);
	draw_set_halign(fa_right);

	// Draw background (empty health)
	draw_set_color(c_black);
	draw_rectangle(bar_x, bar_y, bar_x + bar_width, bar_y + bar_height, false);

	// Draw filled portion (current health)
	draw_set_color(c_red);
	var fill_width = (hp / max_hp) * bar_width;
	draw_rectangle(bar_x, bar_y, bar_x + fill_width, bar_y + bar_height, false);

	// Draw a border around the bar
	draw_set_color(c_white);
	draw_rectangle(bar_x, bar_y, bar_x + bar_width, bar_y + bar_height, true);

	// Draw the text inside of the bar
	draw_set_color(c_white);
	draw_set_font(fnt_health);
	draw_set_halign(fa_center);
	draw_set_valign(fa_center);
	draw_text(bar_x + bar_width/2, bar_y + bar_height/2, string(hp) + "/" + string(max_hp));
}