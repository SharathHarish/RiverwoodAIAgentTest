# Dummy construction data

CONSTRUCTION_DATA = {
    "RW00123": {
        "name": "Ramesh",
        "progress": 55,
        "in_progress": {"Structural Framing": 70, "Roofing": 30, "Electrical and Plumbing": 20},
        "completed": ["Foundation"],
        "pending": ["Painting", "Flooring"],
        "status": "On Schedule"
    },
    "RW00124": {
        "name": "Priya",
        "progress": 60,
        "in_progress": {"Flooring": 15},
        "completed": ["Foundation", "Walls"],
        "pending": ["Painting"],
        "status": "On Schedule"
    },
    "RW00125": {
        "name": "Amit",
        "progress": 80,
        "in_progress": {"Painting": 10},
        "completed": ["Foundation", "Walls", "Roof", "Plumbing"],
        "pending": ["Fixtures"],
        "status": "Slight Delay"
    }
}
