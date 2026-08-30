# Enemy data

## Categories

- Enemies are animate creatures with some sentience.
- Bosses are represented separately in `bosses.json`.
- Unusual enemies are stored in `other.json`.
- Invulnerable objects are stored in `invulnerable.json`.
- Enemy attacks are stored in `attacks.json` and must not be used as the `enemy` in an `enemyDamage` requirement.
- Non-enemy damage sources are stored in `non-enemies.json`.

Some attacks spawned by non-enemies also need enemy records because attacks cannot be referenced directly. For example, a Medusa can summon a Fireball.

## Enemy damage requirements

An `enemyDamage` requirement identifies the enemy dealing damage. Without an `attack`, damage comes from that enemy's `dmgToLink` value for Link's mail color; 8 damage equals one heart.

When `attack` is present, damage instead comes from the named attack's `dmgToLink` value. Naming the attack clarifies which attack hit Link and allows validation that the enemy can perform it. This matters because many attacks have generic names such as Fireball, Weak Fireball, and Spitting Fireball.

## Modeling scope

Many table values are overridden by game code. This data aims to describe how the game behaves from the player's perspective, not the underlying inheritance or tables when an override changes the result.

For example, modeling Spear Soldier (Green) as Spear Soldier (Red) with an HP override is out of scope. Likewise, a weapon-damage table entry is not important when the enemy overrides it. The lightning lock at Agahnim's Tower appears vulnerable to a Fighter Sword spin in its table, but an override requires the Master Sword. Many bosses have similar overrides that make their table values less meaningful.

## Damage from Link

Most `dmgFromLink` values are integer damage amounts. Some weapons may instead produce these special results:

| Weapon | Special results |
|---|---|
| `boomerang` | `stun1Second`, `stun4Seconds`, `stun10Seconds` |
| `hookshot`, `bombs` | `stun10Seconds` |
| `magicPowder` | `fairy`, `slime` |
| `fireRod`, `bombos` | `incinerate` |
| `iceRod`, `ether` | `freeze` |
| `quake` | `stun10Seconds`, `slime` |

`class1` through `class5`, `arrows`, and `silverArrows` are always integers.

Special-result meanings:

- `stun1Second`: Stuns the enemy for approximately 67 frames (1.1 seconds).
- `stun4Seconds`: Stuns the enemy for approximately 265 frames (4.4 seconds).
- `stun10Seconds`: Stuns the enemy for approximately 580 frames (9.7 seconds).
- `fairy`: Replaces the enemy with a fairy.
- `slime`: Replaces the enemy with a zero-HP slime using sprite index 143.
- `incinerate`: Kills the enemy with a moderately long fire animation.
- `freeze`: Freezes the enemy.

Damage classes:

- `boomerang`: Either boomerang color.
- `class1`: Normal Fighter Sword hits, drawn Master Sword, sword sparkles, either cane, bees, and thrown purple or green bushes.
- `class2`: Fighter Sword spin attacks, normal Master Sword hits, and drawn Tempered Sword.
- `class3`: Master Sword spin attacks, normal Tempered Sword hits, drawn Golden Sword, Hammer, and other thrown objects including frozen enemies and yellow bushes.
- `class4`: Tempered Sword spin attacks and normal Golden Sword hits.
- `class5`: Golden Sword spin attacks.

## Prize packs

Prize packs usually have a 50% chance to drop nothing, except pack 3. Most packs have a common theme, with approximately six of their eight drops using the same item:

- 0: Hearts
- 1: Rupees, averaging 5–6
- 2: Magic
- 3: Bombs, with a 100% drop rate
- 4: Arrows
- 5: Low-tier variety
- 6: High-tier variety
