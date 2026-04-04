if (global.current_state == "game_over") {
    if (show_game_over_text) { 
        draw_set_font(game_over_font);
        draw_set_color(c_red);
        draw_set_halign(textalign_center);
        draw_set_valign(textalign_center);
        draw_text(room_width / 2, room_height / 2, "GAME OVER");
    }
    
} else if (global.current_state == "award" or global.current_state == "re_play") {
    draw_set_font(game_over_font);
    draw_set_color(c_red);
    draw_set_halign(textalign_center);
    draw_set_valign(textalign_center);
    var _player_number = "2";
    if (global.winner == "player1") {
        _player_number = "1";
    }
    draw_text(room_width / 2, room_height / 2, "Player "  + _player_number + " wins!");
}