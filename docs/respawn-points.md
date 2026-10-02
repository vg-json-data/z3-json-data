# Death and save-and-quit spawn points

Where you restart depends on your location, follower, remembered checkpoint, and current story stage. These rules come from the original game’s JP1.0 disassembly, including what happens when events occur out of order. Randomizers may change the rules themselves.

## Regular spawn locations

Room nodes identify regular destinations with `spawnPoint` and remembered checkpoint destinations with `rememberedSpawnPoint`. These are destination labels, not checkpoint-setting triggers. See [Room Data: Respawn Points](rooms.md#respawn-points) for the property values and node mapping.

| Location | When you can use it |
| --- | --- |
| Link’s house | A choice whenever the Light World start menu appears. Also the initial start. |
| Sanctuary | A choice whenever the Light World start menu appears. |
| Mountain Cave | An additional Light World menu choice if you have the Magic Mirror item. |
| Pyramid | An automatic Dark World restart when the rules below call for it. It is not a menu choice. |

## Remembered checkpoints

| Checkpoint | What sets it |
| --- | --- |
| Link’s house | Default at the start of the game. |
| Uncle’s secret passage | Receiving your equipment from Uncle. |
| Zelda’s prison | Zelda joining you as a follower. |
| Castle throne room | Starting to push the mantle with Zelda following and the Lamp in your inventory. |
| Lost Old Man’s cave | The lost Old Man joining you as a follower. This is different from the Mountain Cave menu destination. |
| Sanctuary | Completing Zelda’s Sanctuary dialogue or receiving the item from the Old Man. Either event sets it. |

**Only one checkpoint is remembered at a time. Each new checkpoint replaces the previous one, regardless of the order you trigger them.**

Note that the Old Man’s checkpoint change happens during his item-giving event; it is not strictly dependent on the Magic Mirror item.

Losing a follower does not erase the checkpoint. However, remembering a checkpoint does not guarantee that every restart uses it.

## Story stage: separate from the checkpoint

The game also remembers a story stage. This controls whether you can save, whether the start menu appears, and whether Dark World restarts are allowed.

| Event | Story stage it sets |
| --- | --- |
| New game | **Opening:** new progress cannot be saved yet. |
| Receive Uncle’s equipment | **Early:** checkpoint starts are enabled. |
| Complete Zelda’s Sanctuary dialogue | **Rescued:** the normal Light World start menu is enabled. |
| Defeat Agahnim 1 | **Post-Agahnim:** Dark World restarts are also enabled. |

**The most recent of these events determines the stage.** For example, receiving Uncle’s equipment after completing Zelda’s rescue puts you back in the Early stage and sets Uncle’s checkpoint. Checkpoint changes outside these events do not change the stage.

In the Opening, Early, and Rescued stages, death/save-and-quit treats your restart world as Light World—even if you were in the Dark World. In the Post-Agahnim stage, it keeps your current world.

## Death

These rules apply when you choose **Continue** or **Save and Continue** after a game over. In the Opening stage, continuing reloads the existing save instead of keeping new progress.

Otherwise, use this table. “Restart world” means the world determined by the story-stage rules above.

| Location | Follower | Where you restart |
| --- | --- | --- |
| Dungeon | Neither Zelda nor the Old Man | The last entrance from the overworld: entering a dungeon through a node with `nodeType: "door"` or `nodeType: "drop"` sets the dungeon death spawn to that entrance. |
| Dungeon | Zelda | Use the indoor with Zelda rules below. |
| Dungeon | The Old Man | The remembered checkpoint. |
| Ordinary cave or house | Not Zelda | Use the outdoor rules below. |
| Ordinary cave or house | Zelda | Use the indoor with Zelda rules below. |
| Outdoors | Any or none | Use the outdoor rules below. |
| Ganon’s room | Any or none | Use the outdoor rules below. |

### Outdoor rules

Apply the first matching rule:

1. If your restart world is Dark World, restart at the Pyramid.
2. Use the remembered checkpoint if the story stage is Early.
3. Use the remembered checkpoint if it is the lost Old Man’s cave.
4. Otherwise, show the regular Light World start menu.

### Indoor with Zelda rules

Apply the first matching rule:

1. If your restart world is Dark World, use the remembered checkpoint.
2. Use the remembered checkpoint if the story stage is Early.
3. Use the remembered checkpoint if it is the lost Old Man’s cave.
4. Otherwise, show the regular Light World start menu.

For example, Zelda following with prison remembered gives a prison restart in the Early stage or when the restart world is Dark World. In the Rescued stage, even a death in the Dark World uses Light World rules and gives the start menu. If you lose Zelda, a dungeon death instead retries the dungeon entrance without erasing the remembered prison checkpoint.

## Save and Quit

When you reopen the file, apply the first matching rule. Your follower and whether you saved inside a dungeon or cave do not change this list.

| Requirement | Where you restart |
| --- | --- |
| Opening stage | Existing save/initial start; new progress was not saved. |
| Post-Agahnim stage and saved in the Dark World | Pyramid. |
| Early stage | Remembered checkpoint. |
| Lost Old Man’s cave is the remembered checkpoint | Lost Old Man’s cave. |
| Otherwise | Regular Light World start menu. |

**Getting the Mirror does not by itself enable the start menu.** If the Old Man gives it to you in the Early stage, he replaces your checkpoint with Sanctuary, so saving and quitting starts you directly at Sanctuary. If you are in the Rescued stage, you instead get the start menu, now including Mountain Cave.

Likewise, setting a temporary checkpoint during the Opening stage does not enable saving. Checkpoints and story stages are independent.

*Saving during an active Mirror transition has an additional glitch-specific exception outside this reference.*
