import os
import sys
import builtins
import json

# ----------------- Config -----------------
EXIT_WORD = "gameclose"
SAVE_DIR = "saves"
SAVE_FILE = os.path.join(SAVE_DIR, "savegame.json")

# ----------------- Global Variables -----------------
player = {}
game_state = "start"
can_save = False  # only True after character creation completes

# ----------------- Save / Load -----------------
def ensure_save_dir():
    if not os.path.exists(SAVE_DIR):
        os.makedirs(SAVE_DIR)

def save_game():
    global player, game_state, can_save
    if not can_save:
        print("\n[Saving disabled right now — finish character creation first.]\n")
        return False
    ensure_save_dir()
    data = {
        "player": player,
        "state": game_state
    }
    with open(SAVE_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4)
    print("\n[Game Saved]\n")
    return True

def load_game():
    global player, game_state, can_save
    if not os.path.exists(SAVE_FILE):
        print("\nNo save file found.\n")
        return False
    with open(SAVE_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)
    player = data.get("player", {})
    game_state = data.get("state", "after_character_creation")
    # After loading, allow saving (since this is a post-creation save)
    can_save = True
    print("\n[Game Loaded]\n")
    return True

# ----------------- Input Override -----------------
original_input = builtins.input

def clean_input(prompt=""):
    """
    Wrap original_input. Commands (save/load/gameclose) are recognized case-insensitively.
    Returns the raw user string (trimmed) so we keep capitalization for names.
    """
    global player, game_state, can_save

    raw = original_input(prompt)
    if raw is None:
        return ""
    stripped = raw.strip()
    lowered = stripped.lower()

    if lowered == EXIT_WORD:
        if can_save:
            print("\nExiting game... (autosave)")
            save_game()
        else:
            print("\nExiting game... (no save allowed at this time)")
        sys.exit()

    if lowered == "save":
        save_game()
        # re-prompt for the original input
        return clean_input(prompt)

    if lowered == "load":
        if load_game():
            # When load is executed mid-game, we return an empty string so the caller gets something.
            return ""
        else:
            return clean_input(prompt)

    return stripped

# Install the input wrapper
builtins.input = clean_input

# ----------------- Load Game Prompt BEFORE character creation -----------------
# If a save exists, prompt to load it before doing the intro/creation.
if os.path.exists(SAVE_FILE):
    choice = original_input("Load previous game? (yes/no): ").strip().lower()
    if choice == "yes" and load_game():
        # loaded — we should skip pre-creation and character creation
        pass
    else:
        # user said "no" or load failed — remove the save so we start fresh
        try:
            os.remove(SAVE_FILE)
        except OSError:
            pass
        player = {}
        game_state = "start"
        can_save = False

# ----------------- PRE-CHARACTER-CREATION (one intro scene) -----------------
# This runs only if there is no loaded save and game_state is "start"
if game_state == "start":
    story_input = lambda p, k=None: input(p)  # lightweight local helper for the intro
    story_input(
        "\nThe world hushes around you. A soft wind whispers across a wide, misted field.\n"
        "(Press Enter to continue)"
    )
    story_input(
        "\nA voice, distant and gentle, says:\n"
        "'This path is not yet written. Do you have the courage to step forward and choose?' \n"
        "(Press Enter to continue)"
    )
    # Move into character creation state; saving is still disabled until character creation completes
    game_state = "start_character_creation"
    can_save = False

# ----------------- Character Creation -----------------
if game_state == "start_character_creation":
    # Character creation is treated as a single atomic block. No saving is allowed until it finishes.
    print("\n--- CHARACTER CREATION ---")
    while True:
        first_name = input("Hello, adventurer! First name: ").strip()
        if first_name:
            break
        print("Please enter a name.")

    last_name = input("Last name: ").strip()
    title = input("Your title (or leave blank for 'Wanderer'): ").strip() or "Wanderer"

    while True:
        gender = input("Gender (male/female): ").strip().lower()
        if gender in ["male", "female"]:
            break
        print("Please type 'male' or 'female'.")

    while True:
        age_raw = input("Age: ").strip()
        try:
            age = int(age_raw)
            break
        except ValueError:
            print("Please enter a valid number.")

    hair_color = input("Hair color: ").strip()
    eye_color = input("Eye color: ").strip()

    classes = {
        "Warrior": {"hp": 30, "attack": 7, "magic": 2},
        "Mage": {"hp": 20, "attack": 3, "magic": 8},
        "Rogue": {"hp": 25, "attack": 5, "magic": 3}
    }

    print("\nChoose your class:")
    for c in classes:
        print(f"- {c}")

    while True:
        chosen_class = input("Class: ").strip().title()
        if chosen_class in classes:
            stats = classes[chosen_class]
            break
        print("Please choose a valid class from the list.")

    # Build the player dict
    player = {
        "first_name": first_name,
        "last_name": last_name,
        "title": title,
        "gender": gender,
        "age": age,
        "class": chosen_class,
        "hp": stats["hp"],
        "attack": stats["attack"],
        "magic": stats["magic"],
        "hair_color": hair_color,
        "eye_color": eye_color
    }

    print("\n--- Character Created ---")
    print(f"Name: {player['first_name']} {player['last_name']} The {player['title']}")

    # Now that character creation is complete, enable saving and set the next game state
    can_save = True
    game_state = "after_character_creation"
    save_game()

# ----------------- Story Input Helper -----------------
def story_input(prompt, store_choice_key=None):
    """
    Primary helper for story prompts. If store_choice_key is provided and that key exists in player,
    automatically uses the saved choice and prints the prompt to show context.
    """
    global player

    if store_choice_key and store_choice_key in player:
        # print prompt for context, then return the stored value
        print(prompt, end="")
        print(player[store_choice_key])
        return player[store_choice_key]

    user_input = input(prompt)
    if store_choice_key:
        player[store_choice_key] = user_input
    return user_input

# ----------------- STORY PROGRESSION -----------------

# ----------------- WAKING UP -----------------
if game_state == "after_character_creation":

    story_input(
        f"\nI slowly wake up in my small, cozy bedroom. The morning sun streams through the window, "
        f"illuminating my {player.get('hair_color', 'hair')} hair and the simple furniture.\n"
        "(Press Enter to sit up in bed)"
    )

    game_state = "woke_up"
    save_game()

# ----------------- FIRST CHOICES IN BEDROOM -----------------
if game_state == "woke_up":

    story_input(
        "\nAs I sit up, I notice the house is quiet. The smell of breakfast drifts from the kitchen.\n"
        "(Press Enter to continue)"
    )

    choice = story_input(
        "\n(1) Get up and explore the house\n"
        "(2) Lie back for a moment\n"
        "Choice: ",
        store_choice_key="house_choice"
    )

    if choice == "1":
        story_input(
            "\nI get out of bed and stretch, ready to start my day of adventure.\n"
            "(Press Enter to continue)"
        )
    elif choice == "2":
        story_input(
            "\nI lie back for a moment, enjoying the warmth of the morning sun. "
            "Adventure can wait a little longer.\n"
            "(Press Enter to continue)"
        )
    else:
        story_input(
            "\nUnsure what to do, I remain seated, listening to the quiet of my room.\n"
            "(Press Enter to continue)"
        )

    story_input(
        "\nA gentle knock comes at my door. It's Dr. John Roberts, the local scholar and mentor.\n"
        "(Press Enter to continue)"
    )

    if player.get('class') == "Mage":
        story_input("He notices my spellbook on the table and smiles knowingly.\n(Press Enter to continue)")
    elif player.get('class') == "Warrior":
        story_input("He eyes my sword, nodding with approval.\n(Press Enter to continue)")
    else:
        story_input("He observes my light, agile movements and nods in greeting.\n(Press Enter to continue)")

    story_input(
        f"\nDoctor: 'Good morning, {player.get('first_name', 'Traveler')}! I trust you slept well?'\n"
        "(Press Enter to continue)"
    )

    story_input(
        "\nI give a polite nod in response.\n"
        "(Press Enter to continue)"
    )

    story_input(
        "\nDoctor: 'I've received a message from the King of the North. "
        "He's in need of your help. The kingdom is under attack by a powerful enemy.'\n"
        "(Press Enter to continue)"
    )

    choice = story_input(
        "\n(1) 'Enemy? What? Are we at war?'\n"
        "(2) 'I will help immediately, Doctor.'\n"
        "Choice: ",
        store_choice_key="war_choice"
    )

    if choice == "1":
        story_input(
            "\nI ask, 'Enemy? What? Are we at war?'\n"
            "(Press Enter to continue)"
        )
        story_input(
            "\nDoctor: 'Yes. Peace talks failed… and the king calls upon you.'\n"
            "(Press Enter to continue)"
        )
    elif choice == "2":
        story_input(
            "\nI reply, 'I will help immediately, Doctor.'\n"
            "(Press Enter to continue)"
        )
        story_input(
            "\nDoctor: 'Excellent. The kingdom depends on you.'\n"
            "(Press Enter to continue)"
        )
    else:
        story_input(
            "\nI nod silently, accepting the responsibility placed upon me.\n"
            "(Press Enter to continue)"
        )

    game_state = "go_to_kitchen"
    save_game()

# ----------------- KITCHEN / OUTSIDE BRIEFING -----------------
if game_state == "go_to_kitchen":

    def outside_briefing():
        story_input(
            "\nI step outside with Doctor Roberts. The cool morning air hits my face.\n"
            "(Press Enter to continue)"
        )
        story_input(
            "\nDoctor: 'The King of the North requests your help. The enemy approaches quickly.'\n"
            "(Press Enter to continue)"
        )
        story_input(
            "\nI listen carefully, feeling the weight of the task ahead.\n"
            "(Press Enter to continue)"
        )

    story_input(
        "\nI head downstairs with Doctor Roberts. The smell of breakfast fills the kitchen.\n"
        "(Press Enter to continue)"
    )

    choice = story_input(
        "\n(1) Sit for breakfast\n"
        "(2) Go outside immediately to prepare\n"
        "Choice: ",
        store_choice_key="breakfast_choice"
    )

    if choice == "1":
        story_input(
            "I eat quickly, gathering strength for the journey ahead.\n"
            "(Press Enter to continue)"
        )
        story_input(
            "\nDoctor: 'Good. You'll need the energy for what's coming.'\n"
            "(Press Enter to continue)"
        )
        story_input(
            "\nI finish my meal and stand up.\n"
            "(Press Enter to continue)"
        )
        outside_briefing()
    else:
        outside_briefing()

    game_state = "after_briefing"
    save_game()
