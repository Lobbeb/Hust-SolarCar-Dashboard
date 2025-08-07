"""
HUST Solar Car Database Cleanup System
======================================
Automated database maintenance for telemetry data management.
Prevents database overflow during long racing sessions.
"""

import pymysql
import logging
from datetime import datetime, timedelta
from backend.helpers import get_db_connection
import threading
import schedule
import time

logger = logging.getLogger(__name__)

class DatabaseCleaner:
    """Professional database cleanup system for solar car telemetry"""
    
    def __init__(self):
        from backend.config import (BATTERY_RETENTION_DAYS, MOTOR_RETENTION_DAYS, 
                           MPPT_RETENTION_DAYS, VEHICLE_RETENTION_DAYS,
                           LATEST_BATTERY_PRESERVE, LATEST_MOTOR_PRESERVE,
                           LATEST_MPPT_PRESERVE, LATEST_VEHICLE_PRESERVE)
        
        # Racing-optimized retention periods (configurable)
        self.retention_days = {
            'Battery Data Table': BATTERY_RETENTION_DAYS,
            'Motor Data Table': MOTOR_RETENTION_DAYS,  
            'MPPT Data Table': MPPT_RETENTION_DAYS,
            'Vehicle Data Table': VEHICLE_RETENTION_DAYS
        }
        
        # Safety limits - never delete if table has less than this
        self.min_records_to_keep = {
            'Battery Data Table': 1000,   # Keep at least 1000 battery records
            'Motor Data Table': 1000,     # Keep at least 1000 motor records
            'MPPT Data Table': 1000,      # Keep at least 1000 solar records
            'Vehicle Data Table': 500     # Keep at least 500 vehicle records
        }
        
        # Always preserve the latest N records regardless of age (configurable)
        self.latest_records_to_preserve = {
            'Battery Data Table': LATEST_BATTERY_PRESERVE,
            'Motor Data Table': LATEST_MOTOR_PRESERVE,
            'MPPT Data Table': LATEST_MPPT_PRESERVE,
            'Vehicle Data Table': LATEST_VEHICLE_PRESERVE
        }
        
        self.cleanup_running = False
        
    def get_table_stats(self):
        """Get detailed statistics for all telemetry tables"""
        try:
            with get_db_connection() as conn:
                with conn.cursor() as cursor:
                    stats = {}
                    
                    for table in self.retention_days.keys():
                        # Get total count
                        cursor.execute(f"SELECT COUNT(*) as total_count FROM `{table}`")
                        total_result = cursor.fetchone()
                        
                        # Get oldest record
                        cursor.execute(f"SELECT MIN(timestamp) as oldest FROM `{table}`")
                        oldest_result = cursor.fetchone()
                        
                        # Get newest record
                        cursor.execute(f"SELECT MAX(timestamp) as newest FROM `{table}`")
                        newest_result = cursor.fetchone()
                        
                        # Get records older than retention period
                        cutoff_date = datetime.now() - timedelta(days=self.retention_days[table])
                        cursor.execute(f"SELECT COUNT(*) as old_count FROM `{table}` WHERE timestamp < %s", (cutoff_date,))
                        old_result = cursor.fetchone()
                        
                        stats[table] = {
                            'total_records': total_result['total_count'],
                            'oldest_record': oldest_result['oldest'],
                            'newest_record': newest_result['newest'],
                            'records_to_delete': old_result['old_count'],
                            'retention_days': self.retention_days[table],
                            'cutoff_date': cutoff_date
                        }
                    
                    return stats
                    
        except Exception as e:
            logger.error(f"Failed to get table statistics: {e}")
            return {}
    
    def cleanup_old_data(self, dry_run=False):
        """
        Clean up old telemetry data based on retention policies
        
        Args:
            dry_run (bool): If True, only calculate what would be deleted without actually deleting
            
        Returns:
            dict: Cleanup results and statistics
        """
        if self.cleanup_running:
            logger.warning("Cleanup already in progress, skipping...")
            return {'error': 'Cleanup already running'}
        
        self.cleanup_running = True
        
        try:
            cleanup_results = {
                'start_time': datetime.now(),
                'dry_run': dry_run,
                'tables_processed': {},
                'total_deleted': 0,
                'errors': []
            }
            
            logger.info(f"Starting database cleanup {'(DRY RUN)' if dry_run else '(LIVE)'}...")
            
            with get_db_connection() as conn:
                with conn.cursor() as cursor:
                    
                    for table, retention_days in self.retention_days.items():
                        try:
                            logger.info(f"Processing table: {table}")
                            
                            # Calculate cutoff date
                            cutoff_date = datetime.now() - timedelta(days=retention_days)
                            
                            # Check current table size
                            cursor.execute(f"SELECT COUNT(*) as count FROM `{table}`")
                            total_records = cursor.fetchone()['count']
                            
                            if total_records == 0:
                                logger.info(f"Table {table} is empty, skipping...")
                                continue
                            
                            # Safety check - don't process if below absolute minimum
                            min_required = self.min_records_to_keep[table]
                            if total_records <= min_required:
                                logger.info(f"Table {table} has only {total_records} records (minimum: {min_required}), skipping...")
                                cleanup_results['tables_processed'][table] = {
                                    'total_records_before': total_records,
                                    'records_deleted': 0,
                                    'status': 'protected_below_minimum',
                                    'retention_days': retention_days
                                }
                                continue
                            
                            # Get the latest N records to preserve regardless of age
                            latest_preserve = self.latest_records_to_preserve[table]
                            cursor.execute(f"""
                                SELECT id FROM `{table}` 
                                ORDER BY timestamp DESC 
                                LIMIT %s
                            """, (latest_preserve,))
                            preserve_ids = [str(row['id']) for row in cursor.fetchall()]
                            
                            if not preserve_ids:
                                logger.warning(f"No records found to preserve in {table}")
                                continue
                            
                            # Count records that can be safely deleted (old + not in latest N)
                            preserve_ids_str = ','.join(preserve_ids)
                            cursor.execute(f"""
                                SELECT COUNT(*) as count FROM `{table}` 
                                WHERE timestamp < %s 
                                AND id NOT IN ({preserve_ids_str})
                            """, (cutoff_date,))
                            records_to_delete = cursor.fetchone()['count']
                            
                            # Calculate what would remain after deletion
                            remaining_after = total_records - records_to_delete
                            
                            # Final safety check
                            if remaining_after < min_required:
                                # Adjust deletion to only remove the oldest while preserving minimum + latest
                                max_deletable = max(0, total_records - min_required)
                                if max_deletable > 0:
                                    # Delete oldest records while preserving both minimum count AND latest records
                                    delete_query = f"""
                                    DELETE FROM `{table}` 
                                    WHERE id IN (
                                        SELECT id FROM (
                                            SELECT id FROM `{table}` 
                                            WHERE id NOT IN ({preserve_ids_str})
                                            ORDER BY timestamp ASC 
                                            LIMIT %s
                                        ) as temp
                                    )
                                    """
                                    if not dry_run:
                                        cursor.execute(delete_query, (max_deletable,))
                                        actual_deleted = cursor.rowcount
                                    else:
                                        actual_deleted = max_deletable
                                    
                                    logger.info(f"Safety mode: Deleted {actual_deleted} oldest records from {table} (preserving minimum {min_required} + latest {latest_preserve})")
                                else:
                                    actual_deleted = 0
                                    logger.info(f"Skipping {table}: Would breach safety limits")
                            else:
                                # Safe deletion - remove old records but preserve latest N
                                delete_query = f"""
                                DELETE FROM `{table}` 
                                WHERE timestamp < %s 
                                AND id NOT IN ({preserve_ids_str})
                                """
                                if not dry_run:
                                    cursor.execute(delete_query, (cutoff_date,))
                                    actual_deleted = cursor.rowcount
                                else:
                                    actual_deleted = records_to_delete
                                
                                logger.info(f"Deleted {actual_deleted} old records from {table} (latest {latest_preserve} preserved)")
                            
                            # Record results
                            cleanup_results['tables_processed'][table] = {
                                'total_records_before': total_records,
                                'records_deleted': actual_deleted,
                                'cutoff_date': cutoff_date,
                                'retention_days': retention_days,
                                'latest_preserved': latest_preserve,
                                'final_count': total_records - actual_deleted
                            }
                            
                            cleanup_results['total_deleted'] += actual_deleted
                            
                            # Optimize table after deletion (only if not dry run)
                            if not dry_run and actual_deleted > 0:
                                logger.info(f"Optimizing table {table}...")
                                cursor.execute(f"OPTIMIZE TABLE `{table}`")
                            
                        except Exception as table_error:
                            error_msg = f"Error processing table {table}: {table_error}"
                            logger.error(error_msg)
                            cleanup_results['errors'].append(error_msg)
                    
                    # Commit all changes
                    if not dry_run:
                        conn.commit()
                        logger.info("Database cleanup committed successfully")
                    
            cleanup_results['end_time'] = datetime.now()
            cleanup_results['duration'] = (cleanup_results['end_time'] - cleanup_results['start_time']).total_seconds()
            
            logger.info(f"Database cleanup completed {'(DRY RUN)' if dry_run else '(LIVE)'}. "
                       f"Total records {'would be ' if dry_run else ''}deleted: {cleanup_results['total_deleted']}, "
                       f"Duration: {cleanup_results['duration']:.2f} seconds")
            
            return cleanup_results
            
        except Exception as e:
            error_msg = f"Database cleanup failed: {e}"
            logger.error(error_msg)
            return {'error': error_msg}
        
        finally:
            self.cleanup_running = False
    
    def get_cleanup_recommendations(self):
        """Analyze database and provide cleanup recommendations"""
        try:
            stats = self.get_table_stats()
            recommendations = {
                'urgent_cleanup_needed': False,
                'total_records': 0,
                'total_deletable': 0,
                'table_analysis': {},
                'recommended_action': 'no_action'
            }
            
            for table, table_stats in stats.items():
                total_records = table_stats['total_records']
                deletable_records = table_stats['records_to_delete']
                
                recommendations['total_records'] += total_records
                recommendations['total_deletable'] += deletable_records
                
                # Analyze table health
                analysis = {
                    'status': 'healthy',
                    'record_count': total_records,
                    'deletable_count': deletable_records,
                    'age_span_days': None,
                    'recommendation': 'no_action'
                }
                
                if table_stats['oldest_record'] and table_stats['newest_record']:
                    age_span = (table_stats['newest_record'] - table_stats['oldest_record']).days
                    analysis['age_span_days'] = age_span
                
                # Determine status and recommendations
                if total_records > 50000:  # Large table
                    analysis['status'] = 'large'
                    analysis['recommendation'] = 'cleanup_recommended'
                elif total_records > 100000:  # Very large table
                    analysis['status'] = 'very_large'
                    analysis['recommendation'] = 'cleanup_urgent'
                    recommendations['urgent_cleanup_needed'] = True
                elif deletable_records > total_records * 0.5:  # More than 50% old data
                    analysis['status'] = 'old_data_heavy'
                    analysis['recommendation'] = 'cleanup_beneficial'
                
                recommendations['table_analysis'][table] = analysis
            
            # Overall recommendation
            if recommendations['urgent_cleanup_needed']:
                recommendations['recommended_action'] = 'cleanup_urgent'
            elif recommendations['total_deletable'] > 10000:
                recommendations['recommended_action'] = 'cleanup_recommended'
            elif recommendations['total_deletable'] > 5000:
                recommendations['recommended_action'] = 'cleanup_beneficial'
            
            return recommendations
            
        except Exception as e:
            logger.error(f"Failed to generate cleanup recommendations: {e}")
            return {'error': str(e)}


class CleanupScheduler:
    """Automated cleanup scheduler for continuous operation"""
    
    def __init__(self, cleaner: DatabaseCleaner):
        self.cleaner = cleaner
        self.running = False
        self.scheduler_thread = None
        
    def start_scheduler(self):
        """Start the automated cleanup scheduler"""
        if self.running:
            logger.warning("Scheduler already running")
            return
        
        self.running = True
        
        # Schedule cleanup every 7 days at 3:00 AM
        schedule.every(7).days.at("03:00").do(self._scheduled_cleanup)
        
        # Schedule daily stats logging at 1:00 AM
        schedule.every().day.at("01:00").do(self._daily_stats_log)
        
        logger.info("Cleanup scheduler started:")
        logger.info("- Automatic cleanup: Every 7 days at 3:00 AM")
        logger.info("- Daily statistics: Every day at 1:00 AM")
        
        # Run scheduler in separate daemon thread
        def run_schedule():
            while self.running:
                try:
                    schedule.run_pending()
                    time.sleep(300)  # Check every 5 minutes
                except Exception as e:
                    logger.error(f"Scheduler error: {e}")
                    time.sleep(60)  # Wait 1 minute before retrying
        
        self.scheduler_thread = threading.Thread(target=run_schedule, daemon=True)
        self.scheduler_thread.start()
        
    def stop_scheduler(self):
        """Stop the automated cleanup scheduler"""
        self.running = False
        schedule.clear()
        logger.info("Cleanup scheduler stopped")
        
    def _scheduled_cleanup(self):
        """Internal method for scheduled cleanup execution"""
        try:
            logger.info("🧹 Starting scheduled database cleanup...")
            result = self.cleaner.cleanup_old_data(dry_run=False)
            
            if 'error' in result:
                logger.error(f"Scheduled cleanup failed: {result['error']}")
            else:
                logger.info(f"✅ Scheduled cleanup completed successfully. "
                           f"Deleted {result['total_deleted']} records in {result['duration']:.2f} seconds")
                
        except Exception as e:
            logger.error(f"Scheduled cleanup error: {e}")
    
    def _daily_stats_log(self):
        """Internal method for daily statistics logging"""
        try:
            stats = self.cleaner.get_table_stats()
            total_records = sum(table['total_records'] for table in stats.values())
            total_deletable = sum(table['records_to_delete'] for table in stats.values())
            
            logger.info(f"📊 Daily Database Stats - Total records: {total_records:,}, "
                       f"Deletable records: {total_deletable:,}")
            
            # Log per-table stats
            for table, table_stats in stats.items():
                logger.info(f"  {table}: {table_stats['total_records']:,} records "
                           f"({table_stats['records_to_delete']:,} deletable)")
                
        except Exception as e:
            logger.error(f"Daily stats logging error: {e}")


# Global instances
database_cleaner = DatabaseCleaner()
cleanup_scheduler = CleanupScheduler(database_cleaner)

def run_cleanup(dry_run=False):
    """
    Main function to run database cleanup
    
    Args:
        dry_run (bool): If True, only calculate what would be deleted
        
    Returns:
        dict: Cleanup results
    """
    return database_cleaner.cleanup_old_data(dry_run=dry_run)

def get_database_stats():
    """Get current database statistics"""
    return database_cleaner.get_table_stats()

def get_cleanup_recommendations():
    """Get cleanup recommendations based on current database state"""
    return database_cleaner.get_cleanup_recommendations()

def start_automated_cleanup():
    """Start the automated cleanup scheduler"""
    cleanup_scheduler.start_scheduler()

def stop_automated_cleanup():
    """Stop the automated cleanup scheduler"""
    cleanup_scheduler.stop_scheduler()

# For direct script execution
if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='HUST Solar Car Database Cleanup')
    parser.add_argument('--dry-run', action='store_true', help='Show what would be deleted without deleting')
    parser.add_argument('--stats', action='store_true', help='Show database statistics only')
    parser.add_argument('--recommendations', action='store_true', help='Show cleanup recommendations')
    
    args = parser.parse_args()
    
    if args.stats:
        stats = get_database_stats()
        print("📊 Database Statistics:")
        for table, table_stats in stats.items():
            print(f"  {table}: {table_stats['total_records']:,} records")
    elif args.recommendations:
        recs = get_cleanup_recommendations()
        print("🔍 Cleanup Recommendations:")
        print(f"  Total records: {recs['total_records']:,}")
        print(f"  Deletable records: {recs['total_deletable']:,}")
        print(f"  Recommended action: {recs['recommended_action']}")
    else:
        result = run_cleanup(dry_run=args.dry_run)
        if 'error' in result:
            print(f"❌ Cleanup failed: {result['error']}")
        else:
            action = "Would delete" if args.dry_run else "Deleted"
            print(f"✅ {action} {result['total_deleted']:,} records")
