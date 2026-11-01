# Eat Where - Restaurant Decision Assistant
A Python-based restaurant recommendation prototype designed to make everyday dining decisions easier.

Rather than browsing through endless restaurant listings, users answer a few simple questions about their mood, location, budget, dining companions and dietary preferences. The prototype then narrows the results to three restaurant recommendations.

# Features 

- Mood-based restaurant recommendations

- Location search using geocoding

- Nearby restaurant discovery using OpenStreetMap data

- Budget and dietary preference filtering

- Three recommendation categories: Best Match, Alternative and Hidden Gem

# Technologies & APIs

- Python – Core application logic and recommendation system

- Requests – API requests

- Nominatim API – Converts location names into geographical coordinates

- Overpass API – Retrieves nearby restaurant listings from OpenStreetMap

# Files

- `03_main.py`: the full prototype. Run this one.
  
- `01_nominatim_test.py`: an early test of the location lookup (Nominatim).
  
- `02_restaurant_search.py`: an early test of the restaurant search (Overpass).

# Setup

Before running any of the scripts, replace your-email@email.com in the User-Agent header with your own email

# Running the Project

Clone this repository.

Install the required dependencies:

pip install -r requirements.txt

Run the application:

python 03_main.py


# Limitations

This is an early-stage prototype. Restaurant information depends on OpenStreetMap data, which may have incomplete or missing details.

- OpenStreetMap has no price or popularity data, so budget only nudges the ranking and the "Viral/Trending" and "New" moods don't change results yet.
- Dietary filtering only includes places that have been tagged in OpenStreetMap, so some suitable restaurants may be missed.
- "Other" dietary needs (such as allergies) can't be checked. The prototype reminds users to confirm with the restaurant.

# Future Improvements

Improve restaurant ranking and recommendation relevance.

Expand restaurant information and dietary filtering.

Develop a graphical user interface.

Conduct further user testing.

# Why I built this

I surveyed 101 people about how they decide where to eat. Choice overload and budget or distance were among the most common difficulties. My hypothesis was that narrowing many options to a few relevant ones would reduce decision fatigue. I designed the flow in Figma, then built this Python prototype to test whether it could work with real restaurant data.

Full Portfolio Case Study: https://www.figma.com/deck/zwGMLpsRSHwmHVVVaUYh5H
