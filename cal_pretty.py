import json


async def prettify_and_count(data):
    json_data = json.loads(data)
    pretty_list = []

    for item in json_data["food"]:
        nutritional_value = item["nutritional_value"]
        fats = round(nutritional_value["fats"], 1)
        carbs = round(nutritional_value["carbs"], 1)
        protein = round(nutritional_value["protein"], 1)

        # Calculate kcal
        kcal = round(fats * 9 + carbs * 4 + protein * 4, 1)
        nutritional_value["kcal"] = kcal

        # Create pretty string
        pretty_str = f"{item['description']} {item['weight']}г - {kcal} ккал ({fats}г жиров {carbs}г углеводов {protein}г белков)"
        pretty_list.append(pretty_str)

    # Join pretty list into one string
    pretty_output = "\n".join([f"{i+1}) {item}" for i,
                               item in enumerate(pretty_list)])

    # Add pretty string to data
    json_data["pretty"] = pretty_output

    # Print or save the resulting JSON
    resulting_json = json.dumps(json_data, ensure_ascii=False, indent=2)
    print(resulting_json)
    return resulting_json
