from ibm_watsonx_ai import Credentials
from ibm_watsonx_ai.foundation_models import ModelInference
from pydantic import BaseModel, Field, ValidationError
from typing import List, Optional
import json
import os
import shutil
import io
import unittest
from unittest.mock import patch

class TestRestaurantDatabase(unittest.TestCase):

    def setUp(self):
        """Create a temporary clean database for testing."""
        self.test_file = 'structured_restaurant_data_unit_test.json'
        self.test_file_backup = 'structured_restaurant_data_unit_test.json.bak'
        self.initial_data = [{"name": "Test Cafe", "location": "Test City"}]
        with open(self.test_file, 'w') as f:
            json.dump(self.initial_data, f)

    def tearDown(self):
        """Clean up the test file after tests."""
        if os.path.exists(self.test_file):
            os.remove(self.test_file)

        if os.path.exists(self.test_file_backup):
            os.remove(self.test_file_backup)

    @patch('builtins.input')
    @patch('sys.stdout', new_callable=io.StringIO)
    def test_add_and_delete_restaurant_success(self, mock_stdout, mock_input):
        """
        Test Scenario: Add a new restaurant.
        Inputs: '3' (Add), 'yes' (Confirm), 'New Burger Joint', '6' (Exit)
        """
        # We mock the sequence of user inputs
        mock_restaurant = 'The Copper Sprout is a high-concept, Modern Appalachian farm-to-table destination that blends an industrial-chic aesthetic with rustic forest charm, featuring reclaimed wood and amber lighting to create a sophisticated yet cozy vibe. Priced in the $$ category, the menu celebrates seasonal foraging and local heritage, headlined by signature dishes like Cast-Iron Smoked Trout with pickled fiddlehead ferns and hand-foraged Wild Mushroom Risotto with aged goat cheese. The experience is designed to be intimate and earthy, making it a premier spot for those seeking high-quality, smokehouse-influenced cuisine in a refined, atmospheric setting.'
        mock_input.side_effect = ['3', 'yes', mock_restaurant, '6']

        # Run the app
        try:
            manage_restaurants(self.test_file, self.test_file_backup)
        except SystemExit:
            pass # Handle exit if your script uses sys.exit()

        # Check if the data was actually saved
        with open(self.test_file, 'r') as f:
            data = json.load(f)

        print(data)
        self.assertEqual(len(data), 2)
        self.assertIn("✅ Restaurant added.", mock_stdout.getvalue())

        mock_input.side_effect = ['5', 'yes', 1, '6']

        # Run the app
        try:
            manage_restaurants(self.test_file, self.test_file_backup)
        except SystemExit:
            pass # Handle exit if your script uses sys.exit()

        # Check if the data was actually saved
        with open(self.test_file, 'r') as f:
            data = json.load(f)

        print(data)
        self.assertEqual(len(data), 1)

    @patch('builtins.input')
    @patch('sys.stdout', new_callable=io.StringIO)
    def test_delete_security_cancel(self, mock_stdout, mock_input):
        """
        Test Scenario: Try to delete but say 'no' to security warning.
        Inputs: '5' (Delete), 'no' (Cancel), '6' (Exit)
        """
        mock_input.side_effect = ['5', 'no', '6']

        manage_restaurants(self.test_file, self.test_file_backup)

        with open(self.test_file, 'r') as f:
            data = json.load(f)

        self.assertEqual(len(data), 1) # Data should remain unchanged
        self.assertIn("Operation cancelled.", mock_stdout.getvalue())


### 3.1. Define the schema
class Restaurant(BaseModel):
    name: str
    location: str
    type: str
    food_style: str
    rating: Optional[float] = None
    price_range: Optional[int] = None
    signatures: List[str] = Field(default_factory=list)
    vibe: Optional[str] = None
    environment: str
    shortcomings: List[str] = Field(default_factory=list)


FILEPATH = 'structured_restaurant_data.json'
BACKUP_PATH = 'structured_restaurant_data.json.bak'
EXAMPLE_RESTAURANT_PARAGRAPH = """
    Down in **Santa Monica**, **Mar de Cortez** serves as a **sun-drenched**,
    **casual taqueria** specializing in **Baja-style seafood**.
    With a **4.2/5** rating, it captures the salt-air energy of the coast through its
    signature beer-battered snapper tacos and zesty octopus ceviche, making it a
    premier spot for open-air dining near the pier. Price range: $$.
"""
EXAMPLE_OUTPUT = """
    {{
    "name": "Mar de Cortez",
    "location": "Santa Monica",
    "type": "casual taqueria",
    "food_style": "Baja-style seafood",
    "rating": 4.2,
    "price_range": 1,
    "signatures": [
        "beer-battered snapper tacos",
        "zesty octopus ceviche"
    ],
    "vibe": "salt-air energy",
    "environment": "a premier sun-drenched spot for open-air dining near the pier."
    "shortcomings": []
    }}
"""

def manage_restaurants(file_path, backup_path):
    while True:
        data = load_data(file_path)
        print(f"\n🏨 RESTAURANT DATABASE | Records: {len(data)}")
        print("1. Browse All (Names)")
        print("2. View Detailed Record")
        print("3. Add New Restaurant")
        print("4. Edit Restaurant Info")
        print("5. Delete Restaurant")
        print("6. Exit")

        choice = input("\nAction: ")

        if choice == '1':
            print("\n--- Current Listings ---")

            for index, record in enumerate(data):
                print(f"{index+1}: {record.get('name', 'N/A')}")


        elif choice == '2':
            # YOUR CODE HERE:
            index = int(input(f"\nThere are {len(data)} records. Input record index? ").strip())
            if 0 < index < len(data)+1:
                show_restaurant_card(data[index-1], index)
            else:
                print('Invalid index')

        elif choice in ['3', '4', '5']:
            # Strict Security Warning
            print("\n❗ SECURITY WARNING: You are entering write-mode.")
            print("Changes will be saved to the database immediately.")
            confirm = input("Are you sure? (type 'yes' to proceed): ").lower()
            if confirm != 'yes':
                print("Operation cancelled.")
                continue

            if os.path.exists(file_path):
                shutil.copy(file_path, backup_path)

            if choice == '3': # ADD NEW DATA
                itemId = 1000000 + len(data) + 1 #the item id for the new data
                paragraph = input('\nAdd a new restaurant description\n')
                new_data = new_data_entry_process(paragraph, itemId)
                if not new_data:
                    print("New restaurant was not validated, try again")
                else:
                    data.append(new_data)
                    save_data(file_path, data)
                    print("✅ Restaurant added.")

            elif choice == '4': # EDIT DATA
                # YOUR CODE HERE
                edit_index = input(f"\nThere are {len(data)} restaurants. Which to update? ")
                if edit_index.isdigit() and int(edit_index) < len(data)+1:
                    edit_record = data[int(edit_index)-1]
                    for key in edit_record:
                        print(f"\n{key}: {edit_record[key]}")
                        updated_value = input(f"\nNew value for {key}? ")
                        if updated_value:
                            data[int(edit_index)-1][key] = updated_value
                    save_data(file_path, data)
                    print("✅ Record updated.")

                else:
                    print("Invalid index")

            elif choice == '5': # DELETE DATA
                del_index = input(f"\nThere are {len(data)} restaurants. Which to delete? ")
                if del_index.isdigit() and int(del_index) < len(data)+1:
                    new_data = data.pop(int(del_index)-1)
                    save_data(file_path, data)
                    print("✅ Record updated.")

                else:
                    print("Invalid index")

        elif choice == '6': # EXIT
            break
        else:
            print("Invalid input.")


def load_data(file_path):
        if not os.path.exists(file_path):
            return []

        with open(file_path, 'r', encoding="utf-8") as file:
            return json.load(file)


def show_restaurant_card(res, index):
    print(f"\n----- Restaurant #{index} -----")
    for key, value in res.items():
        print(f"+ {key}: {value}")


def save_data(file_path, data):
    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=4)


## Exercise 1: Integrate the LLM model from Lesson 1

#Update your restaurant_data_structure_prompt_generation
def restaurant_data_structure_prompt_generation(restaurant_paragraph):
	#YOUR CODE HERE
    base_system_msg = f"""
    You are an expert in data extraction.

    Instructions:
    1. Carefully read the restaurant description in the prompt.
    2. Extract the relevant information.
    3. Present your findings in structured JSON format following the schema shown in the example.
    4. For "price_range" convert dollar signs into an integer representing the number of dollar symbols.

    Important notes:
    1. Do not include additional JSON keys beyond the ones listed in the example output.
    2. Do not include the same key multiple times in the JSON.

    """

    base_user_prompt = f"""
    Task:
    Read the restaurant description and extract the following fields:
    - "name", "location", "type", "food_style", "rating" (float), "price_range" (int), "signatures" (list), "vibe", "environment", "shortcomings" (list).

    If information for a specific field is missing, return an empty list [] for lists or null for strings or numbers.

    Restaurant description:
    {restaurant_paragraph}

    Example:
    Input Restaurant Description: {EXAMPLE_RESTAURANT_PARAGRAPH}
    Output: {EXAMPLE_OUTPUT}

    """
    return base_system_msg, base_user_prompt


# Might need to explain why we are using granite here (cheap)
def llm_model(system_msg, prompt_txt, params=None):
	#YOUR CODE HERE

    #system_msg: the system message given to the LLM
    #prompt_txt: the user prompt

    model_id = "ibm/granite-4-h-small"
    project_id="skills-network"

    api_key = os.getenv("WATSONX_APIKEY") or os.getenv("API_KEY")
    if api_key:
        credentials = Credentials(url="https://us-south.ml.cloud.ibm.com", api_key=api_key)
    else:
        credentials = Credentials(url="https://us-south.ml.cloud.ibm.com")


    ### 1.1: Define the model by ModelInference
    model = ModelInference(
        model_id=model_id,
        credentials=credentials,
        project_id=project_id,
        params=params
    )

    ### 1.2: Define the messages
    messages = [
        {"role": "system", "content": system_msg},
        {"role": "user", "content": prompt_txt}
    ]

    ### 1.3: Get the final response output and return it
    response = model.chat(messages=messages)
    output_text = response["choices"][0]["message"]["content"]

    return output_text


def JSON_auto_repair_prompts(candidate_json_output, error_message):
	#YOUR CODE HERE
    #pass
    auto_repair_system_msg = """
    You are a JSON repair expert.

    Take an incorrect JSON string and a validation error message and return a perfectly formatted, valid JSON object.

    Do not be verbose, only respond with the correct JSON object.
    """
    auto_repair_prompt = f"""
    The following JSON object failed validation: {candidate_json_output}

    Received validation error: {error_message}

    Provide a correct JSON object.
    """
    return auto_repair_system_msg, auto_repair_prompt


def new_data_entry_process(paragraph, itemId):
    system_msg, prompt_txt = restaurant_data_structure_prompt_generation(paragraph)
    candidate_json_output = llm_model(system_msg, prompt_txt)
    attempts = 0 # auto correction number
    max_attempts = 3 # number of possible auto corrections
    validated = False # initial validation status
    while not validated and attempts < max_attempts:
        try:
            validated_output = Restaurant.model_validate_json(candidate_json_output)
            validated = True
        except ValidationError as e:
            attempts += 1
            repair_system_msg, repair_user_prompt = JSON_auto_repair_prompts(candidate_json_output=candidate_json_output, error_message=str(e))
            candidate_json_output = llm_model(repair_system_msg, repair_user_prompt)

    if validated:
        candidate_json_output = json.loads(candidate_json_output)
        candidate_json_output["itemId"] = itemId
        return candidate_json_output
    else:
        print(f"Warning: new restaurant was not validated after {max_attempts} attempts")
        return {}

    


# RUN THE UI
if __name__ == "__main__":
    #unittest.main() # Unit Test
    manage_restaurants(FILEPATH, BACKUP_PATH) # Actual UI Call