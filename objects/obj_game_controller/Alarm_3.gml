// Alarm for flashing the losing player repeatedly
if (global.winner == "player1") {
    obj_player2.image_alpha = 1 - obj_player2.image_alpha;
} else {
    obj_player1.image_alpha = 1 - obj_player2.image_alpha;
}