"""
Standalone Data Loader Script
Run this script to load all Excel files into the database
"""
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from config.config import Config
from utils.database import DatabaseManager
from datetime import datetime


def main():
    """Main data loading function"""
    print("\n" + "="*70)
    print(" ADS-B DATA LOADER - DISASTER MANAGEMENT SYSTEM")
    print("="*70)
    print(f"\n⏰ Start Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Initialize database
    print("\n📦 Initializing database...")
    db = DatabaseManager()
    
    # Get list of Excel files
    excel_files = Config.get_adsb_files()
    
    if not excel_files:
        print("\n⚠️  No Excel files found in data directory!")
        print(f"   Directory: {Config.ADSB_DATA_DIR}")
        print(f"   Pattern: {Config.ADSB_FILE_PATTERN}")
        print("\n💡 Please ensure Excel files are in the 'data' directory")
        return
    
    print(f"\n📂 Found {len(excel_files)} Excel file(s):")
    for idx, file_path in enumerate(excel_files, 1):
        file_name = Path(file_path).name
        file_size = Path(file_path).stat().st_size / (1024 * 1024)  # MB
        print(f"   {idx}. {file_name} ({file_size:.2f} MB)")
    
    # Confirm loading
    print("\n" + "="*70)
    response = input("🚀 Proceed with data loading? (yes/no): ").strip().lower()
    
    if response not in ['yes', 'y']:
        print("\n❌ Loading cancelled by user")
        return
    
    print("\n" + "="*70)
    print(" STARTING DATA LOAD")
    print("="*70)
    
    # Load all files
    start_time = datetime.now()
    db.load_all_adsb_files(excel_files)
    end_time = datetime.now()
    
    duration = (end_time - start_time).total_seconds()
    
    # Display statistics
    print("\n" + "="*70)
    print(" DATA LOADING COMPLETE")
    print("="*70)
    
    stats = db.get_data_statistics()
    
    print(f"\n⏱️  Total Time: {duration:.2f} seconds ({duration/60:.2f} minutes)")
    print(f"\n📊 DATABASE STATISTICS:")
    print(f"   Total Records: {stats['total_records']:,}")
    print(f"   Unique Aircraft: {stats['unique_aircraft']:,}")
    print(f"   Emergency Flights: {stats['emergency_flights']:,}")
    
    print(f"\n📅 RECORDS BY MONTH:")
    for month_stat in stats['records_by_month']:
        month = month_stat.get('_month', 'Unknown')
        count = month_stat.get('count', 0)
        print(f"   {month}: {count:,} records")
    
    print(f"\n📁 RECORDS BY FILE:")
    for file_stat in stats['records_by_file']:
        file_name = file_stat.get('_file_name', 'Unknown')
        count = file_stat.get('count', 0)
        print(f"   {file_name}: {count:,} records")
    
    # Show loading status
    print(f"\n📋 LOADING STATUS:")
    loading_status = db.get_loading_status()
    for status in loading_status:
        status_icon = "✅" if status['load_status'] == 'success' else "❌"
        print(f"   {status_icon} {status['file_name']}")
        print(f"      Status: {status['load_status']}")
        print(f"      Sheets: {status['sheet_count']}")
        print(f"      Records: {status['total_records']:,}")
        if status['error_message']:
            print(f"      Error: {status['error_message']}")
    
    print("\n" + "="*70)
    print(" 🎉 ALL DONE!")
    print("="*70)
    print(f"\n⏰ End Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"\n💡 You can now run 'python main.py' to start the chatbot\n")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️  Loading interrupted by user")
    except Exception as e:
        print(f"\n\n❌ Fatal error: {str(e)}")
        import traceback
        traceback.print_exc()
