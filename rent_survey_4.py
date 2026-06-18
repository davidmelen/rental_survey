import requests
from bs4 import BeautifulSoup
import re
from urllib.parse import urlparse, parse_qs, urlencode, urlunparse
import time
from datetime import datetime
import openpyxl
from openpyxl.styles import Font

# --- 1. User Input: Area ---
valid_areas = ["M27", "M28", "M30", "M5"]
area = ""

while True:
    user_input = input(f"Enter area code ({', '.join(valid_areas)}): ").strip().upper()
    if user_input in valid_areas:
        area = user_input
        break
    else:
        print(f"Invalid entry. Please choose from: {valid_areas}")

# --- 2. User Input: Property Type ---
selected_prop_type_param = ""
# We will use these to simply label the output, not to strictly delete data
display_type_label = "" 

while True:
    p_type = input("Enter property type (T for Terraced, F for Flat): ").strip().upper()
    if p_type == 'T':
        selected_prop_type_param = 'terraced'
        display_type_label = "Terraced / End of Terrace"
        break
    elif p_type == 'F':
        selected_prop_type_param = 'flat'
        display_type_label = "Flats / Apartments / Maisonettes"
        break
    else:
        print("Invalid entry. Please enter 'T' or 'F'.")

# --- 3. User Input: Bedrooms ---
def get_valid_int(prompt):
    while True:
        try:
            value = int(input(prompt))
            if value < 0:
                print("Please enter a positive number.")
            else:
                return str(value)
        except ValueError:
            print("Invalid input. Please enter a number.")

min_bedrooms = get_valid_int("Enter minimum bedrooms: ")
max_bedrooms = get_valid_int("Enter maximum bedrooms: ")

# --- 4. Select Base URL ---
if area == "M27":
    base_url = "https://www.rightmove.co.uk/property-to-rent/find.html?searchLocation=M27&useLocationIdentifier=true&locationIdentifier=OUTCODE%5E1582&rent=To+rent&radius=0.0&minBedrooms=2&maxBedrooms=2&_includeLetAgreed=on&includeLetAgreed=true&index=0&sortType=6&channel=RENT&transactionType=LETTING&displayLocationIdentifier=M27&propertyTypes=terraced&furnishTypes=unfurnished%2CpartFurnished"
elif area == "M28":
    base_url = "https://www.rightmove.co.uk/property-to-rent/find.html?searchLocation=M28&useLocationIdentifier=true&locationIdentifier=OUTCODE%5E1583&radius=0.0&minBedrooms=2&maxBedrooms=2&propertyTypes=terraced&_includeLetAgreed=on&includeLetAgreed=true&sortType=6&channel=RENT&transactionType=LETTING&displayLocationIdentifier=M28&furnishTypes=unfurnished%2CpartFurnished"
elif area == "M30":
    base_url = "https://www.rightmove.co.uk/property-to-rent/find.html?searchLocation=M30&useLocationIdentifier=true&locationIdentifier=OUTCODE%5E1586&rent=To+rent&radius=0.0&minBedrooms=2&maxBedrooms=2&propertyTypes=terraced&_includeLetAgreed=on&includeLetAgreed=true&furnishTypes=unfurnished%2CpartFurnished&index=0&sortType=6&channel=RENT&transactionType=LETTING&displayLocationIdentifier=M30"
elif area == "M5":
    base_url = "https://www.rightmove.co.uk/property-to-rent/find.html?searchLocation=M5&useLocationIdentifier=true&locationIdentifier=OUTCODE%5E1600&radius=0.0&minBedrooms=2&maxBedrooms=2&propertyTypes=flat&_includeLetAgreed=on&includeLetAgreed=true&furnishTypes=unfurnished%2CpartFurnished&sortType=6&channel=RENT&transactionType=LETTING&displayLocationIdentifier=M5&index=0&minBathrooms=1&maxBathrooms=1&dontShow=student%2Cretirement%2ChouseShare"
else:
    print("Area not supported.")
    exit()

# --- 5. Prepare URL Parameters ---
url_parts = list(urlparse(base_url))
query = parse_qs(url_parts[4])

query['minBedrooms'] = [min_bedrooms]
query['maxBedrooms'] = [max_bedrooms]
query['propertyTypes'] = [selected_prop_type_param] 

# Reorder params (Important for Rightmove stability)
if 'minBedrooms' in query: query['minBedrooms'] = query.pop('minBedrooms')
if 'maxBedrooms' in query: query['maxBedrooms'] = query.pop('maxBedrooms')
if 'propertyTypes' in query: query['propertyTypes'] = query.pop('propertyTypes')

print(f"\nStarting multi-page rental survey in {area}")
print(f"Property Type: {display_type_label}")
print(f"Bedrooms: {min_bedrooms} to {max_bedrooms}")
print("-" * 60)

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36"
}

survey_results = []
page_number = 0
previous_page_addresses = [] # Store ALL addresses from prev page to detect loop
current_url = ""

while True:
    current_index = page_number * 24
    query['index'] = [str(current_index)]
    
    url_parts[4] = urlencode(query, doseq=True)
    current_url = urlunparse(url_parts)
    
    print(f"Scraping Page {page_number + 1}...")

    try:
        response = requests.get(current_url, headers=headers)
        if response.status_code != 200:
            print(f"Failed to retrieve page. Status: {response.status_code}")
            break
            
        soup = BeautifulSoup(response.text, "html.parser")
        listings = soup.find_all("div", class_="propertyCard-details")

        if not listings:
            print("No more listings found.")
            break
            
        # --- FIX 1: Better Loop Detection ---
        # Instead of just checking the first address, we collect ALL addresses on this page
        # and compare them to the previous page.
        current_page_addresses = []
        for l in listings:
            a_tag = l.find("address")
            if a_tag:
                current_page_addresses.append(a_tag.text.strip())
        
        # If the lists are identical, THEN it's a loop.
        if current_page_addresses == previous_page_addresses and page_number > 0:
            print("Duplicate page detected (redirect loop). Finishing survey.")
            break
            
        previous_page_addresses = current_page_addresses
        # ------------------------------------
        
        items_on_page = 0
        for listing in listings:
            # We try to find the property type, but even if we can't perfectly identify it,
            # we should probably keep it if the URL filtered for it.
            type_span = listing.find("span", class_="PropertyInformation_propertyType__u8e76")
            property_type = type_span.text.strip() if type_span else "Unknown"
            
            # --- FIX 2: Removed Strict Filtering ---
            # We trust the URL search mostly, but we can do a sanity check.
            # If searching for Flats, we skip clear errors like "Detached House"
            # but allow "Maisonette", "Studio", "Penthouse" etc.
            skip_property = False
            
            if selected_prop_type_param == 'flat':
                if "House" in property_type or "Bungalow" in property_type:
                    skip_property = True
            elif selected_prop_type_param == 'terraced':
                if "Flat" in property_type or "Apartment" in property_type:
                    skip_property = True
                    
            if not skip_property:
                rent_tag = listing.find("div", class_="PropertyPrice_price__VL65t")
                rent_str = rent_tag.text.strip() if rent_tag else "N/A"
                
                address_tag = listing.find("address")
                address = address_tag.text.strip() if address_tag else "N/A"
                
                # Bedroom Extraction
                bedrooms = "N/A"
                bed_span = listing.find("span", class_="PropertyInformation_bedroomsCount___2b5R")
                
                if bed_span:
                    raw_bed_text = bed_span.text.strip()
                    if raw_bed_text:
                        bedrooms = raw_bed_text
                    
                    if bedrooms == "N/A" or not bedrooms:
                        aria_label = bed_span.get("aria-label", "")
                        if aria_label:
                            match = re.search(r'(\d+)', aria_label)
                            if match:
                                bedrooms = match.group(1)
                
                if bedrooms == "0" or "Studio" in property_type:
                        bedrooms = "Studio"

                if rent_str != "N/A":
                    match = re.search(r'£([\d,]+)', rent_str)
                    if match:
                        rent_amount = int(match.group(1).replace(",", ""))
                        
                        survey_results.append({
                            "address": address,
                            "type": property_type,
                            "bedrooms": bedrooms,
                            "rent_str": rent_str,
                            "rent_val": rent_amount
                        })
                        items_on_page += 1

        print(f"  -> Found {items_on_page} valid properties.")
        page_number += 1
        time.sleep(1)
        
    except Exception as e:
        print(f"An error occurred: {e}")
        break

# --- Summary ---
print("\n" + "=" * 60)
print(f"SURVEY RESULTS FOR {area} - {display_type_label.upper()}")
print("=" * 60)

print(f"{'Beds':<8} | {'Rent':<15} | {'Type':<20} | {'Address'}")
print("-" * 80)
for prop in survey_results:
    # Truncate type to fit column
    p_type_short = (prop['type'][:18] + '..') if len(prop['type']) > 18 else prop['type']
    print(f"{prop['bedrooms']:<8} | {prop['rent_str']:<15} | {p_type_short:<20} | {prop['address']}")

print("-" * 80)

rent_values = [item['rent_val'] for item in survey_results]

if rent_values:
    average_rent = sum(rent_values) / len(rent_values)
    print(f"Total Properties: {len(rent_values)}")
    print(f"AVERAGE RENT:   £{average_rent:.2f} pcm")
    print(f"Lowest Rent:    £{min(rent_values)}")
    print(f"Highest Rent:   £{max(rent_values)}")
else:
    print("No properties found matching criteria.")

print("=" * 60)
print("Use Ctrl + right click to view web page")

# --- Excel Export ---
if survey_results:
    save = input("\nSave results to Excel? (y/n): ").strip().lower()
    if save == 'y':
        beds_label = f"{min_bedrooms}bed" if min_bedrooms == max_bedrooms else f"{min_bedrooms}-{max_bedrooms}bed"
        timestamp = datetime.now().strftime("%Y%m%d%H%M")
        filename = f"exports/{timestamp}_{area}_{selected_prop_type_param}_{beds_label}_survey.xlsx"

        wb = openpyxl.Workbook()
        ws = wb.active
        ws.title = "Survey Results"

        headers = ["Address", "Type", "Bedrooms", "Rent (str)", "Rent (pcm)"]
        ws.append(headers)
        for cell in ws[1]:
            cell.font = Font(bold=True)

        for prop in survey_results:
            ws.append([prop["address"], prop["type"], prop["bedrooms"], prop["rent_str"], prop["rent_val"]])

        # Auto-size columns
        for col in ws.columns:
            max_len = max(len(str(cell.value)) for cell in col if cell.value)
            ws.column_dimensions[col[0].column_letter].width = max_len + 2

        wb.save(filename)
        print(f"Saved: {filename}")

# Clean URL for display
display_query = query.copy()
if 'index' in display_query: del display_query['index']
if 'sortType' in display_query: del display_query['sortType']
if 'channel' in display_query: del display_query['channel']
if 'transactionType' in display_query: del display_query['transactionType']

display_keys = ['searchLocation', 'locationIdentifier', 'useLocationIdentifier', 'minBedrooms', 'maxBedrooms', 'propertyTypes', 'furnishTypes']
final_display_query = {}

for k in display_keys:
    if k in display_query:
        final_display_query[k] = display_query[k]

url_parts[4] = urlencode(final_display_query, doseq=True)
clean_display_url = urlunparse(url_parts)

print(f"Source URL: {clean_display_url}")
print("=" * 60)