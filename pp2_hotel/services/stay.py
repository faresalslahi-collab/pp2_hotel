from pp2_hotel.services.room_status import set_room_status

ROOM_STATUS_BY_STAY_STATUS = {
	"Checked In": "Occupied",
	"Checked Out": "Dirty",
}


def sync_room_status(stay):
	"""Keep Room.status in step with the Hotel Stay lifecycle.

	Checkout leaves the room Dirty rather than Available -- housekeeping
	has to turn it before it can be sold again.
	"""
	new_status = ROOM_STATUS_BY_STAY_STATUS.get(stay.status)
	if not new_status:
		return
	set_room_status(stay.room, new_status)
