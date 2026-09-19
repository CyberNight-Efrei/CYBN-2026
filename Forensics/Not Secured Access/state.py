import re

def get_state(states, user_id):
    for state in states:
        if state["id"] == user_id:
            return state
    return None


with open("L17_14-09-2026.log") as f:
    lines = f.read().splitlines()

states = []
errors = set()

regex = r'^(?P<date>\d\d-\d\d-\d{4}) (?P<time>\d\d:\d\d:\d\d.\d{3}) (?P<outcome>\[\w+\]) (?P<id>[a-f\d]{8}(?:-[a-f\d]{4}){3}-[a-f\d]{12}) (?P<action>[A-Z]+) "(?P<msg>.*)"$'

for line_number, line in enumerate(lines, start=1):
    if not line.strip():
        continue

    data = re.match(regex, line)

    if not data:
        print(f'ERROR - Incorrect line format at line {line_number}: "{line}"')
        continue

    groups = data.groupdict()
    user_id = groups["id"]
    action = groups["action"]

    state = get_state(states, user_id)

    # Premier événement connu pour cet utilisateur
    if state is None:
        state = {
            "id": user_id,
            "state": "OUT" if action == "EXIT" else "IN",
            "entries": 1 if action == "ENTRY" else 0,
            "exits": 1 if action == "EXIT" else 0
        }
        states.append(state)
        continue

    # On compte toujours les entrées/sorties
    if action == "ENTRY":
        state["entries"] += 1
    elif action == "EXIT":
        state["exits"] += 1

    # Gestion de l'état
    if state["state"] == "IN" and action == "EXIT":
        state["state"] = "OUT"

    elif state["state"] == "OUT" and action == "ENTRY":
        state["state"] = "IN"

    else:
        # Une seule erreur par utilisateur : la première uniquement
        if user_id not in errors:
            errors.add(user_id)
            print(
                f'WARNING - Line {line_number}: User {user_id} has wrong state '
                f'-> current:{state["state"]} - action:{action}'
            )


print("All resulting states:")
for state in states:
    print(
        f'[{state["id"]}] : {state["state"]} '
        f'- entries:{state["entries"]} '
        f'- exits:{state["exits"]}'
    )