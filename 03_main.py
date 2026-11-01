import random
import time
import requests

# Replace with your real email. OpenStreetMap's free services ask every user to identify themselves.
HEADERS = {"User-Agent": "EatWhere/0.1 (your-email@email.com)"}

OVERPASS_SERVERS = [
    "https://overpass-api.de/api/interpreter",
    "https://overpass.kumi.systems/api/interpreter",
]

# "Flexible" in the prototype is treated as 10 km here.
DISTANCES_M = {"1": 1000, "5": 5000, "10": 10000, "flexible": 10000}

# OpenStreetMap tags that mark dietary options.
DIET_TAGS = {
    "halal": "diet:halal",
    "vegetarian": "diet:vegetarian",
    "vegan": "diet:vegan",
}

# Rough guesses used to nudge the ranking for "healthy" and "comforting".
HEALTHY = {"salad", "vegan", "vegetarian", "sushi", "japanese", "vietnamese",
           "mediterranean", "greek", "lebanese", "juice", "thai"}
COMFORTING = {"burger", "pizza", "italian", "american", "pasta", "chinese",
              "indian", "british", "fish_and_chips", "ramen", "korean"}

# The same options as the Figma prototype: (value used by the code, label shown to the user).
MOODS = [("healthy", "Healthy"), ("viral", "Viral/Trending"), ("comforting", "Comforting"),
         ("new", "New"), ("skip", "I don't have a preference")]
DISTANCES = [("1", "1 km"), ("5", "5 km"), ("10", "10 km"), ("flexible", "I'm flexible")]
COMPANIONS = [("by myself", "By myself"), ("family", "Family"), ("friends", "Friends"),
              ("partner", "Partner"), ("colleagues", "Colleagues"), ("group", "Group")]

BUDGET_MIN, BUDGET_MAX = 10, 100   # the slider goes £10 to £100+

BACK = object()   # returned when the user types "back"


# ---------- API calls ----------

def geocode(place):
    """Turn a place name into latitude and longitude."""
    response = requests.get(
        "https://nominatim.openstreetmap.org/search",
        params={"q": place, "format": "json", "limit": 1},
        headers=HEADERS,
        timeout=10,
    )
    if response.status_code != 200:
        raise RuntimeError(f"Location lookup failed (status {response.status_code}).")
    results = response.json()
    if not results:
        raise ValueError(f"No location found for '{place}'.")
    return float(results[0]["lat"]), float(results[0]["lon"])


def find_places(lat, lon, radius_m):
    """Find restaurants and cafes around a point, with retries and a backup server."""
    query = f"""
    [out:json][timeout:40];
    nwr["amenity"~"^(restaurant|cafe)$"](around:{radius_m},{lat},{lon});
    out center tags 150;
    """
    for server in OVERPASS_SERVERS:
        for attempt in range(2):
            try:
                response = requests.post(
                    server, data={"data": query}, headers=HEADERS, timeout=60
                )
                if response.status_code == 200:
                    return response.json()["elements"]
                print(f"{server} returned {response.status_code}, retrying...")
            except requests.exceptions.RequestException as e:
                print(f"{server} failed (attempt {attempt + 1}): {type(e).__name__}")
            time.sleep(3)
    raise RuntimeError("All servers failed. Try again in a few minutes.")


# ---------- Filtering and ranking ----------

def get_cuisines(tags):
    """Return cuisines as a list, e.g. 'austrian;german' -> ['austrian', 'german']."""
    raw = tags.get("cuisine", "")
    return [c.strip().lower() for c in raw.split(";") if c.strip()]


def meets_diet(tags, diet):
    """True only if OpenStreetMap confirms the dietary option."""
    yes = {"yes", "only"}
    if tags.get(DIET_TAGS[diet]) in yes:
        return True
    # A vegan place also counts as vegetarian.
    if diet == "vegetarian" and tags.get("diet:vegan") in yes:
        return True
    return False


def score(tags, answers):
    """Higher score = better match. More complete listings also score higher.

    Honest limits: OpenStreetMap has no price data and no popularity data, so
    "budget", "viral" and "new" cannot filter anything yet. Budget and who you
    are eating with only give a small nudge between cafes and restaurants.
    """
    points = 0
    mood = answers["mood"]
    cuisines = set(get_cuisines(tags))
    amenity = tags.get("amenity")

    if mood == "healthy" and cuisines & HEALTHY:
        points += 3
    if mood == "comforting" and cuisines & COMFORTING:
        points += 3

    # Who you are eating with: cafes for solo meals, sit-down restaurants for company.
    if answers["company"] == "by myself" and amenity == "cafe":
        points += 1
    if answers["company"] != "by myself" and amenity == "restaurant":
        points += 1

    # Budget: a low budget leans towards cafes, a high budget towards restaurants.
    if answers["budget"] <= 15 and amenity == "cafe":
        points += 1
    if answers["budget"] >= 60 and amenity == "restaurant":
        points += 1

    if cuisines:
        points += 1
    if tags.get("website") or tags.get("contact:website"):
        points += 1
    if tags.get("opening_hours"):
        points += 1
    if tags.get("addr:street"):
        points += 1
    return points


def build_candidates(elements, answers):
    """Keep named places that meet every dietary choice, then rank them."""
    candidates = []
    for element in elements:
        tags = element.get("tags", {})
        if not tags.get("name"):
            continue
        if not all(meets_diet(tags, d) for d in answers["diets"]):
            continue
        candidates.append({"tags": tags, "score": score(tags, answers)})
    # Highest score first; random order among ties so refreshes vary.
    candidates.sort(key=lambda c: (c["score"], random.random()), reverse=True)
    return candidates


def pick_three(candidates):
    """Best Match, Alternative, Hidden Gem."""
    picks = []
    if len(candidates) >= 1:
        picks.append(("Best Match", candidates[0]))
    if len(candidates) >= 2:
        picks.append(("Alternative", candidates[1]))
    if len(candidates) >= 3:
        used = set(get_cuisines(candidates[0]["tags"])) | set(get_cuisines(candidates[1]["tags"]))
        rest = candidates[2:]
        # Hidden Gem: prefer a cuisine not already shown.
        different = [c for c in rest
                     if get_cuisines(c["tags"]) and not set(get_cuisines(c["tags"])) & used]
        picks.append(("Hidden Gem", random.choice(different) if different else rest[0]))
    return picks


# ---------- Display ----------

def get_address(tags):
    parts = [
        " ".join(p for p in [tags.get("addr:housenumber"), tags.get("addr:street")] if p),
        tags.get("addr:postcode", ""),
    ]
    return ", ".join(p for p in parts if p) or "address not listed"


def show_pick(number, label, candidate):
    tags = candidate["tags"]
    cuisine = ", ".join(get_cuisines(tags)) or "cuisine not listed"
    website = tags.get("website") or tags.get("contact:website")

    print(f"{number}. [{label}] {tags['name']}")
    print(f"    {get_address(tags)}")
    print(f"    Cuisine: {cuisine}")
    if website:
        print(f"    Website: {website}")
    print()


def time_to_eat(candidate):
    """The final screen: just the chosen place."""
    tags = candidate["tags"]
    website = tags.get("website") or tags.get("contact:website")
    print("\n=============== Time to Eat ===============")
    print(f"  {tags['name']}")
    print(f"  {get_address(tags)}")
    if website:
        print(f"  Official website: {website}")
    print("===========================================")


def show_summary(answers):
    diets = ", ".join(answers["diets"]) or "none"
    if answers["others"]:
        diets += f" + other: {answers['others']}"
    mood = dict(MOODS)[answers["mood"]]
    distance = dict(DISTANCES)[answers["distance"]]
    budget = f"£{answers['budget']}" + ("+" if answers["budget"] >= BUDGET_MAX else "")
    print("\nYour answers so far:")
    print(f"  Mood:                {mood}")
    print(f"  Location:            {answers['place']} ({distance})")
    print(f"  Eating with:         {answers['company']}")
    print(f"  Budget per person:   {budget}")
    print(f"  Dietary:             {diets}")


# ---------- Questions (every answer is printed back so it stays visible) ----------
# Type "back" at any question to go to the previous one, like the Back button.

def ask():
    """Ask for input and print the answer so it stays visible in the output."""
    answer = input("> ").strip()
    print(f"   You answered: {answer if answer else '(nothing)'}")
    if answer.lower() == "back":
        return BACK
    return answer


def ask_choice(prompt, options):
    """Pick one option by number or by name. options = [(value, label), ...]."""
    while True:
        print(f"\n{prompt} (type a number, or 'back')")
        for n, (_, label) in enumerate(options, 1):
            print(f"  {n}) {label}")
        answer = ask()
        if answer is BACK:
            return BACK
        text = answer.lower()
        if text.isdigit() and 1 <= int(text) <= len(options):
            return options[int(text) - 1][0]
        for value, label in options:
            if text in (value.lower(), label.lower()):
                return value
        print("Please choose one of the options.")


def step_mood(answers):
    result = ask_choice("First, what are you in the mood for?", MOODS)
    if result is BACK:
        return BACK
    answers["mood"] = result


def step_place(answers):
    while True:
        print("\nNext, where are you planning to eat? (e.g. Shoreditch, London)")
        result = ask()
        if result is BACK:
            return BACK
        if result:
            answers["place"] = result
            return


def step_distance(answers):
    result = ask_choice(f"Cool! How far from {answers['place']} would you be happy to go?",
                        DISTANCES)
    if result is BACK:
        return BACK
    answers["distance"] = result


def step_company(answers):
    result = ask_choice("Who are you looking to eat with?", COMPANIONS)
    if result is BACK:
        return BACK
    answers["company"] = result


def step_budget(answers):
    while True:
        print(f"\nWhat's your estimated budget per person? "
              f"(£{BUDGET_MIN} to £{BUDGET_MAX}+, or 'back')")
        result = ask()
        if result is BACK:
            return BACK
        digits = result.replace("£", "").replace("+", "").strip()
        if digits.isdigit():
            answers["budget"] = max(BUDGET_MIN, min(BUDGET_MAX, int(digits)))
            print(f"Great, thanks for letting me know! (£{answers['budget']})")
            return
        print(f"Please enter a number between {BUDGET_MIN} and {BUDGET_MAX}.")


def step_diets(answers):
    """Diets filter results; 'others' is only shown back as a reminder."""
    print("\nNow, is there any dietary restriction?")
    print("Select any: halal, vegetarian, vegan, others (comma-separated). "
          "Type 'none' or press Enter for none, or 'back'.")
    raw = ask()
    if raw is BACK:
        return BACK

    diets = []
    others = ""
    for item in raw.lower().split(","):
        item = item.strip()
        if not item or item == "none":
            continue
        if item in DIET_TAGS:
            diets.append(item)
        elif item == "others":
            print("\nPlease enter your other restriction (e.g. nut allergy).")
            result = ask()
            others = "" if result is BACK else result
        else:
            print(f"(Skipping '{item}', not one of the options.)")
    answers["diets"] = diets
    answers["others"] = others


STEPS = [step_mood, step_place, step_distance, step_company, step_budget, step_diets]

# What the "What would you like to change?" menu runs for each choice.
CHANGE_MENU = {
    "mood": [step_mood],
    "location": [step_place, step_distance],
    "people": [step_company],
    "budget": [step_budget],
    "dietary": [step_diets],
}


def collect_answers():
    """Walk through every question, allowing 'back'."""
    answers = {}
    i = 0
    while i < len(STEPS):
        result = STEPS[i](answers)
        if result is BACK:
            i = max(0, i - 1)
        else:
            i += 1
    return answers


def confirm_answers(answers):
    """'Would you like to change your answers?' step from the prototype."""
    while True:
        show_summary(answers)
        print("\nThat's all the information we needed.")
        print("Before we show you our recommendations, would you like to change your answers? (yes/no)")
        reply = ask()
        if reply is BACK or reply.lower() in ("no", "n"):
            return
        if reply.lower() in ("yes", "y"):
            choice = ask_choice("What would you like to change?",
                                [(k, k.capitalize()) for k in CHANGE_MENU])
            if choice is BACK:
                continue
            for step in CHANGE_MENU[choice]:
                step(answers)
        else:
            print("Please answer yes or no.")


# ---------- Search and results ----------

def search_and_show(answers):
    """Returns 'done', 'edit' (go back to change answers) or 'error'."""
    print("\nLoading up recommendations... Please wait.")
    try:
        lat, lon = geocode(answers["place"])
        print(f"Found location at {lat}, {lon}. Searching for restaurants (this can take a minute)...")
        elements = find_places(lat, lon, DISTANCES_M[answers["distance"]])
        print(f"Got {len(elements)} places back from OpenStreetMap.")
    except (ValueError, RuntimeError, requests.exceptions.RequestException) as e:
        print(f"\nSorry, something went wrong: {e}")
        return "error"

    candidates = build_candidates(elements, answers)
    print(f"{len(candidates)} of them are named and match your dietary choices.")

    if not candidates:
        print("\nThere is No Match. Please change responses to get matches.")
        return "edit"

    while True:
        print("\nOur Picks for You\n")
        picks = pick_three(candidates)
        for number, (label, candidate) in enumerate(picks, 1):
            show_pick(number, label, candidate)

        if answers["others"]:
            print(f"Note: you listed '{answers['others']}'.")
            print("I can't check this against the restaurant data, so please confirm "
                  "with the restaurant before you order.\n")

        shown = [c for _, c in picks]
        remaining = [c for c in candidates if c not in shown]

        while True:
            print(f"Type 1-{len(picks)} to choose a place, 'refresh' for more, or 'back' to change answers.")
            reply = ask()
            if reply is BACK:
                return "edit"
            text = reply.lower()
            if text.isdigit() and 1 <= int(text) <= len(picks):
                time_to_eat(picks[int(text) - 1][1])
                return "done"
            if text == "refresh":
                if not remaining:
                    print("That's everything I found. Try a bigger distance for more.")
                    continue
                candidates = remaining
                break
            print("Please choose one of the options.")


# ---------- Main flow ----------

def main():
    print("\nWhere Should We Eat?")
    print("Hello! Let's help you find a place to satisfy your belly!")
    print("(Type 'back' at any question to go to the previous one.)")

    while True:
        answers = collect_answers()
        while True:
            confirm_answers(answers)
            outcome = search_and_show(answers)
            if outcome != "edit":
                break
        print("\nNew search? (y/n)")
        reply = ask()
        if reply is BACK or reply.lower() not in ("y", "yes"):
            print("\nEnjoy your meal!")
            break


if __name__ == "__main__":
    main()
