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
        for s in range(self.BAR_SLOTS + self.BAG_SLOTS + 1):
            self.slots.append(InventorySlot())

    def add(self, item: str, count: int, slot: int = 0):
        while slot == 0 or (self.slots[slot].item is not None and self.slots[slot].item != item):
            slot += 1
            if slot >= len(self.slots):
                # print(f"No slot found for {count} {item} ({slot} >= {len(self.slots)})")
                return 0
        self.set_item(slot, item, self.slots[slot].count + count)
        return slot

    def place(self):
        return self.remove(self.slots[self.base.hud._slot].item, 1, self.base.hud._slot)

    def remove(self, item: str, count: int, slot: int = 0):
        find = slot == 0
        if find:
            slot = len(self.slots) - 1

        while slot > 0:
            if self.slots[slot].item == item:
                this_slot = min(count, self.slots[slot].count)
                count -= this_slot
                scount = self.slots[slot].count - this_slot
                self.set_item(slot, None if scount == 0 else item, scount)
                if count == 0:
                    return (item, slot)

            if not find:
                return (None, -1)

            slot -= 1
        return (None, -1)

    def set_item(self, slot: int, item: str | None, count: int):
        self.slots[slot].item = item
        self.slots[slot].count = count
        self.base.hud.set_slot(slot, item, count)

    def set_count(self, slot: int, count: int):
        self.slots[slot].count = count
        self.base.hud.set_slot(slot, self.slots[slot].item, count)

    def can_place(self):
        slot = self.slots[self.base.hud._slot]
        return slot.count > 0 and self.base.hud.block_selected()
