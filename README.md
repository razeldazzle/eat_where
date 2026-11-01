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

# Running the Project

Clone this repository.

Install the required dependencies:

pip install -r requirements.txt

Run the application:

python main.py

# Limitations

This is an early-stage prototype. Restaurant information depends on OpenStreetMap data, which may have incomplete or missing details, including prices, ratings and dietary information.

# Future Improvements

Improve restaurant ranking and recommendation relevance.

Expand restaurant information and dietary filtering.

Develop a graphical user interface.

Conduct further user testing.
