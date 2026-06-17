import requests
from bs4 import BeautifulSoup
import re

area = "M27-3"  # Area code for the survey

# URL to scrape
if area == "M27-2": # 2 bed
    url = "https://www.rightmove.co.uk/property-to-rent/find.html?searchLocation=M27&useLocationIdentifier=true&locationIdentifier=OUTCODE%5E1582&rent=To+rent&radius=0.0&minBedrooms=2&maxBedrooms=2&_includeLetAgreed=on&includeLetAgreed=true&index=0&sortType=6&channel=RENT&transactionType=LETTING&displayLocationIdentifier=M27&propertyTypes=terraced&furnishTypes=unfurnished%2CpartFurnished"
    property_class = "2 bedroom terrace properties" #"2 bedroom flats" Property type
elif area == "M27-3": # 3 bed
    url = "https://www.rightmove.co.uk/property-to-rent/find.html?searchLocation=M27&useLocationIdentifier=true&locationIdentifier=OUTCODE%5E1582&rent=To+rent&radius=0.0&minBedrooms=3&maxBedrooms=3&_includeLetAgreed=on&includeLetAgreed=true&index=0&sortType=6&channel=RENT&transactionType=LETTING&displayLocationIdentifier=M27&propertyTypes=terraced&furnishTypes=unfurnished%2CpartFurnished"
    property_class = "3 bedroom terrace properties" #"3 bedroom flats" Property type
elif area == "M28-2": # 2 bed
    url = "https://www.rightmove.co.uk/property-to-rent/find.html?searchLocation=M28&useLocationIdentifier=true&locationIdentifier=OUTCODE%5E1583&radius=0.0&minBedrooms=2&maxBedrooms=2&propertyTypes=terraced&_includeLetAgreed=on&includeLetAgreed=true&sortType=6&channel=RENT&transactionType=LETTING&displayLocationIdentifier=M28&furnishTypes=unfurnished%2CpartFurnished"
    property_class = "2 bedroom terrace properties" #"2 bedroom flats" Property type
elif area == "M30-2": # 2 bed
    url = "https://www.rightmove.co.uk/property-to-rent/find.html?searchLocation=M30&useLocationIdentifier=true&locationIdentifier=OUTCODE%5E1586&rent=To+rent&radius=0.0&minBedrooms=2&maxBedrooms=2&propertyTypes=terraced&_includeLetAgreed=on&includeLetAgreed=true&furnishTypes=unfurnished%2CpartFurnished&index=0&sortType=6&channel=RENT&transactionType=LETTING&displayLocationIdentifier=M30"
    property_class = "2 bedroom terrace properties" #"2 bedroom flats" Property type
elif area == "M5-2": # 2 bed
    url = "https://www.rightmove.co.uk/property-to-rent/find.html?searchLocation=M5&useLocationIdentifier=true&locationIdentifier=OUTCODE%5E1600&radius=0.0&minBedrooms=2&maxBedrooms=2&propertyTypes=flat&_includeLetAgreed=on&includeLetAgreed=true&furnishTypes=unfurnished%2CpartFurnished&sortType=6&channel=RENT&transactionType=LETTING&displayLocationIdentifier=M5&index=0&minBathrooms=1&maxBathrooms=1&dontShow=student%2Cretirement%2ChouseShare"
    property_class = "2 bedroom terrace properties" #"2 bedroom flats" Property type
else:
    print("Area not supported for this survey.")
    exit()

print(f"Rental survey in area: {area} for {property_class} - unfurnished or part furnished")

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36"
}

response = requests.get(url, headers=headers)
soup = BeautifulSoup(response.text, "html.parser")

rents = []  # list to store rent values as integers

# Find all property listings on the page
listings = soup.find_all("div", class_="propertyCard-details")  # class may change

for listing in listings:
    # Find the property type span
    type_span = listing.find("span", class_="PropertyInformation_propertyType__u8e76")
    if type_span:
        property_type = type_span.text.strip()
        if property_type in ("Terraced", "End of Terrace", "Flat", "Apartment"):
            # Get address
            address_tag = listing.find("address")
            address = address_tag.text.strip() if address_tag else "N/A"

            # Get rent and extract integer using regex
            rent_tag = listing.find("div", class_="PropertyPrice_price__VL65t")
            rent_str = rent_tag.text.strip() if rent_tag else "N/A"

            rent_amount = None
            if rent_str != "N/A":
                match = re.search(r'£([\d,]+)', rent_str)
                if match:
                    rent_amount = int(match.group(1).replace(",", ""))
                    rents.append(rent_amount)

            print(f"Type: {property_type}")
            print(f"Address: {address}")
            print(f"Rent: {rent_str}")
            print("-" * 40)

# Summary
print(f"\nTotal properties found in {area}: {len(rents)}")

# Calculate and display average rent
if rents:
    average_rent = sum(rents) / len(rents)
    print(f"\nAverage rent for the selected properties: £{average_rent:.2f} pcm")
else:
    print("\nNo rent data found to calculate average.")