obj_game_controller.reset_players();

if (global.map == "circles") {
    instance_create_layer(0, 0, "Arena", obj_arena_circles);
}