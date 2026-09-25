import os
import csv
from rapidfuzz import process, fuzz


BASE_DIR = os.path.dirname(
    os.path.dirname(
        os.path.abspath(__file__)
    )
)

LGD_FILE = os.path.join(
    BASE_DIR,
    "data",
    "LGD",
    "villages_clean.csv"
)

COORDINATE_FILE = os.path.join(
    BASE_DIR,
    "data",
    "LGD",
    "village_coordinates.csv"
)


def load_villages():

    villages = []

    with open(
        LGD_FILE,
        "r",
        encoding="utf-8-sig"
    ) as file:

        reader = csv.DictReader(file)

        for row in reader:

            name = row["Village Name "].strip()

            if not name:
                continue

            villages.append({
                "name": name,
                "district": row["District Name"].strip(),
                "subdistrict": row["Sub-District Name"].strip(),
                "village_code": row["Village Code"].strip()
            })

    return villages


def load_coordinates():

    coordinates = {}

    with open(
        COORDINATE_FILE,
        "r",
        encoding="utf-8-sig"
    ) as file:

        reader = csv.DictReader(file)

        for row in reader:

            coordinates[row["Village Code"].strip()] = {
                "latitude": float(row["Latitude"]),
                "longitude": float(row["Longitude"])
            }

    return coordinates


VILLAGES = load_villages()
COORDINATES = load_coordinates()


VILLAGE_NAMES = [
    village["name"]
    for village in VILLAGES
]


def search_location(query):

    query = query.strip()

    if not query:
        return []


    matches = process.extract(
        query,
        VILLAGE_NAMES,
        scorer=fuzz.WRatio,
        limit=5,
        score_cutoff=60
    )


    results = []


    for match_name, score, _ in matches:

        for village in VILLAGES:

            if village["name"] == match_name:

                code = village["village_code"]

                coordinate = COORDINATES.get(code)


                result = {
                    "name": village["name"],
                    "district": village["district"],
                    "subdistrict": village["subdistrict"],
                    "state": "Madhya Pradesh",
                    "village_code": code,
                    "score": score
                }


                if coordinate:

                    result["latitude"] = coordinate["latitude"]
                    result["longitude"] = coordinate["longitude"]


                results.append(result)

                break


    return results