#!/usr/bin/env python3
"""
HUST Solar Car Database Cleanup Utility
=======================================
Standalone script for database maintenance and cleanup operations.
Can be run manually or via cron jobs for automated maintenance.

Usage:
    python cleanup_utility.py --help
    python cleanup_utility.py --stats
    python cleanup_utility.py --dry-run
    python cleanup_utility.py --execute
    python cleanup_utility.py --recommendations
"""

import sys
import argparse
import logging
import json
from datetime import datetime
from pathlib import Path

# Add backend to path for imports
sys.path.append(str(Path(__file__).parent))

try:
    from backend.database_cleanup import (
        run_cleanup,
        get_database_stats,
        get_cleanup_recommendations
    )
    from backend.config import (
        BATTERY_RETENTION_DAYS,
        MOTOR_RETENTION_DAYS,
        MPPT_RETENTION_DAYS,
        VEHICLE_RETENTION_DAYS
    )
except ImportError as e:
    print(f"❌ Error importing modules: {e}")
    print("Make sure you're running this from the project root directory.")
    sys.exit(1)

def setup_logging(verbose=False):
    """Setup logging configuration"""
    level = logging.DEBUG if verbose else logging.INFO
    
    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler('cleanup.log')
        ]
    )
    
    return logging.getLogger(__name__)

def print_banner():
    """Print application banner"""
    print("=" * 60)
    print("🏁 HUST Solar Car Database Cleanup Utility")
    print("=" * 60)
    print()

def print_stats(stats):
    """Print database statistics in a formatted way"""
    if not stats:
        print("❌ No statistics available")
        return
    
    print("📊 DATABASE STATISTICS")
    print("-" * 40)
    
    total_records = sum(table['total_records'] for table in stats['table_stats'].values())
    total_deletable = sum(table['records_to_delete'] for table in stats['table_stats'].values())
    
    print(f"Total Records:    {total_records:,}")
    print(f"Deletable Records: {total_deletable:,}")
    print(f"Cleanup Percentage: {(total_deletable/total_records*100) if total_records > 0 else 0:.1f}%")
    print()
    
    print("📋 TABLE BREAKDOWN")
    print("-" * 40)
    
    for table_name, table_stats in stats['table_stats'].items():
        display_name = {
            'Battery Data Table': 'Battery',
            'Motor Data Table': 'Motor', 
            'MPPT Data Table': 'Solar (MPPT)',
            'Vehicle Data Table': 'Vehicle'
        }.get(table_name, table_name)
        
        print(f"{display_name:<15} | {table_stats['total_records']:>8,} total | {table_stats['records_to_delete']:>8,} deletable | {table_stats['retention_days']:>2}d retention")
        
        if table_stats['oldest_record']:
            oldest_date = datetime.fromisoformat(table_stats['oldest_record'].replace('Z', '+00:00')).strftime('%Y-%m-%d')
            print(f"{'':15} | Oldest: {oldest_date}")
        print()

def print_recommendations(recommendations):
    """Print cleanup recommendations"""
    if not recommendations or 'error' in recommendations:
        print("❌ No recommendations available")
        return
    
    print("🔍 CLEANUP RECOMMENDATIONS")
    print("-" * 40)
    
    action = recommendations['recommended_action']
    total_records = recommendations['total_records']
    total_deletable = recommendations['total_deletable']
    
    # Action-specific messages
    if action == 'cleanup_urgent':
        print("🚨 URGENT CLEANUP NEEDED!")
        print(f"Database has {total_records:,} records with {total_deletable:,} deletable.")
        print("Performance may be significantly affected.")
    elif action == 'cleanup_recommended':
        print("⚠️  CLEANUP RECOMMENDED")
        print(f"{total_deletable:,} old records can be safely removed to improve performance.")
    elif action == 'cleanup_beneficial':
        print("💡 CLEANUP BENEFICIAL")
        print(f"{total_deletable:,} records can be removed to free up space.")
    else:
        print("✅ DATABASE HEALTHY")
        print(f"Only {total_deletable:,} old records available for cleanup.")
    
    print()
    
    # Urgent cleanup table analysis
    if recommendations['urgent_cleanup_needed']:
        print("⚠️  TABLES NEEDING URGENT ATTENTION:")
        for table, analysis in recommendations['table_analysis'].items():
            if analysis['recommendation'] in ['cleanup_urgent', 'cleanup_recommended']:
                display_name = {
                    'Battery Data Table': 'Battery',
                    'Motor Data Table': 'Motor',
                    'MPPT Data Table': 'Solar',
                    'Vehicle Data Table': 'Vehicle'
                }.get(table, table)
                print(f"  • {display_name}: {analysis['record_count']:,} records ({analysis['deletable_count']:,} deletable)")
        print()

def print_cleanup_result(result):
    """Print cleanup execution results"""
    if 'error' in result:
        print(f"❌ Cleanup failed: {result['error']}")
        return
    
    action = "WOULD DELETE" if result['dry_run'] else "DELETED"
    print(f"✅ CLEANUP {'PREVIEW' if result['dry_run'] else 'COMPLETED'}")
    print("-" * 40)
    print(f"{action}: {result['total_deleted']:,} records")
    
    if not result['dry_run']:
        print(f"Duration: {result['duration']:.2f} seconds")
    
    print()
    print("📋 TABLE BREAKDOWN:")
    
    for table_name, table_result in result['tables_processed'].items():
        display_name = {
            'Battery Data Table': 'Battery',
            'Motor Data Table': 'Motor',
            'MPPT Data Table': 'Solar (MPPT)',
            'Vehicle Data Table': 'Vehicle'
        }.get(table_name, table_name)
        
        print(f"  {display_name:<15} | {table_result['records_deleted']:>8,} records")
    
    print()

def confirm_cleanup():
    """Get user confirmation for cleanup execution"""
    print("⚠️  WARNING: This will permanently delete old telemetry data!")
    print("This action cannot be undone.")
    print()
    
    while True:
        response = input("Do you want to proceed? (yes/no): ").strip().lower()
        if response in ['yes', 'y']:
            return True
        elif response in ['no', 'n']:
            return False
        else:
            print("Please enter 'yes' or 'no'")

def main():
    """Main application entry point"""
    parser = argparse.ArgumentParser(
        description='HUST Solar Car Database Cleanup Utility',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s --stats                    # Show database statistics
  %(prog)s --recommendations         # Show cleanup recommendations  
  %(prog)s --dry-run                 # Preview what would be deleted
  %(prog)s --execute                 # Execute cleanup (with confirmation)
  %(prog)s --execute --force         # Execute cleanup without confirmation
  %(prog)s --execute --force --quiet # Silent cleanup execution
        """
    )
    
    parser.add_argument('--stats', action='store_true',
                       help='Show database statistics only')
    parser.add_argument('--recommendations', action='store_true', 
                       help='Show cleanup recommendations')
    parser.add_argument('--dry-run', action='store_true',
                       help='Show what would be deleted without deleting')
    parser.add_argument('--execute', action='store_true',
                       help='Execute actual cleanup')
    parser.add_argument('--force', action='store_true',
                       help='Skip confirmation prompts')
    parser.add_argument('--quiet', action='store_true',
                       help='Minimal output (for automated scripts)')
    parser.add_argument('--verbose', action='store_true',
                       help='Verbose output for debugging')
    parser.add_argument('--json', action='store_true',
                       help='Output results in JSON format')
    
    args = parser.parse_args()
    
    # Setup logging
    logger = setup_logging(args.verbose)
    
    # Print banner unless quiet mode
    if not args.quiet:
        print_banner()
    
    # If no action specified, show help
    if not any([args.stats, args.recommendations, args.dry_run, args.execute]):
        parser.print_help()
        return 0
    
    try:
        # Show statistics
        if args.stats:
            if not args.quiet:
                print("Loading database statistics...")
                print()
            
            stats = get_database_stats()
            
            if args.json:
                print(json.dumps(stats, indent=2, default=str))
            else:
                print_stats(stats)
            
            return 0
        
        # Show recommendations
        if args.recommendations:
            if not args.quiet:
                print("Analyzing database for cleanup recommendations...")
                print()
            
            recommendations = get_cleanup_recommendations()
            
            if args.json:
                print(json.dumps(recommendations, indent=2, default=str))
            else:
                print_recommendations(recommendations)
            
            return 0
        
        # Dry run or execute cleanup
        if args.dry_run or args.execute:
            dry_run = args.dry_run
            
            if not args.quiet:
                action = "preview" if dry_run else "execute"
                print(f"Starting cleanup {action}...")
                print()
            
            # Get confirmation for actual execution
            if args.execute and not dry_run and not args.force:
                if not confirm_cleanup():
                    print("Cleanup cancelled by user.")
                    return 0
                print()
            
            # Run cleanup
            result = run_cleanup(dry_run=dry_run)
            
            if args.json:
                print(json.dumps(result, indent=2, default=str))
            else:
                print_cleanup_result(result)
            
            # Return error code if cleanup failed
            if 'error' in result:
                return 1
            
            return 0
            
    except KeyboardInterrupt:
        print("\n❌ Operation cancelled by user")
        return 1
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        if args.verbose:
            import traceback
            traceback.print_exc()
        return 1

if __name__ == "__main__":
    sys.exit(main())
