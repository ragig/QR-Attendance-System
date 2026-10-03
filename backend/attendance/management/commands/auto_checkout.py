from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta, datetime, time
from attendance.models import AttendanceRecord


class Command(BaseCommand):
    help = 'Automatically checkout employees at end of day if they have not checked out'

    def add_arguments(self, parser):
        parser.add_argument(
            '--end-of-day-hour',
            type=int,
            default=18,
            help='Hour of day to consider as end of day (24-hour format, default: 18)'
        )

    def handle(self, *args, **options):
        end_of_day_hour = options['end_of_day_hour']
        
        # Get current datetime in UTC
        now = timezone.now()
        
        # Find all open attendance records (checked in but not checked out)
        open_records = AttendanceRecord.objects.filter(check_out__isnull=True)
        
        checked_out_count = 0
        
        for record in open_records:
            # Convert check_in to local timezone for comparison
            check_in_local = timezone.localtime(record.check_in)
            now_local = timezone.localtime(now)
            
            # If check_in was on a previous day, auto-checkout at start of current day
            # If check_in was on current day but we're past end_of_day_hour, auto-checkout at end_of_day_hour
            if check_in_local.date() < now_local.date():
                # Employee checked in yesterday or earlier, checkout at midnight
                checkout_time = timezone.make_aware(
                    datetime.combine(
                        check_in_local.date() + timedelta(days=1),
                        time()
                    )
                )
            elif check_in_local.date() == now_local.date() and now_local.hour >= end_of_day_hour:
                # Employee checked in today and it's past end of day, checkout at end_of_day_hour
                checkout_time = timezone.make_aware(
                    datetime.combine(
                        now_local.date(),
                        time(hour=end_of_day_hour, minute=0, second=0)
                    )
                )
            else:
                # Not end of day yet for this record
                continue
            
            record.check_out = checkout_time
            record.save(update_fields=['check_out'])
            checked_out_count += 1
            
            self.stdout.write(
                self.style.SUCCESS(
                    f'✓ Auto-checked out {record.employee.username} '
                    f'(checked in: {check_in_local}, checked out: {timezone.localtime(checkout_time)})'
                )
            )
        
        if checked_out_count == 0:
            self.stdout.write(self.style.WARNING('No records needed auto-checkout'))
        else:
            self.stdout.write(
                self.style.SUCCESS(f'\n✓ Total auto-checked out: {checked_out_count} employee(s)')
            )
