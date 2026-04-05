// Alarm to flash player
if (flashing_player == obj_player1) {
    obj_player1.image_alpha = 1 - obj_player1.image_alpha;
} else {
    obj_player2.image_alpha = 1 - obj_player2.image_alpha;
}
flashed++;