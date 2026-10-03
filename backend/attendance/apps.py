from django.apps import AppConfig
import sys


class AttendanceConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'attendance'

    def ready(self):
        """Initialize the APScheduler when Django starts"""
        from apscheduler.schedulers.background import BackgroundScheduler
        from django.conf import settings
        import logging

        # Configure logging to ensure output appears
        logging.basicConfig(level=logging.INFO, stream=sys.stdout)
        logger = logging.getLogger(__name__)
        
        # Check if scheduler is already running to avoid duplicate instances
        if not hasattr(settings, '_scheduler_started'):
            try:
                scheduler = BackgroundScheduler()
                
                # Schedule auto-checkout every day at 18:00 (6 PM) UTC
                scheduler.add_job(
                    self.run_auto_checkout,
                    'cron',
                    hour=18,
                    minute=0,
                    id='auto_checkout_job',
                    name='Auto-checkout employees at end of day',
                    replace_existing=True,
                )
                
                scheduler.start()
                settings._scheduler_started = True
                print('[OK] Auto-checkout scheduler started successfully')
                logger.info('[OK] Auto-checkout scheduler started successfully')
            except Exception as e:
                print(f'Failed to start auto-checkout scheduler: {e}')
                logger.error(f'Failed to start auto-checkout scheduler: {e}')
                import traceback
                traceback.print_exc()

    @staticmethod
    def run_auto_checkout():
        """Run the auto-checkout management command"""
        from django.core.management import call_command
        import logging
        import sys

        logger = logging.getLogger(__name__)
        try:
            msg = 'Running auto-checkout task...'
            print(msg)
            logger.info(msg)
            call_command('auto_checkout', end_of_day_hour=18)
        except Exception as e:
            err_msg = f'Error during auto-checkout: {e}'
            print(err_msg)
            logger.error(err_msg)
            import traceback
            traceback.print_exc()

