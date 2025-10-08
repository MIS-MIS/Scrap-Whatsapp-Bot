from playwright.sync_api import sync_playwright
from dataclasses import dataclass, asdict, field
import pandas as pd
import argparse
import os
import sys
import json
import time
import random
from pathlib import Path

@dataclass
class Business:
    """holds business data"""

    name: str = None
    address: str = None
    website: str = None
    phone_number: str = None
    reviews_count: int = None
    reviews_average: float = None
    search_query: str = None
    
    def get_unique_id(self):
        """Generate a unique identifier for the business"""
        return f"{self.name}_{self.address}_{self.phone_number}".replace(" ", "_").lower()
    
    def format_indian_phone(self, phone):
        """Format phone number in Indian format without spaces"""
        if not phone:
            return ""
        
        # Convert scientific notation to regular number
        try:
            if 'E+' in str(phone) or 'e+' in str(phone):
                phone = f"{float(phone):.0f}"
        except:
            pass
        
        # Remove all non-digit characters
        digits = ''.join(filter(str.isdigit, str(phone)))
        
        # Handle different Indian phone number formats
        if len(digits) == 10:
            # Mobile: 9876543210 -> +919876543210
            return f"+91{digits}"
        elif len(digits) == 11 and digits.startswith('0'):
            # Landline with 0: 01123456789 -> +91123456789
            return f"+91{digits[1:]}"
        elif len(digits) == 12 and digits.startswith('91'):
            # Already has country code: 919876543210 -> +919876543210
            return f"+{digits}"
        else:
            # Return digits only if format is unclear
            return digits if digits else str(phone)


@dataclass
class BusinessList:
    """holds list of Business objects,
    and save to centralized csv file
    """
    business_list: list[Business] = field(default_factory=list)
    save_at = 'output'
    centralized_csv = 'output/all_contacts.csv'

    def dataframe(self):
        """transform business_list to pandas dataframe

        Returns: pandas dataframe
        """
        return pd.json_normalize(
            (asdict(business) for business in self.business_list), sep="_"
        )

    def append_to_centralized_csv(self):
        """Append new data to centralized CSV file without overwriting"""
        
        if not os.path.exists(self.save_at):
            os.makedirs(self.save_at)
        
        if len(self.business_list) == 0:
            print("No new data to save.")
            return
            
        new_df = self.dataframe()
        
        # Check if centralized CSV exists
        if os.path.exists(self.centralized_csv):
            # Read existing data
            try:
                existing_df = pd.read_csv(self.centralized_csv)
                # Append new data
                combined_df = pd.concat([existing_df, new_df], ignore_index=True)
                print(f"Appending {len(new_df)} new contacts to existing {len(existing_df)} contacts")
            except:
                # If file is corrupted or empty, start fresh
                combined_df = new_df
                print(f"Creating new centralized CSV with {len(new_df)} contacts")
        else:
            # Create new file
            combined_df = new_df
            print(f"Creating new centralized CSV with {len(new_df)} contacts")
        
        # Save combined data
        combined_df.to_csv(self.centralized_csv, index=False)
        print(f"✅ Saved to: {self.centralized_csv}")
        print(f"📊 Total contacts in database: {len(combined_df)}")
        
    def save_to_excel(self, filename):
        """saves pandas dataframe to excel (xlsx) file (legacy method)"""
        if not os.path.exists(self.save_at):
            os.makedirs(self.save_at)
        self.dataframe().to_excel(f"output/{filename}.xlsx", index=False)

    def save_to_csv(self, filename):
        """saves pandas dataframe to csv file (legacy method)"""
        if not os.path.exists(self.save_at):
            os.makedirs(self.save_at)
        self.dataframe().to_csv(f"output/{filename}.csv", index=False)

# Removed coordinate extraction - not needed for this use case

class ContactManager:
    """Manages fetched contacts and prevents duplicates"""
    
    def __init__(self, cache_file="fetched_contacts.json", search_progress_file="search_progress.json"):
        self.cache_file = cache_file
        self.search_progress_file = search_progress_file
        self.fetched_contacts = self.load_cache()
        self.search_progress = self.load_search_progress()
    
    def load_cache(self):
        """Load previously fetched contacts from cache file"""
        if os.path.exists(self.cache_file):
            try:
                with open(self.cache_file, 'r') as f:
                    return set(json.load(f))
            except:
                return set()
        return set()
    
    def load_search_progress(self):
        """Load search progress from file"""
        if os.path.exists(self.search_progress_file):
            try:
                with open(self.search_progress_file, 'r') as f:
                    return json.load(f)
            except:
                return {}
        return {}
    
    def save_cache(self):
        """Save fetched contacts to cache file"""
        with open(self.cache_file, 'w') as f:
            json.dump(list(self.fetched_contacts), f)
    
    def save_search_progress(self):
        """Save search progress to file"""
        with open(self.search_progress_file, 'w') as f:
            json.dump(self.search_progress, f)
    
    def is_already_fetched(self, business_id):
        """Check if business was already fetched"""
        return business_id in self.fetched_contacts
    
    def mark_as_fetched(self, business_id):
        """Mark business as fetched"""
        self.fetched_contacts.add(business_id)
    
    def get_last_position(self, search_query):
        """Get the last scroll position for a search query"""
        return self.search_progress.get(search_query, 0)
    
    def update_search_position(self, search_query, position):
        """Update the last successful position for a search query"""
        self.search_progress[search_query] = position
    
    def get_stats(self):
        """Get statistics about fetched contacts"""
        return len(self.fetched_contacts)

def add_random_delay(min_delay=2, max_delay=5):
    """Add random delay to avoid being detected as bot"""
    delay = random.uniform(min_delay, max_delay)
    time.sleep(delay)

def fix_character_encoding(text):
    """Fix common character encoding issues"""
    if not text:
        return text
    
    # Common encoding fixes for accented characters
    encoding_fixes = {
        'Ã©': 'é',  # é -> é
        'Ã¨': 'è',  # è -> è
        'Ã¡': 'á',  # á -> á
        'Ã ': 'à',  # à -> à
        'Ã³': 'ó',  # ó -> ó
        'Ã²': 'ò',  # ò -> ò
        'Ã­': 'í',  # í -> í
        'Ã¬': 'ì',  # ì -> ì
        'Ãº': 'ú',  # ú -> ú
        'Ã¹': 'ù',  # ù -> ù
        'Ã§': 'ç',  # ç -> ç
        'Ã±': 'ñ',  # ñ -> ñ
        'Ã¼': 'ü',  # ü -> ü
        'Ã¶': 'ö',  # ö -> ö
        'Ã¤': 'ä',  # ä -> ä
        'Ã‰': 'É',  # É -> É
        'Ã‡': 'Ç',  # Ç -> Ç
    }
    
    fixed_text = text
    for wrong, correct in encoding_fixes.items():
        fixed_text = fixed_text.replace(wrong, correct)
    
    return fixed_text

def is_valid_business_name(name):
    """Validate if extracted text is a proper business name"""
    if not name or len(name.strip()) < 2:
        return False
    
    name = name.strip()
    
    # Fix character encoding issues
    name = fix_character_encoding(name)
    
    # Filter out names that are too long (likely contain descriptions)
    if len(name) > 80:  # Most business names are under 80 characters
        return False
    
    # Filter out common invalid patterns
    invalid_patterns = [
        "directions",
        "website",
        "call",
        "save",
        "share",
        "overview",
        "reviews",
        "photos",
        "menu",
        "hours",
        "suggest an edit",
        "claim this business",
        "add a photo",
        "write a review",
        "google maps",
        "loading",
        "error",
        "not found",
        "unavailable",
        "premium serviced offices",
        "meeting rooms",
        "virtual",
        "co-working spaces",
        "best college",
        "top rated",
        "book now",
        "order online"
    ]
    
    # Check if name contains promotional/descriptive patterns
    name_lower = name.lower()
    for pattern in invalid_patterns:
        if pattern in name_lower:
            return False
    
    # Filter out names with pipe symbols (often used for descriptions)
    if "|" in name or "⁠" in name:
        # Try to extract just the business name before the pipe
        clean_name = name.split("|")[0].strip()
        if len(clean_name) > 3 and len(clean_name) < 80:
            return clean_name  # Return cleaned name
        return False
    
    # Filter out names that are just numbers or symbols
    if name.replace(" ", "").replace("-", "").replace(".", "").isdigit():
        return False
    
    # Filter out very short names (likely not business names)
    if len(name) < 3:
        return False
    
    # Filter out names with too many special characters
    special_char_count = sum(1 for char in name if not char.isalnum() and char not in " -.,&'()[]")
    if special_char_count > len(name) * 0.3:  # More than 30% special characters
        return False
    
    # Filter out names with excessive punctuation or promotional text
    if name.count(",") > 3 or name.count("|") > 0 or "⁠" in name:
        return False
    
    return True

def main():
    
    ########
    # input 
    ########
    
    # read search from arguments
    parser = argparse.ArgumentParser()
    parser.add_argument("-s", "--search", type=str, help="Search query for Google Maps")
    parser.add_argument("-l", "--limit", type=int, default=100, help="Number of contacts to fetch (default: 100)")
    parser.add_argument("--skip-duplicates", action="store_true", help="Skip already fetched contacts")
    parser.add_argument("--clear-cache", action="store_true", help="Clear the cache of fetched contacts")
    parser.add_argument("--clear-progress", action="store_true", help="Clear search progress (start from beginning)")
    parser.add_argument("--min-delay", type=float, default=2.0, help="Minimum delay between requests (default: 2.0)")
    parser.add_argument("--max-delay", type=float, default=5.0, help="Maximum delay between requests (default: 5.0)")
    args = parser.parse_args()
    
    # Initialize contact manager
    contact_manager = ContactManager()
    
    # Ensure cache files exist
    if not os.path.exists(contact_manager.cache_file):
        contact_manager.save_cache()
        print(f"Created cache file: {contact_manager.cache_file}")
    
    if not os.path.exists(contact_manager.search_progress_file):
        contact_manager.save_search_progress()
        print(f"Created progress file: {contact_manager.search_progress_file}")
    
    # Clear cache if requested
    if args.clear_cache:
        if os.path.exists(contact_manager.cache_file):
            os.remove(contact_manager.cache_file)
            contact_manager.fetched_contacts = set()
        contact_manager.save_cache()
        print("Cache cleared!")
    
    # Clear search progress if requested
    if args.clear_progress:
        if os.path.exists(contact_manager.search_progress_file):
            os.remove(contact_manager.search_progress_file)
            contact_manager.search_progress = {}
        print("Search progress cleared! Will start from beginning for all searches.")
    
    # Set limit
    limit = args.limit
    print(f"Fetching limit set to: {limit} contacts")
    print(f"Previously fetched contacts: {contact_manager.get_stats()}")
    
    if args.search:
        search_list = [args.search]

    if not args.search:
        search_list = []
        # read search from input.txt file
        input_file_name = 'input.txt'
        # Get the absolute path of the file in the current working directory
        input_file_path = os.path.join(os.getcwd(), input_file_name)
        # Check if the file exists
        if os.path.exists(input_file_path):
        # Open the file in read mode
            with open(input_file_path, 'r') as file:
            # Read all lines into a list
                search_list = file.readlines()
                
        if len(search_list) == 0:
            print('Error occured: You must either pass the -s search argument, or add searches to input.txt')
            sys.exit()
        
    ###########
    # scraping
    ###########
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        page = browser.new_page()

        page.goto("https://www.google.com/maps", timeout=60000)
        # wait is added for dev phase. can remove it in production
        page.wait_for_timeout(5000)
        
        total_new_contacts = 0  # Track new contacts across all searches
        
        for search_for_index, search_for in enumerate(search_list):
            search_query = search_for.strip()
            print(f"-----\n{search_for_index} - {search_query}")
            
            # Check if we have previous progress for this search
            last_position = contact_manager.get_last_position(search_query)
            if last_position > 0:
                print(f"Resuming from position {last_position} (skipping first {last_position} results)")
            
            page.locator('//input[@id="searchboxinput"]').fill(search_query)
            add_random_delay(args.min_delay, args.max_delay)

            page.keyboard.press("Enter")
            add_random_delay(args.min_delay, args.max_delay)

            # scrolling
            page.hover('//a[contains(@href, "https://www.google.com/maps/place")]')

            # this variable is used to detect if the bot
            # scraped the same number of listings in the previous iteration
            previously_counted = 0
            remaining_limit = limit - total_new_contacts
            
            if remaining_limit <= 0:
                print(f"Reached overall limit of {limit} contacts. Stopping.")
                break
                
            print(f"Remaining contacts to fetch: {remaining_limit}")
            
            # Smart collection: only collect what we need, checking for duplicates in real-time
            collected_listings = []
            checked_names = set()  # Quick check for obvious duplicates during collection
            total_seen = 0  # Track total listings encountered
            duplicates_skipped_during_collection = 0
            max_attempts = remaining_limit * 3  # Maximum listings to examine (3x the target)
            consecutive_duplicates = 0  # Track consecutive duplicates found
            
            # Skip to last known position if resuming
            current_position = last_position
            
            while len(collected_listings) < remaining_limit and total_seen < max_attempts:
                page.mouse.wheel(0, 10000)
                add_random_delay(1, 3)  # Shorter delay for scrolling

                current_listings = page.locator(
                    '//a[contains(@href, "https://www.google.com/maps/place")]'
                ).all()
                
                # Check new listings for potential duplicates
                for listing in current_listings[current_position:]:
                    current_position += 1
                    total_seen += 1
                    
                    # Safety check: stop if we've examined too many listings
                    if total_seen >= max_attempts:
                        print(f"\nReached maximum attempts ({max_attempts}). Stopping collection.")
                        break
                    
                    if len(collected_listings) >= remaining_limit:
                        break
                        
                    # Quick duplicate check using business name from aria-label
                    try:
                        business_name = listing.get_attribute('aria-label')
                        if business_name:
                            # Create a simple ID for quick duplicate detection
                            simple_id = business_name.lower().strip().replace(" ", "_")
                            
                            # Check against both current session and cached data
                            if simple_id not in checked_names:
                                # If skip-duplicates is enabled, also check cache
                                if args.skip_duplicates:
                                    # Quick check if this might be a duplicate from cache
                                    is_likely_duplicate = any(simple_id in cached_id for cached_id in contact_manager.fetched_contacts)
                                    if is_likely_duplicate:
                                        print(f"Skipping cached duplicate: {business_name[:50]}...")
                                        duplicates_skipped_during_collection += 1
                                        consecutive_duplicates += 1
                                        
                                        # If we've found too many consecutive duplicates, consider stopping
                                        if consecutive_duplicates >= 20:
                                            print(f"\nFound {consecutive_duplicates} consecutive duplicates. Area might be fully scraped.")
                                            print("Consider trying a different search term or location.")
                                        continue
                                
                                checked_names.add(simple_id)
                                collected_listings.append(listing.locator("xpath=.."))
                                consecutive_duplicates = 0  # Reset counter when we find a new listing
                                efficiency = (len(collected_listings) / total_seen) * 100 if total_seen > 0 else 0
                                print(f"Collected: {len(collected_listings)}/{remaining_limit} (Efficiency: {efficiency:.1f}%) - {business_name[:50]}...")
                            else:
                                duplicates_skipped_during_collection += 1
                                consecutive_duplicates += 1
                    except:
                        # If we can't get the name, still collect it but with caution
                        if len(collected_listings) < remaining_limit:
                            collected_listings.append(listing.locator("xpath=.."))
                
                # Check if we've reached all available listings
                if len(current_listings) == previously_counted:
                    print(f"Arrived at all available listings. Collected: {len(collected_listings)}")
                    break
                else:
                    previously_counted = len(current_listings)
            
            listings = collected_listings
            collection_efficiency = (len(listings) / total_seen) * 100 if total_seen > 0 else 0
            print(f"\n=== COLLECTION SUMMARY ===")
            print(f"Total listings seen: {total_seen}")
            print(f"Duplicates skipped during collection: {duplicates_skipped_during_collection}")
            print(f"Unique listings collected: {len(listings)}")
            print(f"Collection efficiency: {collection_efficiency:.1f}%")
            
            # Handle the "all duplicates" scenario
            if len(listings) == 0:
                print(f"⚠️  WARNING: No new contacts found!")
                print(f"   - All {total_seen} listings examined were duplicates")
                print(f"   - This area might be fully scraped already")
                print(f"   - Try a different search term or location")
                print(f"   - Or use --clear-cache to start fresh")
                continue  # Skip to next search term
            elif len(listings) < remaining_limit * 0.1:  # Less than 10% of target
                print(f"⚠️  LOW YIELD: Only found {len(listings)} new contacts out of {remaining_limit} requested")
                print(f"   - Consider expanding search area or trying different keywords")
            
            print(f"Now processing {len(listings)} listings for detailed data...")

            business_list = BusinessList()
            new_contacts_this_search = 0
            skipped_duplicates = 0
            skipped_no_phone = 0

            # scraping
            for listing_index, listing in enumerate(listings):
                try:
                    listing.click()
                    add_random_delay(args.min_delay, args.max_delay)

                    # Multiple selectors for better data extraction
                    name_selectors = [
                        '//h1[contains(@class, "DUwDvf")]',
                        '//h1[@data-attrid="title"]',
                        '//div[contains(@class, "lMbq3e")]//div[contains(@class, "fontHeadlineSmall")]',
                        '//div[contains(@class, "x3AX1-LfntMc-header-title")]//span',
                        '//h1[contains(@class, "fontHeadlineLarge")]',
                        '//div[@role="main"]//h1',
                        '//div[contains(@class, "SPZz6b")]//h1'
                    ]
                    
                    address_xpath = '//button[@data-item-id="address"]//div[contains(@class, "fontBodyMedium")]'
                    website_xpath = '//a[@data-item-id="authority"]//div[contains(@class, "fontBodyMedium")]'
                    phone_number_xpath = '//button[contains(@data-item-id, "phone:tel:")]//div[contains(@class, "fontBodyMedium")]'
                    review_count_xpath = '//button[@jsaction="pane.reviewChart.moreReviews"]//span'
                    reviews_average_xpath = '//div[@jsaction="pane.reviewChart.moreReviews"]//div[@role="img"]'
                    
                    # Alternative selectors if primary ones fail
                    alt_review_count_xpath = '//div[contains(@class, "F7nice")]//span[contains(@aria-label, "reviews")]'
                    
                    
                    business = Business()
                    
                    # Set the search query for tracking
                    business.search_query = search_query
                   
                    # Extract business name with multiple fallback options and validation
                    business.name = None
                    
                    # Try each name selector until we find a valid name
                    for selector in name_selectors:
                        try:
                            if page.locator(selector).count() > 0:
                                extracted_name = page.locator(selector).first.inner_text().strip()
                                
                                # Validate the extracted name
                                validation_result = is_valid_business_name(extracted_name)
                                if validation_result:
                                    # If validation returns a cleaned name, use it
                                    if isinstance(validation_result, str):
                                        business.name = fix_character_encoding(validation_result)
                                    else:
                                        business.name = fix_character_encoding(extracted_name)
                                    break
                        except:
                            continue
                    
                    # If no valid name found from page selectors, try aria-label
                    if not business.name:
                        try:
                            aria_label = listing.get_attribute('aria-label')
                            if aria_label:
                                validation_result = is_valid_business_name(aria_label)
                                if validation_result:
                                    # If validation returns a cleaned name, use it
                                    if isinstance(validation_result, str):
                                        business.name = fix_character_encoding(validation_result)
                                    else:
                                        business.name = fix_character_encoding(aria_label)
                        except:
                            pass
                    
                    # Final fallback
                    if not business.name:
                        business.name = "Name not found"
                        print(f"⚠️ Could not extract valid name for listing {listing_index + 1}")
                    
                    # Extract address
                    try:
                        if page.locator(address_xpath).count() > 0:
                            business.address = page.locator(address_xpath).first.inner_text().strip()
                        else:
                            business.address = ""
                    except:
                        business.address = ""
                    
                    # Extract website
                    try:
                        if page.locator(website_xpath).count() > 0:
                            business.website = page.locator(website_xpath).first.inner_text().strip()
                        else:
                            business.website = ""
                    except:
                        business.website = ""
                    
                    # Extract and format phone number
                    try:
                        if page.locator(phone_number_xpath).count() > 0:
                            raw_phone = page.locator(phone_number_xpath).first.inner_text().strip()
                            business.phone_number = business.format_indian_phone(raw_phone)
                        else:
                            business.phone_number = ""
                    except:
                        business.phone_number = ""
                    
                    # Extract review count
                    try:
                        if page.locator(review_count_xpath).count() > 0:
                            review_text = page.locator(review_count_xpath).first.inner_text().strip()
                            # Extract number from text like "1,234 reviews"
                            review_number = ''.join(filter(str.isdigit, review_text.split()[0]))
                            business.reviews_count = int(review_number) if review_number else 0
                        elif page.locator(alt_review_count_xpath).count() > 0:
                            review_text = page.locator(alt_review_count_xpath).first.inner_text().strip()
                            review_number = ''.join(filter(str.isdigit, review_text))
                            business.reviews_count = int(review_number) if review_number else 0
                        else:
                            business.reviews_count = 0
                    except:
                        business.reviews_count = 0
                        
                    # Extract review average
                    try:
                        if page.locator(reviews_average_xpath).count() > 0:
                            aria_label = page.locator(reviews_average_xpath).first.get_attribute('aria-label')
                            if aria_label:
                                # Extract rating from aria-label like "4.5 stars"
                                rating_text = aria_label.split()[0]
                                business.reviews_average = float(rating_text.replace(',', '.'))
                            else:
                                business.reviews_average = 0.0
                        else:
                            business.reviews_average = 0.0
                    except:
                        business.reviews_average = 0.0

                    # Skip businesses without phone numbers
                    if not business.phone_number or business.phone_number.strip() == "":
                        print(f"Skipping {business.name} - No phone number available")
                        skipped_no_phone += 1
                        continue
                    
                    # Check for duplicates
                    business_id = business.get_unique_id()
                    
                    if args.skip_duplicates and contact_manager.is_already_fetched(business_id):
                        print(f"Skipping duplicate: {business.name}")
                        skipped_duplicates += 1
                        continue
                    
                    # Mark as fetched and add to list
                    contact_manager.mark_as_fetched(business_id)
                    business_list.business_list.append(business)
                    new_contacts_this_search += 1
                    total_new_contacts += 1
                    
                    print(f"Processed {listing_index + 1}/{len(listings)}: {business.name} - {business.phone_number}")
                    
                    # Check if we've reached our limit
                    if total_new_contacts >= limit:
                        print(f"Reached limit of {limit} contacts. Stopping.")
                        break
                        
                except Exception as e:
                    print(f'Error occurred while processing listing {listing_index + 1}: {e}')
                    add_random_delay(1, 2)  # Brief delay on error
                    # Continue to next listing instead of stopping
            
            #########
            # output
            #########
            print(f"\nSearch '{search_query}' completed:")
            print(f"  - Listings examined: {total_seen}")
            print(f"  - Duplicates skipped during collection: {duplicates_skipped_during_collection}")
            print(f"  - Duplicates skipped during processing: {skipped_duplicates}")
            print(f"  - Skipped (no phone number): {skipped_no_phone}")
            print(f"  - New contacts found: {new_contacts_this_search}")
            print(f"  - Collection efficiency: {collection_efficiency:.1f}%")
            print(f"  - Total new contacts so far: {total_new_contacts}")
            
            # Save to centralized CSV file
            if len(business_list.business_list) > 0:
                business_list.append_to_centralized_csv()
            else:
                print("No new contacts to save for this search.")
            
            # Save cache and progress after each search
            contact_manager.save_cache()
            contact_manager.update_search_position(search_query, current_position)
            contact_manager.save_search_progress()
            
            # Check if we've reached our limit
            if total_new_contacts >= limit:
                print(f"\nReached overall limit of {limit} contacts. Stopping all searches.")
                break

        print(f"\n=== FINAL SUMMARY ===")
        print(f"Total new contacts fetched: {total_new_contacts}")
        print(f"Total contacts in cache: {contact_manager.get_stats()}")
        print(f"Cache file: {contact_manager.cache_file}")
        
        browser.close()


if __name__ == "__main__":
    main()
