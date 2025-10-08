#!/usr/bin/env python3
"""
Interactive Google Maps Scraper
User-friendly menu interface for all scraper features
"""

import os
import sys
import json
import subprocess
from pathlib import Path
import time
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
from typing import List, Dict, Optional

@dataclass
class Schedule:
    """Individual schedule configuration"""
    id: str
    name: str
    search_terms: List[str]
    start_time: str
    duration_minutes: int
    limit_per_run: int
    skip_duplicates: bool
    is_recurring: bool
    is_active: bool
    last_run: str = ""
    total_runs: int = 0
    estimated_duration_minutes: int = 15
    auto_sequence: bool = False
    currently_running: bool = False

class InteractiveScraper:
    def __init__(self):
        self.default_limit = 100
        self.default_min_delay = 2.0
        self.default_max_delay = 5.0
        self.cache_file = "fetched_contacts.json"
        self.progress_file = "search_progress.json"
        self.output_file = "output/all_contacts.csv"
        
        # Scheduling system
        self.schedule_file = "schedule_config.json"
        self.multi_schedules_file = "multi_schedules.json"
        self.schedules: Dict[str, Schedule] = {}
        self.load_schedules()
    
    def clear_screen(self):
        """Clear the terminal screen"""
        os.system('cls' if os.name == 'nt' else 'clear')
    
    def print_header(self):
        """Print the main header"""
        print("=" * 55)
        print("    GOOGLE MAPS SCRAPER - INTERACTIVE MENU")
        print("=" * 55)
        print()
    
    def print_main_menu(self):
        """Print the main menu options"""
        print("📋 MAIN MENU:")
        print("=" * 20)
        print("1.  Quick Search (Default: 100 contacts)")
        print("2.  Custom Search (Set your parameters)")
        print("3.  Batch Search (Multiple searches)")
        print("4.  Scheduled Scraping (NEW!)")
        print("5.  Cache Management")
        print("6.  View Statistics & Files")
        print("7.  Troubleshooting Tools")
        print("8.  Settings & Configuration")
        print("9.  Help & Commands Reference")
        print("10. Exit")
        print()
    
    def get_user_input(self, prompt, default=None):
        """Get user input with optional default"""
        if default:
            user_input = input(f"{prompt} [{default}]: ").strip()
            return user_input if user_input else str(default)
        return input(f"{prompt}: ").strip()
    
    def run_scraper_command(self, command):
        """Execute the main scraper with given command"""
        try:
            print(f"\n🚀 Running: python main.py {command}")
            print("-" * 50)
            result = subprocess.run(f"python main.py {command}", shell=True, capture_output=False)
            print("-" * 50)
            input("\nPress Enter to continue...")
            return result.returncode == 0
        except Exception as e:
            print(f"❌ Error running command: {e}")
            input("Press Enter to continue...")
            return False
    
    def quick_search(self):
        """Quick search with default settings"""
        self.clear_screen()
        self.print_header()
        print("🚀 QUICK SEARCH")
        print("=" * 20)
        print("Default settings: 100 contacts, skip duplicates, 2-5s delays")
        print()
        
        search_term = self.get_user_input("Enter search term (e.g., 'business delhi')")
        if not search_term:
            print("❌ Search term is required!")
            input("Press Enter to continue...")
            return
        
        command = f'-s "{search_term}" --limit {self.default_limit} --skip-duplicates'
        self.run_scraper_command(command)
    
    def custom_search(self):
        """Custom search with user-defined parameters"""
        self.clear_screen()
        self.print_header()
        print("⚙️ CUSTOM SEARCH")
        print("=" * 20)
        
        search_term = self.get_user_input("Enter search term")
        if not search_term:
            print("❌ Search term is required!")
            input("Press Enter to continue...")
            return
        
        limit = self.get_user_input("Enter contact limit", self.default_limit)
        skip_duplicates = self.get_user_input("Skip duplicates? (y/n)", "y").lower() == 'y'
        min_delay = self.get_user_input("Minimum delay (seconds)", self.default_min_delay)
        max_delay = self.get_user_input("Maximum delay (seconds)", self.default_max_delay)
        
        command = f'-s "{search_term}" --limit {limit} --min-delay {min_delay} --max-delay {max_delay}'
        if skip_duplicates:
            command += " --skip-duplicates"
        
        self.run_scraper_command(command)
    
    def batch_search(self):
        """Multiple searches in sequence"""
        self.clear_screen()
        self.print_header()
        print("📦 BATCH SEARCH")
        print("=" * 20)
        print("Enter multiple search terms (one per line, empty line to finish):")
        print("Example: restaurants delhi")
        print("         hotels mumbai")
        print("         gyms bangalore")
        print()
        
        searches = []
        while True:
            search = input(f"Search {len(searches) + 1}: ").strip()
            if not search:
                break
            searches.append(search)
        
        if not searches:
            print("❌ No search terms entered!")
            input("Press Enter to continue...")
            return
        
        limit = self.get_user_input("Contacts per search", self.default_limit)
        skip_duplicates = self.get_user_input("Skip duplicates? (y/n)", "y").lower() == 'y'
        
        print(f"\n🚀 Running {len(searches)} searches...")
        for i, search in enumerate(searches, 1):
            print(f"\n--- Search {i}/{len(searches)}: {search} ---")
            command = f'-s "{search}" --limit {limit}'
            if skip_duplicates:
                command += " --skip-duplicates"
            
            success = self.run_scraper_command(command)
            if not success:
                retry = input("❌ Search failed. Continue with next? (y/n): ").lower() == 'y'
                if not retry:
                    break
    
    def cache_management(self):
        """Cache and progress management"""
        while True:
            self.clear_screen()
            self.print_header()
            print("🗂️ CACHE MANAGEMENT")
            print("=" * 20)
            print("1. Clear contact cache (reset duplicate tracking)")
            print("2. Clear search progress (start from beginning)")
            print("3. Reset everything (cache + progress)")
            print("4. View cache status")
            print("5. Back to main menu")
            print()
            
            choice = self.get_user_input("Select option (1-5)")
            
            if choice == "1":
                confirm = self.get_user_input("Clear contact cache? (y/n)", "n").lower() == 'y'
                if confirm:
                    self.run_scraper_command("--clear-cache -s 'dummy' --limit 1")
            elif choice == "2":
                confirm = self.get_user_input("Clear search progress? (y/n)", "n").lower() == 'y'
                if confirm:
                    self.run_scraper_command("--clear-progress -s 'dummy' --limit 1")
            elif choice == "3":
                confirm = self.get_user_input("Reset everything? (y/n)", "n").lower() == 'y'
                if confirm:
                    self.run_scraper_command("--clear-cache --clear-progress -s 'dummy' --limit 1")
            elif choice == "4":
                self.view_cache_status()
            elif choice == "5":
                break
    
    def view_cache_status(self):
        """Display cache and file status"""
        print("\n📊 CACHE STATUS:")
        print("-" * 20)
        
        # Check cache file
        if os.path.exists(self.cache_file):
            try:
                with open(self.cache_file, 'r') as f:
                    cache_data = json.load(f)
                print(f"✅ Contact cache: {len(cache_data)} contacts tracked")
            except:
                print("❌ Contact cache: File corrupted")
        else:
            print("❌ Contact cache: Not found")
        
        # Check progress file
        if os.path.exists(self.progress_file):
            try:
                with open(self.progress_file, 'r') as f:
                    progress_data = json.load(f)
                print(f"✅ Search progress: {len(progress_data)} searches tracked")
                for search, position in progress_data.items():
                    print(f"   - '{search}': position {position}")
            except:
                print("❌ Search progress: File corrupted")
        else:
            print("❌ Search progress: Not found")
        
        # Check output file
        if os.path.exists(self.output_file):
            try:
                import pandas as pd
                df = pd.read_csv(self.output_file)
                print(f"✅ Output database: {len(df)} total contacts")
                if 'search_query' in df.columns:
                    searches = df['search_query'].value_counts()
                    print("   Search breakdown:")
                    for search, count in searches.head(5).items():
                        print(f"   - '{search}': {count} contacts")
            except:
                print("❌ Output database: File corrupted or empty")
        else:
            print("❌ Output database: Not found")
        
        input("\nPress Enter to continue...")
    
    def view_statistics(self):
        """Display comprehensive statistics"""
        self.clear_screen()
        self.print_header()
        print("📊 STATISTICS & FILES")
        print("=" * 20)
        self.view_cache_status()
        
        print("\n📁 FILE LOCATIONS:")
        print("-" * 20)
        print(f"Main script: main.py")
        print(f"Contact cache: {self.cache_file}")
        print(f"Search progress: {self.progress_file}")
        print(f"Output database: {self.output_file}")
        print(f"Commands reference: scraper_commands.txt")
        
        input("\nPress Enter to continue...")
    
    def troubleshooting_tools(self):
        """Troubleshooting and testing tools"""
        while True:
            self.clear_screen()
            self.print_header()
            print("🔧 TROUBLESHOOTING TOOLS")
            print("=" * 20)
            print("1. Test mode (5 contacts only)")
            print("2. Stealth mode (long delays)")
            print("3. Reset stuck search")
            print("4. Check system requirements")
            print("5. Back to main menu")
            print()
            
            choice = self.get_user_input("Select option (1-5)")
            
            if choice == "1":
                search_term = self.get_user_input("Enter test search term", "test business delhi")
                command = f'-s "{search_term}" --limit 5 --skip-duplicates'
                self.run_scraper_command(command)
            elif choice == "2":
                search_term = self.get_user_input("Enter search term")
                limit = self.get_user_input("Enter limit", "25")
                command = f'-s "{search_term}" --limit {limit} --skip-duplicates --min-delay 8 --max-delay 15'
                print("🐌 Using stealth mode with 8-15 second delays...")
                self.run_scraper_command(command)
            elif choice == "3":
                search_term = self.get_user_input("Enter stuck search term")
                confirm = self.get_user_input("Reset progress for this search? (y/n)", "y").lower() == 'y'
                if confirm:
                    self.run_scraper_command("--clear-progress -s 'dummy' --limit 1")
                    print(f"✅ Progress reset. You can now restart '{search_term}'")
                    input("Press Enter to continue...")
            elif choice == "4":
                self.check_system()
            elif choice == "5":
                break
    
    def check_system(self):
        """Check system requirements and files"""
        print("\n🔍 SYSTEM CHECK:")
        print("-" * 20)
        
        # Check main script
        if os.path.exists("main.py"):
            print("✅ main.py found")
        else:
            print("❌ main.py not found!")
        
        # Check required modules
        try:
            import playwright
            print("✅ Playwright installed")
        except ImportError:
            print("❌ Playwright not installed")
        
        try:
            import pandas
            print("✅ Pandas installed")
        except ImportError:
            print("❌ Pandas not installed")
        
        # Check output directory
        if os.path.exists("output"):
            print("✅ Output directory exists")
        else:
            print("⚠️ Output directory will be created")
        
        input("\nPress Enter to continue...")
    
    def settings_configuration(self):
        """Settings and configuration management"""
        while True:
            self.clear_screen()
            self.print_header()
            print("⚙️ SETTINGS & CONFIGURATION")
            print("=" * 20)
            print(f"Current defaults:")
            print(f"  - Contact limit: {self.default_limit}")
            print(f"  - Min delay: {self.default_min_delay}s")
            print(f"  - Max delay: {self.default_max_delay}s")
            print()
            print("1. Change default contact limit")
            print("2. Change default delays")
            print("3. Reset to factory defaults")
            print("4. Back to main menu")
            print()
            
            choice = self.get_user_input("Select option (1-4)")
            
            if choice == "1":
                new_limit = self.get_user_input("Enter new default limit", self.default_limit)
                try:
                    self.default_limit = int(new_limit)
                    print(f"✅ Default limit set to {self.default_limit}")
                except:
                    print("❌ Invalid number")
                input("Press Enter to continue...")
            elif choice == "2":
                new_min = self.get_user_input("Enter new min delay", self.default_min_delay)
                new_max = self.get_user_input("Enter new max delay", self.default_max_delay)
                try:
                    self.default_min_delay = float(new_min)
                    self.default_max_delay = float(new_max)
                    print(f"✅ Delays set to {self.default_min_delay}-{self.default_max_delay}s")
                except:
                    print("❌ Invalid numbers")
                input("Press Enter to continue...")
            elif choice == "3":
                self.default_limit = 100
                self.default_min_delay = 2.0
                self.default_max_delay = 5.0
                print("✅ Reset to factory defaults")
                input("Press Enter to continue...")
            elif choice == "4":
                break
    
    def show_help(self):
        """Show help and command reference"""
        self.clear_screen()
        self.print_header()
        print("📖 HELP & COMMANDS REFERENCE")
        print("=" * 20)
        
        if os.path.exists("scraper_commands.txt"):
            print("📋 Full command reference available in 'scraper_commands.txt'")
            print()
            show_file = self.get_user_input("Display command file? (y/n)", "y").lower() == 'y'
            if show_file:
                try:
                    with open("scraper_commands.txt", "r", encoding='utf-8') as f:
                        content = f.read()
                    print("\n" + "="*60)
                    # Display content in chunks to avoid overwhelming the screen
                    lines = content.split('\n')
                    for i, line in enumerate(lines):
                        print(line)
                        # Pause every 30 lines for readability
                        if (i + 1) % 30 == 0:
                            input("\nPress Enter to continue reading...")
                    print("="*60)
                except Exception as e:
                    print(f"❌ Error reading command file: {e}")
                    print("\nShowing built-in help instead...")
                    self.show_built_in_help()
        else:
            print("❌ scraper_commands.txt not found")
            self.show_built_in_help()
    
    def show_built_in_help(self):
        """Display built-in help when file is not available"""
        print("\n📋 BUILT-IN QUICK REFERENCE:")
        print("=" * 40)
        print("\n🚀 BASIC USAGE:")
        print("1. Quick Search - Default 100 contacts with duplicate skipping")
        print("2. Custom Search - Set your own limits and delays")
        print("3. Batch Search - Multiple searches in sequence")
        print("4. Cache Management - Clear duplicates and progress")
        print("5. Statistics - View your scraping progress")
        
        print("\n⚙️ COMMON PARAMETERS:")
        print("- Search terms: 'business delhi', 'restaurants mumbai'")
        print("- Limits: 10-1000 contacts")
        print("- Delays: 2-15 seconds (longer = more stealthy)")
        print("- Skip duplicates: Always recommended")
        
        print("\n🔧 TROUBLESHOOTING:")
        print("- Use Test Mode for 5 contacts only")
        print("- Use Stealth Mode if getting blocked")
        print("- Clear cache if too many duplicates")
        print("- Reset progress if search gets stuck")
        
        print("\n📁 OUTPUT:")
        print("- All data saved to: output/all_contacts.csv")
        print("- Includes: name, address, website, phone, reviews")
        print("- Phone format: +919876543210 (Indian format)")
        print("- Search tracking: Shows which term found each contact")
        
        input("\nPress Enter to continue...")
    
    def scheduled_scraping(self):
        """Integrated scheduling system - no external files needed"""
        while True:
            self.clear_screen()
            self.print_header()
            print("🕐 SCHEDULED SCRAPING - ALL-IN-ONE")
            print("=" * 40)
            print("1.  Quick Schedule (Run once at specific time)")
            print("2.  Recurring Schedule (Run at intervals)")
            print("3.  View All Schedules")
            print("4.  Start Scheduled Scraping")
            print("5.  Manual Run (Test immediately)")
            print("6.  Schedule Management")
            print("7.  Conflict Checker")
            print("8.  Schedule Help & Examples")
            print("9.  Back to Main Menu")
            print()
            
            choice = self.get_user_input("Select option (1-9)")
            
            if choice == "1":
                self.quick_schedule_setup()
            elif choice == "2":
                self.recurring_schedule_setup()
            elif choice == "3":
                self.view_all_schedules()
            elif choice == "4":
                self.start_scheduler()
            elif choice == "5":
                self.manual_schedule_run()
            elif choice == "6":
                self.schedule_management()
            elif choice == "7":
                self.conflict_checker()
            elif choice == "8":
                self.schedule_help()
            elif choice == "9":
                break
            else:
                print("❌ Invalid choice. Please select 1-9.")
                input("Press Enter to continue...")
    
    # ========== SCHEDULING SYSTEM METHODS ==========
    
    def load_schedules(self):
        """Load all schedules from file"""
        if os.path.exists(self.multi_schedules_file):
            try:
                with open(self.multi_schedules_file, 'r') as f:
                    data = json.load(f)
                
                self.schedules = {}
                for schedule_data in data:
                    schedule = Schedule(**schedule_data)
                    self.schedules[schedule.id] = schedule
            except Exception as e:
                print(f"Error loading schedules: {e}")
                self.schedules = {}
    
    def save_schedules(self):
        """Save all schedules to file"""
        try:
            schedules_list = [asdict(schedule) for schedule in self.schedules.values()]
            with open(self.multi_schedules_file, 'w') as f:
                json.dump(schedules_list, f, indent=2)
        except Exception as e:
            print(f"Error saving schedules: {e}")
    
    def estimate_execution_time(self, search_terms, limit_per_run):
        """Estimate how long the schedule will take to execute"""
        time_per_contact = 0.1  # 6 seconds per contact average
        total_contacts = len(search_terms) * limit_per_run
        estimated_minutes = int(total_contacts * time_per_contact)
        buffer_minutes = max(5, len(search_terms) * 2)
        return estimated_minutes + buffer_minutes
    
    def validate_time_format(self, time_str):
        """Validate time format HH:MM"""
        try:
            datetime.strptime(time_str, "%H:%M")
            return True
        except ValueError:
            return False
    
    def validate_duration(self, duration_str):
        """Validate and convert duration to minutes"""
        duration_str = duration_str.lower().strip()
        
        if duration_str.endswith('m') or duration_str.endswith('min') or duration_str.endswith('minute') or duration_str.endswith('minutes'):
            try:
                return int(duration_str.split()[0].replace('m', '').replace('in', '').replace('ute', '').replace('s', ''))
            except:
                return None
        elif duration_str.endswith('h') or duration_str.endswith('hour') or duration_str.endswith('hours'):
            try:
                hours = int(duration_str.split()[0].replace('h', '').replace('our', '').replace('s', ''))
                return hours * 60
            except:
                return None
        elif duration_str.endswith('d') or duration_str.endswith('day') or duration_str.endswith('days'):
            try:
                days = int(duration_str.split()[0].replace('d', '').replace('ay', '').replace('s', ''))
                return days * 24 * 60
            except:
                return None
        else:
            try:
                return int(duration_str)
            except:
                return None
    
    def format_duration(self, minutes):
        """Format duration in minutes to readable format"""
        if minutes < 60:
            return f"{minutes} minutes"
        elif minutes < 1440:
            hours = minutes // 60
            mins = minutes % 60
            if mins == 0:
                return f"{hours} hour{'s' if hours != 1 else ''}"
            else:
                return f"{hours} hour{'s' if hours != 1 else ''} {mins} minute{'s' if mins != 1 else ''}"
        else:
            days = minutes // 1440
            remaining_hours = (minutes % 1440) // 60
            if remaining_hours == 0:
                return f"{days} day{'s' if days != 1 else ''}"
            else:
                return f"{days} day{'s' if days != 1 else ''} {remaining_hours} hour{'s' if remaining_hours != 1 else ''}"
    
    def quick_schedule_setup(self):
        """Set up a one-time scheduled run"""
        self.clear_screen()
        self.print_header()
        print("⏰ QUICK SCHEDULE - ONE TIME RUN")
        print("=" * 35)
        
        # Get search terms
        search_terms = []
        print("Enter search terms (one per line, empty line to finish):")
        while True:
            search = input(f"Search {len(search_terms) + 1}: ").strip()
            if not search:
                break
            search_terms.append(search)
        
        if not search_terms:
            print("❌ No search terms entered!")
            input("Press Enter to continue...")
            return
        
        # Get time
        while True:
            start_time = self.get_user_input("Enter start time (HH:MM format, e.g., 14:30)")
            if self.validate_time_format(start_time):
                break
            print("❌ Invalid time format! Use HH:MM (e.g., 14:30)")
        
        # Get other settings
        limit = int(self.get_user_input("Contacts per search", self.default_limit))
        skip_duplicates = self.get_user_input("Skip duplicates? (y/n)", "y").lower() == 'y'
        
        # Create schedule
        schedule_id = f"quick_{int(time.time())}"
        estimated_duration = self.estimate_execution_time(search_terms, limit)
        
        schedule = Schedule(
            id=schedule_id,
            name=f"Quick Schedule - {start_time}",
            search_terms=search_terms,
            start_time=start_time,
            duration_minutes=0,
            limit_per_run=limit,
            skip_duplicates=skip_duplicates,
            is_recurring=False,
            is_active=True,
            estimated_duration_minutes=estimated_duration
        )
        
        # Check conflicts and offer smart resolution
        conflicts = self.check_schedule_conflicts(schedule)
        if conflicts:
            print(f"\n⚠️ CONFLICTS DETECTED:")
            for conflict in conflicts:
                print(f"   - {conflict}")
            
            # Show safe time suggestions
            safe_times = self.get_safe_time_suggestions(schedule)
            if safe_times:
                print(f"\n💡 SUGGESTED SAFE TIMES:")
                for i, safe_time in enumerate(safe_times[:5], 1):
                    print(f"   {i}. {safe_time}")
            
            print(f"\n🔧 CONFLICT RESOLUTION OPTIONS:")
            print(f"   1. Use suggested safe time")
            print(f"   2. Auto-sequence (run after conflicting schedule)")
            print(f"   3. Proceed with conflict (auto-sequencing enabled)")
            print(f"   4. Cancel schedule")
            
            choice = self.get_user_input("Select option (1-4)", "2")
            
            if choice == "1" and safe_times:
                # Use suggested time
                print(f"\nSelect safe time:")
                for i, safe_time in enumerate(safe_times[:5], 1):
                    print(f"   {i}. {safe_time}")
                
                try:
                    time_choice = int(self.get_user_input("Enter time number")) - 1
                    if 0 <= time_choice < len(safe_times):
                        schedule.start_time = safe_times[time_choice]
                        print(f"✅ Schedule time updated to: {schedule.start_time}")
                    else:
                        print("❌ Invalid selection, using auto-sequence instead")
                        schedule.start_time = self.calculate_sequential_time(schedule)
                except:
                    print("❌ Invalid input, using auto-sequence instead")
                    schedule.start_time = self.calculate_sequential_time(schedule)
            
            elif choice == "2":
                # Auto-sequence: calculate time after conflicting schedules
                new_time = self.calculate_sequential_time(schedule)
                if new_time:
                    schedule.start_time = new_time
                    print(f"✅ Schedule auto-sequenced to: {schedule.start_time}")
                    print(f"   Will run automatically after conflicting schedules complete")
                else:
                    print("❌ Could not calculate sequential time, keeping original")
            
            elif choice == "3":
                # Proceed with conflict but enable auto-sequencing during execution
                print(f"⚠️ Proceeding with original time: {schedule.start_time}")
                print(f"🔧 Auto-sequencing enabled: will wait for conflicting schedules to complete")
                # Add metadata for sequential execution
                schedule.auto_sequence = True
            
            elif choice == "4":
                # Cancel
                print("Schedule cancelled.")
                input("Press Enter to continue...")
                return
        
        # Save schedule
        self.schedules[schedule_id] = schedule
        self.save_schedules()
        
        print(f"\n✅ Quick schedule created!")
        print(f"   ID: {schedule_id}")
        print(f"   Search terms: {', '.join(search_terms)}")
        print(f"   Start time: {schedule.start_time}")
        print(f"   Estimated duration: {estimated_duration} minutes")
        
        if hasattr(schedule, 'auto_sequence') and schedule.auto_sequence:
            print(f"   🔧 Auto-sequencing: Will run after conflicting schedules")
        
        input("Press Enter to continue...")
    
    def recurring_schedule_setup(self):
        """Set up recurring scheduled runs"""
        self.clear_screen()
        self.print_header()
        print("🔄 RECURRING SCHEDULE - AUTOMATED RUNS")
        print("=" * 40)
        
        # Get search terms
        search_terms = []
        print("Enter search terms (one per line, empty line to finish):")
        while True:
            search = input(f"Search {len(search_terms) + 1}: ").strip()
            if not search:
                break
            search_terms.append(search)
        
        if not search_terms:
            print("❌ No search terms entered!")
            input("Press Enter to continue...")
            return
        
        # Get start time
        while True:
            start_time = self.get_user_input("Enter first run time (HH:MM format, e.g., 09:00)")
            if self.validate_time_format(start_time):
                break
            print("❌ Invalid time format! Use HH:MM (e.g., 09:00)")
        
        # Get duration/interval
        print("\nDuration examples: 30m, 2h, 1d, or just 90 (for minutes)")
        while True:
            duration_input = self.get_user_input("Enter interval between runs")
            duration_minutes = self.validate_duration(duration_input)
            if duration_minutes and duration_minutes > 0:
                break
            print("❌ Invalid duration! Try: 30m, 2h, 1d, or just 90")
        
        # Get other settings
        limit = int(self.get_user_input("Contacts per search", self.default_limit))
        skip_duplicates = self.get_user_input("Skip duplicates? (y/n)", "y").lower() == 'y'
        
        # Create schedule
        schedule_id = f"recurring_{int(time.time())}"
        estimated_duration = self.estimate_execution_time(search_terms, limit)
        
        schedule = Schedule(
            id=schedule_id,
            name=f"Recurring Schedule - {start_time}",
            search_terms=search_terms,
            start_time=start_time,
            duration_minutes=duration_minutes,
            limit_per_run=limit,
            skip_duplicates=skip_duplicates,
            is_recurring=True,
            is_active=True,
            estimated_duration_minutes=estimated_duration
        )
        
        # Check conflicts
        conflicts = self.check_schedule_conflicts(schedule)
        if conflicts:
            print(f"\n⚠️ CONFLICTS DETECTED:")
            for conflict in conflicts:
                print(f"   - {conflict}")
            
            proceed = self.get_user_input("\nProceed anyway? (y/n)", "n").lower() == 'y'
            if not proceed:
                print("Schedule cancelled.")
                input("Press Enter to continue...")
                return
        
        # Save schedule
        self.schedules[schedule_id] = schedule
        self.save_schedules()
        
        print(f"\n✅ Recurring schedule created!")
        print(f"   ID: {schedule_id}")
        print(f"   Search terms: {', '.join(search_terms)}")
        print(f"   Start time: {start_time}")
        print(f"   Interval: {self.format_duration(duration_minutes)}")
        print(f"   Estimated duration per run: {estimated_duration} minutes")
        
        input("Press Enter to continue...")
    
    def view_all_schedules(self):
        """Display all schedules"""
        self.clear_screen()
        self.print_header()
        print("📅 ALL SCHEDULES")
        print("=" * 20)
        
        if not self.schedules:
            print("❌ No schedules configured")
            print("   Use option 1 or 2 to create schedules")
        else:
            for i, (schedule_id, schedule) in enumerate(self.schedules.items(), 1):
                status = "🟢 Active" if schedule.is_active else "🔴 Inactive"
                print(f"\n{i}. {schedule.name} ({status})")
                print(f"   ID: {schedule_id}")
                print(f"   🔍 Searches: {', '.join(schedule.search_terms)}")
                print(f"   ⏰ Start: {schedule.start_time}")
                
                if schedule.is_recurring:
                    print(f"   🔄 Interval: {self.format_duration(schedule.duration_minutes)}")
                else:
                    print(f"   🔄 Type: One-time")
                
                print(f"   📊 Contacts per search: {schedule.limit_per_run}")
                print(f"   ⏱️ Est. duration: {schedule.estimated_duration_minutes} min")
                print(f"   📈 Runs completed: {schedule.total_runs}")
                
                if schedule.last_run:
                    print(f"   🕐 Last run: {schedule.last_run}")
        
        input("\nPress Enter to continue...")
    
    def check_schedule_conflicts(self, new_schedule):
        """Check for conflicts with existing schedules"""
        conflicts = []
        
        for existing_id, existing in self.schedules.items():
            if not existing.is_active:
                continue
            
            # Direct time conflict
            if existing.start_time == new_schedule.start_time:
                conflicts.append(f"Direct time conflict with '{existing.name}' at {existing.start_time}")
            
            # Execution overlap
            overlap = self.check_execution_overlap(existing, new_schedule)
            if overlap:
                conflicts.append(overlap)
        
        return conflicts
    
    def check_execution_overlap(self, schedule1, schedule2):
        """Check if execution windows overlap"""
        try:
            time1 = datetime.strptime(schedule1.start_time, "%H:%M")
            time2 = datetime.strptime(schedule2.start_time, "%H:%M")
            
            end1 = time1 + timedelta(minutes=schedule1.estimated_duration_minutes)
            end2 = time2 + timedelta(minutes=schedule2.estimated_duration_minutes)
            
            if (time1 <= time2 < end1) or (time2 <= time1 < end2):
                return f"Execution overlap with '{schedule1.name}'"
        except:
            pass
        
        return None
    
    def get_safe_time_suggestions(self, new_schedule):
        """Generate smart time suggestions based on current time and existing schedules"""
        safe_times = []
        current_time = datetime.now()
        current_hour_minute = current_time.strftime("%H:%M")
        
        # Get conflicting schedules to understand the conflict better
        conflicting_schedules = []
        for existing_id, existing in self.schedules.items():
            if existing.is_active:
                conflicts = self.check_schedule_conflicts_between(new_schedule, existing)
                if conflicts:
                    conflicting_schedules.append(existing)
        
        # Strategy 1: Find slots BEFORE the first conflicting schedule (if there's time)
        before_slots = self.find_slots_before_conflicts(new_schedule, conflicting_schedules, current_time)
        safe_times.extend(before_slots)
        
        # Strategy 2: Find slots AFTER the last conflicting schedule
        after_slots = self.find_slots_after_conflicts(new_schedule, conflicting_schedules)
        safe_times.extend(after_slots)
        
        # Strategy 3: If no good slots found, add some reasonable alternatives
        if len(safe_times) < 3:
            fallback_slots = self.find_fallback_slots(new_schedule, current_time)
            safe_times.extend(fallback_slots)
        
        # Remove duplicates and sort by proximity to current time
        safe_times = list(dict.fromkeys(safe_times))  # Remove duplicates
        safe_times = self.sort_by_time_proximity(safe_times, current_hour_minute)
        
        return safe_times[:8]  # Return top 8 suggestions
    
    def check_schedule_conflicts_between(self, schedule1, schedule2):
        """Check conflicts between two specific schedules"""
        conflicts = []
        
        # Direct time conflict
        if schedule1.start_time == schedule2.start_time:
            conflicts.append("Direct time conflict")
        
        # Execution overlap
        try:
            time1 = datetime.strptime(schedule1.start_time, "%H:%M")
            time2 = datetime.strptime(schedule2.start_time, "%H:%M")
            
            end1 = time1 + timedelta(minutes=schedule1.estimated_duration_minutes)
            end2 = time2 + timedelta(minutes=schedule2.estimated_duration_minutes)
            
            if (time1 <= time2 < end1) or (time2 <= time1 < end2):
                conflicts.append("Execution overlap")
        except:
            pass
        
        return conflicts
    
    def find_slots_before_conflicts(self, new_schedule, conflicting_schedules, current_time):
        """Find safe slots before conflicting schedules"""
        before_slots = []
        
        if not conflicting_schedules:
            return before_slots
        
        # Find the earliest conflicting schedule
        earliest_conflict = None
        for conflict_schedule in conflicting_schedules:
            try:
                conflict_time = datetime.strptime(conflict_schedule.start_time, "%H:%M")
                if earliest_conflict is None or conflict_time < earliest_conflict:
                    earliest_conflict = conflict_time
            except:
                continue
        
        if earliest_conflict is None:
            return before_slots
        
        # Calculate when new schedule needs to finish to avoid conflict
        buffer_minutes = 10  # 10-minute buffer
        latest_start = earliest_conflict - timedelta(minutes=new_schedule.estimated_duration_minutes + buffer_minutes)
        
        # Only suggest times that are after current time
        current_plus_buffer = current_time + timedelta(minutes=5)  # 5-minute buffer from now
        
        if latest_start > current_plus_buffer:
            # We have time before the conflict - suggest slots
            start_checking = max(current_plus_buffer, current_time.replace(minute=0, second=0))
            
            # Generate 30-minute slots between now and latest_start
            checking_time = start_checking
            while checking_time <= latest_start and len(before_slots) < 4:
                time_str = checking_time.strftime("%H:%M")
                
                # Round to nearest 30-minute mark
                minute = checking_time.minute
                if minute < 15:
                    rounded_minute = 0
                elif minute < 45:
                    rounded_minute = 30
                else:
                    rounded_minute = 0
                    checking_time += timedelta(hours=1)
                
                rounded_time = checking_time.replace(minute=rounded_minute, second=0)
                time_str = rounded_time.strftime("%H:%M")
                
                # Check if this time is actually safe
                if self.is_time_slot_safe(time_str, new_schedule):
                    before_slots.append(time_str)
                
                checking_time += timedelta(minutes=30)
        
        return before_slots
    
    def find_slots_after_conflicts(self, new_schedule, conflicting_schedules):
        """Find safe slots after conflicting schedules complete"""
        after_slots = []
        
        if not conflicting_schedules:
            return after_slots
        
        # Find the latest ending conflicting schedule
        latest_end = None
        for conflict_schedule in conflicting_schedules:
            try:
                conflict_start = datetime.strptime(conflict_schedule.start_time, "%H:%M")
                conflict_end = conflict_start + timedelta(minutes=conflict_schedule.estimated_duration_minutes)
                
                if latest_end is None or conflict_end > latest_end:
                    latest_end = conflict_end
            except:
                continue
        
        if latest_end is None:
            return after_slots
        
        # Add buffer and suggest times after conflicts
        buffer_minutes = 10
        earliest_after = latest_end + timedelta(minutes=buffer_minutes)
        
        # Generate slots after conflicts (up to 4 suggestions)
        checking_time = earliest_after
        end_of_day = datetime.now().replace(hour=22, minute=0, second=0)  # Until 10 PM
        
        while checking_time <= end_of_day and len(after_slots) < 4:
            # Round to nearest 30-minute mark
            minute = checking_time.minute
            if minute < 15:
                rounded_minute = 0
            elif minute < 45:
                rounded_minute = 30
            else:
                rounded_minute = 0
                checking_time += timedelta(hours=1)
                continue
            
            rounded_time = checking_time.replace(minute=rounded_minute, second=0)
            time_str = rounded_time.strftime("%H:%M")
            
            # Check if this time is actually safe
            if self.is_time_slot_safe(time_str, new_schedule):
                after_slots.append(time_str)
            
            checking_time += timedelta(minutes=30)
        
        return after_slots
    
    def find_fallback_slots(self, new_schedule, current_time):
        """Find reasonable fallback slots if no good options found"""
        fallback_slots = []
        
        # Suggest some reasonable times around current time
        base_times = [
            current_time + timedelta(hours=1),
            current_time + timedelta(hours=2),
            current_time + timedelta(hours=3),
            current_time - timedelta(hours=1) if current_time.hour > 7 else current_time + timedelta(hours=4),
        ]
        
        for base_time in base_times:
            if 6 <= base_time.hour <= 22:  # Reasonable hours
                # Round to 30-minute marks
                minute = 0 if base_time.minute < 30 else 30
                rounded_time = base_time.replace(minute=minute, second=0)
                time_str = rounded_time.strftime("%H:%M")
                
                if self.is_time_slot_safe(time_str, new_schedule):
                    fallback_slots.append(time_str)
        
        return fallback_slots
    
    def is_time_slot_safe(self, test_time, new_schedule):
        """Check if a specific time slot is safe for the new schedule"""
        # Create temporary schedule to test
        temp_schedule = Schedule(
            id="temp",
            name="temp",
            search_terms=new_schedule.search_terms,
            start_time=test_time,
            duration_minutes=new_schedule.duration_minutes,
            limit_per_run=new_schedule.limit_per_run,
            skip_duplicates=new_schedule.skip_duplicates,
            is_recurring=new_schedule.is_recurring,
            is_active=True,
            estimated_duration_minutes=new_schedule.estimated_duration_minutes
        )
        
        # Check for conflicts
        conflicts = self.check_schedule_conflicts(temp_schedule)
        return len(conflicts) == 0
    
    def sort_by_time_proximity(self, time_list, current_time_str):
        """Sort times by proximity to current time"""
        try:
            current_time = datetime.strptime(current_time_str, "%H:%M")
            
            def time_distance(time_str):
                try:
                    test_time = datetime.strptime(time_str, "%H:%M")
                    # Calculate absolute difference in minutes
                    diff = abs((test_time - current_time).total_seconds() / 60)
                    # Prefer times after current time slightly
                    if test_time > current_time:
                        return diff
                    else:
                        return diff + 30  # Small penalty for past times
                except:
                    return 9999
            
            return sorted(time_list, key=time_distance)
        except:
            return time_list
    
    def calculate_sequential_time(self, new_schedule):
        """Calculate the best time to run after conflicting schedules"""
        latest_end_time = None
        
        # Find the latest end time of all conflicting schedules
        for existing_id, existing in self.schedules.items():
            if not existing.is_active:
                continue
            
            try:
                existing_start = datetime.strptime(existing.start_time, "%H:%M")
                existing_end = existing_start + timedelta(minutes=existing.estimated_duration_minutes)
                
                if latest_end_time is None or existing_end > latest_end_time:
                    latest_end_time = existing_end
            except:
                continue
        
        if latest_end_time:
            # Add 10-minute buffer after the latest schedule
            sequential_time = latest_end_time + timedelta(minutes=10)
            
            # If it goes past midnight, schedule for next day
            if sequential_time.hour >= 23:
                sequential_time = sequential_time.replace(hour=8, minute=0) + timedelta(days=1)
            
            return sequential_time.strftime("%H:%M")
        
        return None
    
    def schedules_would_conflict_now(self, schedule1, schedule2):
        """Check if two schedules would conflict if run simultaneously"""
        # Always conflict if one is already running
        if schedule2.currently_running:
            return True
        
        # Check execution overlap potential
        try:
            time1 = datetime.strptime(schedule1.start_time, "%H:%M")
            time2 = datetime.strptime(schedule2.start_time, "%H:%M")
            
            end1 = time1 + timedelta(minutes=schedule1.estimated_duration_minutes)
            end2 = time2 + timedelta(minutes=schedule2.estimated_duration_minutes)
            
            # If execution windows would overlap
            if (time1 <= time2 < end1) or (time2 <= time1 < end2):
                return True
        except:
            pass
        
        return False
    
    def start_scheduler(self):
        """Start the scheduling system"""
        active_schedules = [s for s in self.schedules.values() if s.is_active]
        
        if not active_schedules:
            print("❌ No active schedules! Create a schedule first.")
            input("Press Enter to continue...")
            return
        
        self.clear_screen()
        self.print_header()
        print("🚀 STARTING SCHEDULER")
        print("=" * 25)
        print(f"Active schedules: {len(active_schedules)}")
        for schedule in active_schedules:
            print(f"   - {schedule.name} at {schedule.start_time}")
        
        print(f"\n⏰ Current time: {datetime.now().strftime('%H:%M:%S')}")
        print("\n💡 Press Ctrl+C to stop the scheduler")
        print("=" * 40)
        
        try:
            while True:
                current_time = datetime.now().strftime("%H:%M")
                
                # Check if any schedule is currently running
                running_schedules = [s for s in active_schedules if s.currently_running]
                
                for schedule in active_schedules:
                    # Skip if this schedule is already running
                    if schedule.currently_running:
                        continue
                    
                    # Check for scheduled runs
                    should_run = False
                    run_type = ""
                    
                    if schedule.total_runs == 0 and current_time == schedule.start_time:
                        # First run
                        should_run = True
                        run_type = "FIRST RUN"
                    
                    elif schedule.is_recurring and schedule.last_run:
                        # Recurring run
                        try:
                            last_run_time = datetime.strptime(schedule.last_run, "%Y-%m-%d %H:%M:%S")
                            next_run_time = last_run_time + timedelta(minutes=schedule.duration_minutes)
                            
                            if datetime.now() >= next_run_time:
                                should_run = True
                                run_type = "RECURRING RUN"
                        except:
                            pass
                    
                    if should_run:
                        # Check for auto-sequencing
                        if hasattr(schedule, 'auto_sequence') and schedule.auto_sequence and running_schedules:
                            print(f"\n⏳ WAITING: {schedule.name} (auto-sequencing)")
                            print(f"   Waiting for {len(running_schedules)} schedule(s) to complete...")
                            continue
                        
                        # Check for conflicts with currently running schedules
                        has_conflict = False
                        for running_schedule in running_schedules:
                            if self.schedules_would_conflict_now(schedule, running_schedule):
                                has_conflict = True
                                break
                        
                        if has_conflict:
                            print(f"\n⏳ QUEUED: {schedule.name} (waiting for running schedules)")
                            continue
                        
                        print(f"\n🎯 {run_type}: {schedule.name} ({schedule.start_time})")
                        self.execute_schedule(schedule)
                
                # Show status every 30 seconds
                if datetime.now().second % 30 == 0:
                    print(f"⏳ Monitoring... Current time: {datetime.now().strftime('%H:%M:%S')}")
                
                time.sleep(1)
                
        except KeyboardInterrupt:
            print(f"\n\n🛑 SCHEDULER STOPPED")
            print("All schedules remain saved for next time.")
            input("Press Enter to continue...")
    
    def execute_schedule(self, schedule):
        """Execute a specific schedule with sequential execution support"""
        # Mark as currently running
        schedule.currently_running = True
        self.save_schedules()
        
        print(f"\n🎯 EXECUTING: {schedule.name}")
        print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        # Show auto-sequencing info if applicable
        if hasattr(schedule, 'auto_sequence') and schedule.auto_sequence:
            print(f"🔧 Auto-sequencing: Running after conflicting schedules")
        
        print("=" * 50)
        
        success_count = 0
        start_time = datetime.now()
        
        try:
            for i, search_term in enumerate(schedule.search_terms, 1):
                print(f"\n--- Search {i}/{len(schedule.search_terms)}: {search_term} ---")
                
                command = f'-s "{search_term}" --limit {schedule.limit_per_run}'
                if schedule.skip_duplicates:
                    command += " --skip-duplicates"
                
                try:
                    print(f"🚀 Running: python main.py {command}")
                    result = subprocess.run(f"python main.py {command}", shell=True, capture_output=False)
                    if result.returncode == 0:
                        success_count += 1
                        print(f"✅ Search completed successfully")
                    else:
                        print(f"❌ Search failed")
                except Exception as e:
                    print(f"❌ Error: {e}")
        
        finally:
            # Always mark as not running, even if there was an error
            schedule.currently_running = False
            
            # Update schedule stats
            schedule.last_run = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            schedule.total_runs += 1
            
            # Reset auto_sequence flag after first run
            if hasattr(schedule, 'auto_sequence'):
                schedule.auto_sequence = False
            
            self.save_schedules()
        
        end_time = datetime.now()
        actual_duration = int((end_time - start_time).total_seconds() / 60)
        
        print(f"\n✅ SCHEDULE COMPLETED")
        print(f"   Successful searches: {success_count}/{len(schedule.search_terms)}")
        print(f"   Total runs: {schedule.total_runs}")
        print(f"   Actual duration: {actual_duration} minutes")
        print(f"   Estimated duration: {schedule.estimated_duration_minutes} minutes")
        
        if schedule.is_recurring:
            next_run = datetime.now() + timedelta(minutes=schedule.duration_minutes)
            print(f"   Next run: {next_run.strftime('%Y-%m-%d %H:%M:%S')}")
        
        # Notify about queued schedules
        queued_schedules = [s for s in self.schedules.values() 
                           if s.is_active and hasattr(s, 'auto_sequence') and s.auto_sequence]
        
        if queued_schedules:
            print(f"\n🔄 QUEUED SCHEDULES WILL NOW RUN:")
            for queued in queued_schedules:
                print(f"   - {queued.name} (was waiting for this schedule)")
    
    def manual_schedule_run(self):
        """Run a schedule immediately"""
        if not self.schedules:
            print("❌ No schedules available! Create a schedule first.")
            input("Press Enter to continue...")
            return
        
        self.clear_screen()
        self.print_header()
        print("🚀 MANUAL RUN")
        print("=" * 15)
        
        # Show available schedules
        active_schedules = [s for s in self.schedules.values() if s.is_active]
        
        if not active_schedules:
            print("❌ No active schedules!")
            input("Press Enter to continue...")
            return
        
        print("Select schedule to run:")
        for i, schedule in enumerate(active_schedules, 1):
            print(f"{i}. {schedule.name} ({len(schedule.search_terms)} searches)")
        
        try:
            choice = int(self.get_user_input("Enter schedule number")) - 1
            if 0 <= choice < len(active_schedules):
                selected_schedule = active_schedules[choice]
                
                confirm = self.get_user_input(f"Run '{selected_schedule.name}' now? (y/n)", "y").lower() == 'y'
                if confirm:
                    self.execute_schedule(selected_schedule)
            else:
                print("❌ Invalid selection!")
        except:
            print("❌ Invalid input!")
        
        input("Press Enter to continue...")
    
    def schedule_management(self):
        """Manage existing schedules"""
        while True:
            self.clear_screen()
            self.print_header()
            print("⚙️ SCHEDULE MANAGEMENT")
            print("=" * 25)
            print("1. Edit schedule")
            print("2. Delete schedule")
            print("3. Activate/Deactivate schedule")
            print("4. Export schedules")
            print("5. Import schedules")
            print("6. Back to scheduler menu")
            print()
            
            choice = self.get_user_input("Select option (1-6)")
            
            if choice == "1":
                self.edit_schedule()
            elif choice == "2":
                self.delete_schedule()
            elif choice == "3":
                self.toggle_schedule()
            elif choice == "4":
                self.export_schedules()
            elif choice == "5":
                self.import_schedules()
            elif choice == "6":
                break
    
    def edit_schedule(self):
        """Edit an existing schedule"""
        if not self.schedules:
            print("❌ No schedules to edit!")
            input("Press Enter to continue...")
            return
        
        # Show schedules
        schedules_list = list(self.schedules.values())
        print("\nSelect schedule to edit:")
        for i, schedule in enumerate(schedules_list, 1):
            print(f"{i}. {schedule.name}")
        
        try:
            choice = int(self.get_user_input("Enter schedule number")) - 1
            if 0 <= choice < len(schedules_list):
                schedule = schedules_list[choice]
                
                print(f"\nEditing: {schedule.name}")
                print("Leave empty to keep current value")
                
                # Edit name
                new_name = self.get_user_input("New name", schedule.name)
                if new_name != schedule.name:
                    schedule.name = new_name
                
                # Edit start time
                new_time = self.get_user_input("New start time (HH:MM)", schedule.start_time)
                if self.validate_time_format(new_time):
                    schedule.start_time = new_time
                
                self.save_schedules()
                print("✅ Schedule updated!")
            else:
                print("❌ Invalid selection!")
        except:
            print("❌ Invalid input!")
        
        input("Press Enter to continue...")
    
    def delete_schedule(self):
        """Delete a schedule"""
        if not self.schedules:
            print("❌ No schedules to delete!")
            input("Press Enter to continue...")
            return
        
        schedules_list = list(self.schedules.items())
        print("\nSelect schedule to delete:")
        for i, (schedule_id, schedule) in enumerate(schedules_list, 1):
            print(f"{i}. {schedule.name}")
        
        try:
            choice = int(self.get_user_input("Enter schedule number")) - 1
            if 0 <= choice < len(schedules_list):
                schedule_id, schedule = schedules_list[choice]
                
                confirm = self.get_user_input(f"Delete '{schedule.name}'? (y/n)", "n").lower() == 'y'
                if confirm:
                    del self.schedules[schedule_id]
                    self.save_schedules()
                    print("✅ Schedule deleted!")
            else:
                print("❌ Invalid selection!")
        except:
            print("❌ Invalid input!")
        
        input("Press Enter to continue...")
    
    def toggle_schedule(self):
        """Activate/deactivate a schedule"""
        if not self.schedules:
            print("❌ No schedules available!")
            input("Press Enter to continue...")
            return
        
        schedules_list = list(self.schedules.values())
        print("\nSelect schedule to toggle:")
        for i, schedule in enumerate(schedules_list, 1):
            status = "🟢 Active" if schedule.is_active else "🔴 Inactive"
            print(f"{i}. {schedule.name} ({status})")
        
        try:
            choice = int(self.get_user_input("Enter schedule number")) - 1
            if 0 <= choice < len(schedules_list):
                schedule = schedules_list[choice]
                schedule.is_active = not schedule.is_active
                status = "activated" if schedule.is_active else "deactivated"
                
                self.save_schedules()
                print(f"✅ Schedule {status}!")
            else:
                print("❌ Invalid selection!")
        except:
            print("❌ Invalid input!")
        
        input("Press Enter to continue...")
    
    def export_schedules(self):
        """Export schedules to file"""
        if not self.schedules:
            print("❌ No schedules to export!")
            input("Press Enter to continue...")
            return
        
        filename = f"schedules_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        try:
            schedules_data = [asdict(schedule) for schedule in self.schedules.values()]
            with open(filename, 'w') as f:
                json.dump(schedules_data, f, indent=2)
            
            print(f"✅ Schedules exported to: {filename}")
        except Exception as e:
            print(f"❌ Export failed: {e}")
        
        input("Press Enter to continue...")
    
    def import_schedules(self):
        """Import schedules from file"""
        filename = self.get_user_input("Enter filename to import")
        
        if not os.path.exists(filename):
            print(f"❌ File not found: {filename}")
            input("Press Enter to continue...")
            return
        
        try:
            with open(filename, 'r') as f:
                schedules_data = json.load(f)
            
            imported_count = 0
            for schedule_data in schedules_data:
                schedule = Schedule(**schedule_data)
                # Generate new ID to avoid conflicts
                new_id = f"imported_{int(time.time())}_{imported_count}"
                schedule.id = new_id
                self.schedules[new_id] = schedule
                imported_count += 1
            
            self.save_schedules()
            print(f"✅ Imported {imported_count} schedules!")
        except Exception as e:
            print(f"❌ Import failed: {e}")
        
        input("Press Enter to continue...")
    
    def conflict_checker(self):
        """Check for schedule conflicts"""
        self.clear_screen()
        self.print_header()
        print("🔍 CONFLICT CHECKER")
        print("=" * 20)
        
        if len(self.schedules) < 2:
            print("❌ Need at least 2 schedules to check conflicts")
            input("Press Enter to continue...")
            return
        
        active_schedules = [s for s in self.schedules.values() if s.is_active]
        
        if len(active_schedules) < 2:
            print("❌ Need at least 2 active schedules to check conflicts")
            input("Press Enter to continue...")
            return
        
        print(f"Checking {len(active_schedules)} active schedules for conflicts...\n")
        
        conflicts_found = False
        
        for i, schedule1 in enumerate(active_schedules):
            for j, schedule2 in enumerate(active_schedules[i+1:], i+1):
                conflicts = []
                
                # Direct time conflict
                if schedule1.start_time == schedule2.start_time:
                    conflicts.append(f"Same start time: {schedule1.start_time}")
                
                # Execution overlap
                overlap = self.check_execution_overlap(schedule1, schedule2)
                if overlap:
                    conflicts.append("Execution windows overlap")
                
                if conflicts:
                    conflicts_found = True
                    print(f"⚠️ CONFLICT DETECTED:")
                    print(f"   Schedule 1: {schedule1.name} at {schedule1.start_time}")
                    print(f"   Schedule 2: {schedule2.name} at {schedule2.start_time}")
                    print(f"   Issues: {', '.join(conflicts)}")
                    print()
        
        if not conflicts_found:
            print("✅ NO CONFLICTS DETECTED!")
            print("All active schedules are safe to run together.")
        
        input("\nPress Enter to continue...")
    
    def schedule_help(self):
        """Show scheduling help and examples"""
        self.clear_screen()
        self.print_header()
        print("📖 SCHEDULING HELP & EXAMPLES")
        print("=" * 35)
        
        print("\n🕐 TIME FORMAT:")
        print("   Use 24-hour format: HH:MM")
        print("   Examples: 09:30, 14:15, 23:45")
        
        print("\n⏱️ DURATION FORMATS:")
        print("   Minutes: 30m, 45min, 90 minutes")
        print("   Hours: 2h, 3 hours")
        print("   Days: 1d, 2 days")
        print("   Just numbers: 120 (means 120 minutes)")
        
        print("\n📋 EXAMPLE SCHEDULES:")
        print("   1. Daily morning run:")
        print("      - Start: 09:00")
        print("      - Interval: 24h")
        print("      - Searches: 'restaurants delhi', 'cafes mumbai'")
        
        print("\n   2. Hourly business updates:")
        print("      - Start: 10:00")
        print("      - Interval: 1h")
        print("      - Searches: 'new businesses bangalore'")
        
        print("\n🔄 CONFLICT PREVENTION:")
        print("   - Space schedules 30+ minutes apart")
        print("   - Use conflict checker before starting")
        print("   - Consider execution time estimates")
        print("   - Use daily rotation instead of same-day multiple schedules")
        
        print("\n💾 FILES CREATED:")
        print("   - multi_schedules.json: All your schedules")
        print("   - output/all_contacts.csv: Scraped data")
        print("   - fetched_contacts.json: Duplicate prevention")
        
        input("\nPress Enter to continue...")
        
    def run(self):
        """Main application loop"""
        while True:
            self.clear_screen()
            self.print_header()
            self.print_main_menu()
            
            choice = self.get_user_input("Select option (1-10)")
            
            if choice == "1":
                self.quick_search()
            elif choice == "2":
                self.custom_search()
            elif choice == "3":
                self.batch_search()
            elif choice == "4":
                self.scheduled_scraping()
            elif choice == "5":
                self.cache_management()
            elif choice == "6":
                self.view_statistics()
            elif choice == "7":
                self.troubleshooting_tools()
            elif choice == "8":
                self.settings_configuration()
            elif choice == "9":
                self.show_help()
            elif choice == "10":
                print("\n👋 Thank you for using Google Maps Scraper!")
                print("Your data is saved in: output/all_contacts.csv")
                break
            else:
                print("❌ Invalid choice. Please select 1-10.")
                input("Press Enter to continue...")

def main():
    """Entry point for the interactive scraper"""
    try:
        scraper = InteractiveScraper()
        scraper.run()
    except KeyboardInterrupt:
        print("\n\n👋 Goodbye!")
    except Exception as e:
        print(f"\n❌ An error occurred: {e}")
        print("Please check your setup and try again.")

if __name__ == "__main__":
    main()