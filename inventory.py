class InventorySlot:
    item: str | None = None
    count: int = 0

class Inventory:
    instance = None
    BAR_SLOTS = 9
    BAG_SLOTS = 36
    slots: list[InventorySlot] = []
    def __init__(self, base):
        Inventory.instance = self
        self.base = base
        for s in range(self.BAR_SLOTS + self.BAG_SLOTS):
            self.slots.append(InventorySlot())

    def add(self, item: str, count: int, slot: int = 0):
        while slot == 0 or (self.slots[slot].item is not None and self.slots[slot].item != item):
            slot += 1
            print(f"{slot}: {self.slots[slot].item}")
            if slot >= len(self.slots):
                print(f"No slot found for {count} {item} ({slot} >= {len(self.slots)})")
                return 0
        print(f"Adding {count} {item} to slot {slot}")
        self.set_item(slot, item, self.slots[slot].count + count)
        return slot

    def remove(self, item: str, count: int):
        slot = len(self.slots) - 1
        while slot > 0:
            if self.slots[slot].item == item:
                this_slot = min(count, self.slots[slot].count)
                count -= this_slot
                self.slots[slot].count -= this_slot
                if self.slots[slot].count == 0:
                    self.set_item(slot, None)
                if count == 0:
                    return slot
            slot -= 1
        return -1

    def set_item(self, slot: int, item: str | None, count: int):
        self.slots[slot].item = item
        self.slots[slot].count = count
        self.base.hud.set_slot(slot, item, count)

    def set_count(self, slot: int, count: int):
        self.slots[slot].count = count
        self.base.hud.set_slot(slot, self.slots[slot].item, count)

