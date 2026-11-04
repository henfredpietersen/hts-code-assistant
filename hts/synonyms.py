"""Everyday words -> the words the tariff schedule uses for the same thing.

The schedule says "automatic data processing machines" where a shop says "laptop", and
"pneumatic tires" where it says "tyres". A query word found here gets these schedule words
added to it (the original word stays).

Written while looking at data/golden_dev.json, after data/golden_test.json was committed, so
the dev set flatters this list and the test set doesn't. Git history shows the order.
"""

SYNONYMS = {
    # spelling
    "aluminium": "aluminum", "tyre": "tire", "tyres": "tires", "colour": "color", "jewellery": "jewelry",
    "petrol": "gasoline spark-ignition", "trainers": "footwear",
    # electronics
    "laptop": "automatic data processing machines portable", "notebook computer": "automatic data processing machines portable",
    "computer": "automatic data processing machines", "pc": "automatic data processing machines",
    "smartphone": "telephones cellular networks", "phone": "telephones", "speaker": "loudspeakers", "bluetooth": "wireless",
    "tv": "television reception apparatus", "television": "television reception apparatus",
    "camera": "cameras digital", "printer": "printers printing machinery", "battery": "accumulators",
    "solar": "photovoltaic", "led": "light-emitting diode", "bulb": "lamps", "light bulb": "lamps",
    # appliances
    "fridge": "refrigerators", "refrigerator": "refrigerators household", "freezer": "freezers",
    "microwave": "microwave ovens", "hair dryer": "hair dryers electrothermic", "kettle": "electric water heaters",
    "vacuum": "vacuum cleaners", "washing machine": "laundry-type washing machines", "air conditioner": "air conditioning machines",
    # clothing and footwear
    "t-shirt": "t-shirts singlets", "tee": "t-shirts", "sweater": "sweaters pullovers", "jumper": "sweaters pullovers",
    "jeans": "trousers denim", "pants": "trousers", "shoes": "footwear", "sneakers": "footwear uppers textile",
    "running shoes": "footwear sports", "handbag": "handbags", "purse": "handbags", "towel": "toilet linen terry towelling",
    "towels": "toilet linen terry towelling",
    # household
    "pot": "cooking", "pan": "cooking", "plate": "tableware", "mug": "tableware", "dishes": "tableware",
    "drinking glasses": "glassware drinking", "bookcase": "furniture", "shelf": "furniture", "table": "furniture",
    "chair": "seats", "sofa": "seats", "couch": "seats", "mattress": "mattresses", "pillow": "pillows",
    "tent": "tents", "candle": "candles", "christmas tree": "christmas festive articles", "stroller": "baby carriages",
    "pram": "baby carriages", "pushchair": "baby carriages",
    # vehicles
    "car": "motor cars vehicles transport persons", "bike": "bicycles", "bicycle": "bicycles cycles",
    "motorbike": "motorcycles", "scooter": "scooters",
    # food and drink
    "coffee": "coffee roasted", "tea": "tea fermented", "olive oil": "olive oil virgin", "chocolate": "chocolate cocoa",
    "wine": "wine grapes", "beer": "beer malt", "whisky": "whiskies spirits", "whiskey": "whiskies spirits",
    "vodka": "vodka spirits", "shrimp": "shrimps prawns", "prawns": "shrimps prawns", "honey": "natural honey",
    "cigarettes": "cigarettes tobacco",
    # personal care
    "perfume": "perfumes toilet waters", "cologne": "toilet waters", "shampoo": "shampoos hair preparations",
    "toothpaste": "dentifrices oral dental hygiene", "deodorant": "deodorants",
    # other
    "sunglasses": "sunglasses spectacles", "glasses": "spectacles", "eyeglass": "spectacles", "eyeglasses": "spectacles",
    "watch": "wrist watches", "wristwatch": "wrist watches", "toy": "toys", "blocks": "construction sets",
    "golf": "golf", "cards": "playing cards", "guitar": "guitars string musical instruments", "piano": "pianos",
    "pallet": "pallets", "foil": "foil", "screws": "screws bolts", "hammer": "hammers hand tools",
    "books": "printed books", "toilet paper": "toilet paper", "umbrella": "umbrellas",
}
