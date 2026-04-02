if (pressed) {
	draw_set_halign(textalign_center);
	draw_set_valign(textalign_center);
	draw_set_font(fnt_ready);
	draw_text(room_width/2, room_height/2, ceil(alarm[0] / 60));
}