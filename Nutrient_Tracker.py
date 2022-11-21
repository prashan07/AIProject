import openfoodfacts as off
import os
import time
from datetime import date
import re

def main():
    # check last time today_food.csv file was modified.  If yesterday, reset
    timeSinceEpoch = os.path.getmtime("today_food.csv")
    timeString = time.strftime('%Y-%m-%d %H:%M:%S',
                               time.localtime(timeSinceEpoch))
    # Checks the last time the file was modified.  If the last time it was
    # modified was before today, it resets
    if timeString < (str(date.today()) + " 00:00:00"):
        open("today_food.csv", 'w').close()

    # This function checks the past foods and determines if they need to be
    # removed since they haven't been eaten in a while
    check_past_foods()

    # Runs the menu in a way where there won't be a ton of embedded functions
    # running for no purpose
    repeat = menu()
    while repeat:
        repeat = menu()

# menu function
def menu():
    # Presents the user interface and options to select
    print("Welcome to Nutrient Tracker")
    print("Please select an option")
    selection = input("1. Add a food\n2. Assess Today\n3. Exit\n"
                      "Your Selection: ")
    # Input validates the selection
    while selection not in ["1", "2", "3"]:
        print("\nNot a valid option.  Please try again")
        selection = input("1. Add a food\n2. Assess Today\nYour Selection: ")
    # Directs to specified function based on selection.  Again, written in a
    # while loop to prevent constant embedded functions
    if selection == '1':
        repeat = add_food()
        while repeat:
            repeat = add_food()
        return True
    elif selection == '2':
        assess_day()
        return True
    elif selection == '3':
        return False
    else:
        # Might be unnecessary to write this but it doesn't hurt
        print("Something went wrong please restart the application")

# add food function
def add_food():
    # Ask for user food barcode
    print("\nPlease enter the barcode on the food you wish to add.")
    barcode = input("Barcode: ")
    # Uses the OpenFoodFacts Database to find the item
    item = off.products.get_product(barcode)
    # If the item status is 0, it means the food wasn't found so ask
    # the user for another barcode
    while item["status"] == 0:
        print("\nBarcode not found.  Please try again")
        barcode = input("Barcode: ")
        item = off.products.get_product(barcode)
    # Just in case a barcode changed, ask the user if the item is correct
    # Displays name and brand
    while item["status"] == 1:
        print("\nITEM FOUND!")
        print("Item Name: ", item["product"]["product_name"])
        print("Brand: ", item["product"]["brands"].split(",")[0])
        print("Is this item correct?")
        selection = input("[y or n]: ")
        # Input validation
        while selection not in ["y", "yes", "n", "no", "Y", "N", "No", "Yes"]:
            print("Not a valid option.  Please try again")
            print("Item Name: ", item["product"]["product_name"])
            print("Brand: ", item["product"]["brands"].split(",")[0])
            print("Is this item correct?")
            selection = input("[y or n]: ")
        # If the product is wrong ask the user if they want to try again
        if selection in ["n", "no", "No"]:
            print("Would you like to try again?")
            repeat = input("[y or n]: ")
            # More input validation
            while repeat not in ["y", "yes", "n", "no", "Y", "N", "No", "Yes"]:
                print("Not a valid option.  Please try again")
                print("Would you like to try again?")
                repeat = input("[y or n]: ")
            # If the user says yes, then return true so the menu function will
            # run this function again
            if repeat in ["y", "Y", "yes", "Yes"]:
                return True
            # If they say no then they will be brought back to the menu
            else:
                return False
        # If the barcode did give them the right food item, break the loop
        # and move on to adding the data to the files
        else:
            break

    # This section grabs all the nutrients, adds them to today's food,
    # and shows the user what was added
    print("===FOOD DATA===")
    # The 'todayString' variable is what will eventually end up in the file
    # and it is constantly added to as new data is discovered
    todayString = item["product"]["product_name"]
    # The 'nutriments' variable is the dictionary containing all the
    # nutrient info of the item
    nutriments = item["product"]["nutriments"]
    print("Nutriments: ", nutriments)
    # Open up the FDA_DV.csv file for reading
    FDA = open("FDA_DV.csv", 'r')
    # Iterate through each line
    for i in FDA.readlines():
        # Split the line into the nutrient and the recommended value
        line = i.split(",")
        # This sets the key to find in the dictionary
        value_to_find = line[0] + "_serving"
        # We put this in a try just in case the value doesn't exist
        try:
            # We find the value of the nutrient
            nutrient_level = nutriments[value_to_find]
            # We also need the unit to do some future multiplication
            unitString = line[0] + "_unit"
            unit = nutriments[unitString]
            # Check what the unit is
            if unit == "µg":
                # If it's micro grams we have to multiply by 10000
                amount = float(nutrient_level) * 10000
                # Add the amount to the todayString
                todayString += "," + str(amount)
                # Tell the user the amount
                print(line[0], ",", amount, "mcg")
            else:
                # If it is milligrams we need to multiply by 1000
                amount = float(nutrient_level) * 1000
                # Add the amount to the todayString
                todayString += "," + str(amount)
                # Tell the user the amount
                print(line[0], ",", amount, "mg")
        # We need to check for KeyErrors if the nutrient isn't present
        except KeyError:
            # Simply add 0.0 to the todayString
            todayString += ",0.0"
            # Tell the user the amount
            print(line[0], ",0.0")
    # We no longer need the FDA_DV file so we can close it
    FDA.close()
    # We add a newline to the end of the string so we can add more foods later
    todayString += "\n"
    # Open up the today food file for appending and add the new food data
    today = open("today_food.csv", 'a')
    today.write(todayString)
    # Make sure to close it
    today.close()

    # Now that the food has been added to the file for today, we need to
    # check whether is needs to be added to the other files

    # The past food file is used to determine if the food is eaten frequently
    # and should be added to the frequently eaten foods.  We open it
    # in read/write mode
    past = open("past_food.csv", 'r+')
    # We will read all the lines and set our self back to the beginning
    # for writing
    lines = past.readlines()
    past.seek(0)
    # We will set a flag for whether the food was found to be already in the
    # file
    found = 0
    # First we make sure the file wasn't empty to start.  If it was, we
    # can just write in the food with a time stamp for later use
    if not lines:
        past.write(item["product"]["product_name"] + ",1"
                   + "," + str(date.today()) + "\n")
    # if it wasn't empty, we are going to iterate through the file of
    # commonly eaten foods and see if it is worth it to add to the frequent
    # foods list
    else:
        for i in lines:
            # We will split the foods into their names, times eaten, and the
            # date we last ate it
            splitLines = i.split(",")
            # First we check the line we are on and see if it is the food
            # we just added
            if splitLines[0] == item["product"]["product_name"]:
                # We mark that we found the food for later use
                found = 1
                # If it was the food we just added we increase the number of
                # times it was eaten by one
                splitLines[1] = int(splitLines[1]) + 1
                # Then we write this amount back into the file with
                # the date for future use
                past.write(item["product"]["product_name"] + ","
                         + str(splitLines[1]) + "," + str(date.today()) + "\n")
                # This is where the program determines if the food is
                # something considered eaten frequently.  This value
                # is what will be changed to see what seems best rationally
                if int(splitLines[1]) > 3:
                    # We will then open the frequent foods file for reading
                    frequentFile = open("frequent_foods.csv", 'r')
                    # Read all the lines
                    frequentLines = frequentFile.readlines()
                    # Set a flag to check and see if it is already in the
                    # frequent foods file
                    presentInFrequent = 0
                    # Iterate through the lines
                    for i in frequentLines:
                        # Split it into the name of the item and what it
                        # is proficient in
                        frequentSplit = i.split(",")
                        # If it is already present in the file then there is
                        # no need to go any further so break the loop
                        if frequentSplit[0] == item["product"]["product_name"]:
                            presentInFrequent = 1
                            break
                    # We can close the file now that we have read all we need
                    frequentFile.close()
                    # If the item wasn't already in the file, we need to add it
                    if presentInFrequent == 0:
                        # We run another function that returns a list of what
                        # nutrients the item has a high concentration of.
                        # If the food has no nutrients that are high, then
                        # we won't add it to our frequent foods file
                        if high_check(item) != []:
                            # If it is high in some nutrient we need to write
                            # it to the frequent foods file
                            frequentFile = open("frequent_foods.csv", 'a')
                            for i in high_check(item):
                                # This writes a line in the frequent foods
                                # file like this: item, what it is high in
                                frequentFile.write(item["product"]\
                                            ["product_name"] + "," + i + "\n")
                            # Make sure we close the file
                            frequentFile.close()
            # If the line does not contain the food we just added
            # simply write it back into the file
            else:
                past.write(i)
        # If we never found the food in the past foods file, we need to write
        # it in
        if found == 0:
            past.write(item["product"]["product_name"] + ",1"
                   + "," + str(date.today()) + "\n")
    # Truncate the whole file and close it
    past.truncate()
    past.close()

    # Now that the food has been added and the data has been saved we will
    # ask the user if they want to add another food
    print("Would you like to add another food?")
    repeat = input("[y or n]: ")
    # Input validation
    while repeat not in ["y", "yes", "n", "no", "Y", "N", "No", "Yes"]:
        print("Not a valid option.  Please try again")
        print("Would you like to try again?")
        repeat = input("[y or n]: ")
    # If they say yes we can return true to the menu function so it will
    # run this function again
    if repeat in ["y", "Y", "yes", "Yes"]:
        return True
    # If they don't want to add another food, it will return them to the menu
    else:
        return False

# This function checks if the food is high in a certain nutrient based on
# our set standards.  This is what can be edited as well to try to mimic
# rationality
def high_check(item):
    # Initialize a list to return
    high_list = []
    # Grab the nutriments dictionary
    nutriments = item["product"]["nutriments"]
    # Open the FDA_DV.csv file
    FDA = open("FDA_DV.csv", 'r')
    # Iterate through it's lines
    for i in FDA.readlines():
        # split it into the nutrients and their Daily Values
        line = i.split(",")
        # Grab the name of the nutrient we are trying to find
        string_to_find = line[0] + "_serving"
        # Use a try in case the nutrient isn't found and throws a KeyError
        try:
            # Look for the nutrient in the dictionary
            nutrient_level = nutriments[string_to_find]
            # Find it's unit for some future math
            unitString = line[0] + "_unit"
            unit = nutriments[unitString]
            # Check which unit it is
            if unit == "µg":
                # If it is micro grams we need to multiply by 10000
                amount = float(nutrient_level) * 10000
            else:
                # If it is milligrams we need to multiply by 1000
                amount = float(nutrient_level) * 1000
            # The base is the base amount the FDA suggests.  We grab this
            # amount from the file and strip it of all useless characters
            base = line[1].replace("mg", "").replace("mcg", "").rstrip("\n")
            # Turn that str into an int
            base = int(base)
            # This is where we determine if the amount is considered high.
            # This can be changed to better seem rational
            if amount >= base * 0.2:
                # If the nutrient is considered high, add it to the list
                high_list.append(line[0])
        # If the nutrient doesn't exist in the product, just move on
        except KeyError:
            continue
    # Return the list of nutrients considered high in content
    return high_list

# This function checks to see what food shouldn't be frequent anymore
def check_past_foods():
    # Open up the past foods file for read/write
    past = open("past_food.csv", 'r+')
    # Read the lines and go back to the beginning
    lines = past.readlines()
    past.seek(0)
    # Iterate through the lines
    for i in lines:
        line = i.split(",")
        # Check the last date that the food was eaten
        pastDate = line[2]
        # Grab the date for today
        today = str(date.today())
        # Make a cut off date for when the food should be considered
        # no longer frequent.  We can also change this to be more rational
        cutoffDate = pastDate[0:8] + str(int(pastDate[8:10]) + 2)
        # Check if we are passed the cutoff date
        if today >= cutoffDate:
            # If we are past the cutoff date we need to delete the item from
            # both the past foods file and the frequent foods file
            frequent = open("frequent_foods.csv", 'r+')
            # Read all the lines in frequent file and go back to the start
            FLines = frequent.readlines()
            frequent.seek(0)
            # Iterate through the lines and find the line with the same item
            for j in FLines:
                FLine = j.split(",")
                if FLine[0] == line[0]:
                    # Simply continuing will delete the item
                    continue
                else:
                    # If this is not the line with the item, write it back
                    # into the file
                    frequent.write(j)
            # Truncate and close frequent file
            frequent.truncate()
            frequent.close()
        else:
            # If the item is still considered frequent, simply write it back in
            past.write(i)
    # Truncate and close the past file
    past.truncate()
    past.close()



# assess food
def assess_day():
    FDA = open("FDA_DV.csv", 'r')
    FDARecommended = {}
    for eachFood in FDA:
        nutrient, amount = eachFood.strip().split(",")
        FDARecommended[nutrient] = float((re.findall(r'\d+', amount))[0])
    FDA.close()
    
    todayFoods = open('today_food.csv', "r")
    todayFoodTracker = {
        "vitamin-d": 0,
        "iron" : 0,
        "calcium": 0,
        "potassium": 0
    }
    for eachFood in todayFoods:
        foodName, v_d, iron, calcium, potassium = eachFood.split(",")
        todayFoodTracker["vitamin-d"] += float(v_d)
        todayFoodTracker["iron"] += float(iron)
        todayFoodTracker["calcium"] += float(calcium)
        todayFoodTracker["potassium"] += float(potassium)
    todayFoods.close()

    user_vd, user_iron, user_calcium, user_potassium = 0, 0, 0, 0
    if todayFoodTracker["vitamin-d"] < FDARecommended["vitamin-d"]:
        user_vd = -1
    if todayFoodTracker["iron"] < FDARecommended["iron"]:
        user_iron = -1
    if todayFoodTracker["calcium"] < FDARecommended["calcium"]:
        user_calcium = -1
    if todayFoodTracker["potassium"] < FDARecommended["potassium"]:
        user_potassium = -1
    
    if user_vd == 0 and user_iron == 0 and user_calcium == 0 and user_potassium == 0:
        print("Awesome! You have fulfilled all your nutrients requirement for today!")
    
    if user_vd == -1:
        print("You still need {:.2f} mcg vitamin-d".format(FDARecommended["vitamin-d"]-todayFoodTracker["vitamin-d"]))
        # Recommend vitamin-d food
        frequentFoods = open("frequent_foods.csv", 'r')
        recommendedFood = None
        for eachFood in frequentFoods:
            food, nutrient = eachFood.strip().split(",")
            if nutrient == "vitamin-d":
                recommendedFood = food
                break
        frequentFoods.close()
        # if recommendedFood is None then search and recommend from default_foods.csv
        if recommendedFood is None:
            defaultFoods = open("default_foods.csv", 'r')
            for eachFood in defaultFoods:
                food, nutrient = eachFood.strip().split(",")
                if nutrient == "vitamin-d":
                    recommendedFood = food
                    break
            defaultFoods.close()
        if recommendedFood is None:
            print("Something is missing!")
        print("{:s} is rich in vitamin-d".format(recommendedFood))
        print()

    if user_iron == -1:
        print("You still need {:.2f} mg iron".format(FDARecommended["iron"]-todayFoodTracker["iron"]))
        # Recommend iron food
        frequentFoods = open("frequent_foods.csv", 'r')
        recommendedFood = None
        for eachFood in frequentFoods:
            food, nutrient = eachFood.strip().split(",")
            if nutrient == "iron":
                recommendedFood = food
                break
        frequentFoods.close()
        # if recommendedFood is None then search and recommend from default_foods.csv
        if recommendedFood is None:
            defaultFoods = open("default_foods.csv", 'r')
            for eachFood in defaultFoods:
                food, nutrient = eachFood.strip().split(",")
                if nutrient == "iron":
                    recommendedFood = food
                    break
            defaultFoods.close()
        print("{:s} is rich in iron".format(recommendedFood))
        print()

    if user_calcium == -1:
        print("You still need {:2f} mg calcium".format(FDARecommended["calcium"]-todayFoodTracker["calcium"]))
        # Recommend calcium food
        frequentFoods = open("frequent_foods.csv", 'r')
        recommendedFood = None
        for eachFood in frequentFoods:
            food, nutrient = eachFood.strip().split(",")
            if nutrient == "calcium":
                recommendedFood = food
                break
        frequentFoods.close()
        # if recommendedFood is None then search and recommend from default_foods.csv
        if recommendedFood is None:
            defaultFoods = open("default_foods.csv", 'r')
            for eachFood in defaultFoods:
                food, nutrient = eachFood.strip().split(",")
                if nutrient == "calcium":
                    recommendedFood = food
                    break
            defaultFoods.close()
        print("{:s} is rich in calcium".format(recommendedFood))
        print()

    if user_potassium == -1:
        print("You still need {:.2f} mg potassium".format(FDARecommended["potassium"]-todayFoodTracker["potassium"]))
        # Recommend potassium food
        frequentFoods = open("frequent_foods.csv", 'r')
        recommendedFood = None
        for eachFood in frequentFoods:
            food, nutrient = eachFood.strip().split(",")
            if nutrient == "potassium":
                recommendedFood = food
                break
        frequentFoods.close()
        # if recommendedFood is None then search and recommend from default_foods.csv
        if recommendedFood is None:
            defaultFoods = open("default_foods.csv", 'r')
            for eachFood in defaultFoods:
                food, nutrient = eachFood.strip().split(",")
                if nutrient == "potassium":
                    recommendedFood = food
                    break
            defaultFoods.close()
        print("{:s} is rich in potassium".format(recommendedFood))
        print()

# Essentially I will need you to write the assess_food function which will
# take all the food in the today_food.csv and assess whether the user has met
# the values in the FDA_DV file.
# If they have, simply tell them good job or whatever but if they
# are low in something tell them how much more they need and then make
# suggestions on what they should eat.
# You should first make suggestions from the frequent foods
# file which will tell you what each food has a high content of.
# If no high value foods exist in the frequent foods file just use the default
# foods file which has some common foods that are high in the four nutrients

# I would suggest giving this a couple runs using the barcodes I provided.
# You can even use some foods you have too.
# Just take a look at how the data gets put in the files.
# If you want to see how the data is put into the frequent foods file, just
# add the Meijer Hot Chocolate I provided 4 times because that is high enough
# in calcium to be considered high

# A couple of bar codes I used to test this all

# 038000169663 pringles
# 719283995391 Meijer hot chocolate

main()
