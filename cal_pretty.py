import json

async def prettify_and_count(data, detailed_format=True):
    json_data = json.loads(data)
    
    if not json_data.get("food", []):
        json_data["pretty"] = "Не могу найти еду"
        resulting_json = json.dumps(json_data, ensure_ascii=False, indent=2)
        print(resulting_json)
        return resulting_json
    
    pretty_list = []

    for item in json_data["food"]:
        nutritional_value = item["nutritional_value"]
        fats = round(nutritional_value["fats"], 1)
        carbs = round(nutritional_value["carbs"], 1)
        protein = round(nutritional_value["protein"], 1)

        kcal = round(fats * 9 + carbs * 4 + protein * 4, 1)
        nutritional_value["kcal"] = kcal

        if detailed_format:
            pretty_str = f"{item['description']} {item['weight']}г - {kcal} ккал ({fats}г жиров {carbs}г углеводов {protein}г белков)"
        else:
            pretty_str = (
                f"{item['description']} {item['weight']} г:</b>\n"
                f" {kcal} ккал ({fats}г жиров / {carbs}г углеводов / {protein}г белков);"
            )
        pretty_list.append(pretty_str)
    
    if detailed_format:
        pretty_output = "\n".join([f"{i+1}) {item}" for i, item in enumerate(pretty_list)])
    else:
        pretty_output = "<b>Прием пищи:</b>\n\n" + "\n".join([f"{i+1}.<b> {item}" for i, item in enumerate(pretty_list)])

    json_data["pretty"] = pretty_output

    resulting_json = json.dumps(json_data, ensure_ascii=False, indent=2)
    print(resulting_json)
    return resulting_json
