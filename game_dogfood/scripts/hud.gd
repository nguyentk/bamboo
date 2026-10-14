extends CanvasLayer

@onready var label: Label = $Coins


func on_coin_collected(total: int) -> void:
	label.text = "Coins: %d" % total
