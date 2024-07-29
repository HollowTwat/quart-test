import json


async def prettify_and_count(data):
    pretty_list = []

    for item in data["food"]:
        nutritional_value = item["nutritional_value"]
        fats = nutritional_value["fats"]
        carbs = nutritional_value["carbs"]
        protein = nutritional_value["protein"]

        # Calculate kcal
        kcal = fats * 9 + carbs * 4 + protein * 4
        nutritional_value["kcal"] = kcal

        # Create pretty string
        pretty_str = f"{item['description']} {item['weight']}г - {kcal} ккал ({fats}г жиров {carbs}г углеводов {protein}г белков)"
        pretty_list.append(pretty_str)

    # Join pretty list into one string
    pretty_output = "\n".join([f"{i+1}) {item}" for i,
                               item in enumerate(pretty_list)])

    # Add pretty string to data
    data["pretty"] = pretty_output

    # Print or save the resulting JSON
    resulting_json = json.dumps(data, ensure_ascii=False, indent=2)
    print(resulting_json)
    return resulting_json
