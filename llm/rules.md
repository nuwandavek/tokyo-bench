# godzilla-v2
A simplified variant of the King of Tokyo game

### Goal
You can win by either:
- Victory Points (VP): Being the first agent to get to 20 victory points
- Last Monster Standing: Eliminate all other agents by reducing their health to 0

### Game Elements
- Monsters: Each agent is a monster
- Dice: 6 custom dice with symbols: 1, 2, 3, Heal, Attack
- Tokyo: A special location (only max of one agent can be in Tokyo at any point in time)

### Turn Stages
Each player's turn follows these stages. Turns go in clockwise direction.

1. Start turn: If the current agent is in Tokyo, it gains 2 VP
2. Roll Phase:
    - Roll all 6 dice up to 3 times
    - After each roll, the agent can choose to keep any dice and re-roll the rest. So between each roll, `keep_dice` method is called, which returns the mask of the dice to keep.
3. Resolve Dice Phase: Once the dice are finalized, we resolve them as follows:
    - Resolve VPs: 
        Numbers (1, 2, 3): If you have at least three of the same number, gain points equal to dice name + 1 extra VP for each new same number dice after 3.
        Example1: dice = [1, 2, 3, Heal, Attack, 1], VP = 0, since there are no sets of 3
        Example2: dice = [1, 2, 2, 2, Attack, Heal], VP = 2, since triple number 2s is 2 VP
        Example3: dice = [3, 3, 3, 3, Heal, 1], VP = 4, since triple 3s make 3VP + 1 VP for the extra 3
        Example4: dice = [Heal, 1, 1, 1, Attack, 1], VP = 2, since triple 1s make 1VP + 1 VP for the extra 1
        Example5: three 1s, 2 Heals, 1 Attack, VP = 1 (1 for triple 1s)
        Example6: four 1s, 1 Heals, 1 Attack, VP = 2 (1 for triple 1s + 1 for the 4th 1)

        In code this is resolved as:
        ```python
        for dieside in [1, 2, 3]:
            cnt = sum([x == dieside for x in dice])
            if cnt >= 3:
                delta_vp = dieside + (cnt - 3)
            else:
                delta_vp = 0
        ```
    - Resolve Attacks: Total damage is the number of Attacks in the final dice roll
        - If your monster is inside Tokyo, you damage all monsters outside Tokyo.
        - If your monster is outside Tokyo, you damage only the monster inside Tokyo. The monster inside tokyo can choose to yield Tokyo or continue to remain in it. `yield_tokyo` method is called for that agent, which returns `True` or `False`

    - Resolve Healing: Total healing is the number of Heals in the final dice roll
        - If you are inside Tokyo, you cannot be healed
        - If you are outside Tokyo, you can heal up to your MAX_HEALTH (10)
        - Each heal from the dice heals 1 HP

4. Enter Tokyo Phase: If Tokyo is empty, you have to enter it. When you enter Tokyo, you get 1 VP

The game ends when either terminal criteria is met (>=20VP or only 1 monster alive)

### Useful Tips
- You cannot heal inside Tokyo, so if inside Tokyo, there's no point in choosing 'Heal'
- You cannot get more health than MAX_HEALTH, which is 10. So there's no point choosing 'Heal' if you are already at MAX_HEALTH
