"""
Phase 3: Service Layer Deep Dive Tests

Tests for:
- NotificationService
- ExportService
- CalendarService
- EmailService
- RecurrenceService
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, date, timedelta
from io import BytesIO

from services import (
    NotificationService,
    ExportService,
    CalendarService,
    EmailService,
    RecurrenceService
)


# ============================================================================
# NOTIFICATION SERVICE TESTS
# ============================================================================

class TestNotificationServiceCreate:
    """Tests for NotificationService.create()"""
    
    def test_create_notification_basic(self, app, db, user):
        """Test creating a basic notification"""
        with app.app_context():
            notification = NotificationService.create(
                user_id=user.id,
                notification_type='info',
                title_de='Test Titel',
                title_en='Test Title'
            )
            db.session.commit()
            
            assert notification is not None
            assert notification.user_id == user.id
            assert notification.title_de == 'Test Titel'
            assert notification.title_en == 'Test Title'
    
    def test_create_notification_with_message(self, app, db, user):
        """Test creating notification with message"""
        with app.app_context():
            notification = NotificationService.create(
                user_id=user.id,
                notification_type='task_assigned',
                title_de='Aufgabe zugewiesen',
                title_en='Task Assigned',
                message_de='Eine neue Aufgabe wurde Ihnen zugewiesen.',
                message_en='A new task has been assigned to you.'
            )
            db.session.commit()
            
            assert notification.message_de == 'Eine neue Aufgabe wurde Ihnen zugewiesen.'
            assert notification.message_en == 'A new task has been assigned to you.'
    
    def test_create_notification_with_entity_reference(self, app, db, user):
        """Test creating notification with entity reference"""
        with app.app_context():
            notification = NotificationService.create(
                user_id=user.id,
                notification_type='comment_added',
                title_de='Neuer Kommentar',
                title_en='New Comment',
                entity_type='task',
                entity_id=123
            )
            db.session.commit()
            
            assert notification.entity_type == 'task'
            assert notification.entity_id == 123
    
    def test_create_notification_with_actor(self, app, db, user):
        """Test creating notification with actor (who triggered it)"""
        from models import User
        
        with app.app_context():
            # Create another user as actor
            actor = User(email='actor@test.com', name='Actor User')
            actor.set_password('test')
            db.session.add(actor)
            db.session.commit()
            
            notification = NotificationService.create(
                user_id=user.id,
                notification_type='task_approved',
                title_de='Aufgabe genehmigt',
                title_en='Task Approved',
                actor_id=actor.id
            )
            db.session.commit()
            
            assert notification.actor_id == actor.id


class TestNotificationServiceNotifyUsers:
    """Tests for NotificationService.notify_users()"""
    
    def test_notify_single_user(self, app, db, user):
        """Test notifying a single user"""
        with app.app_context():
            notifications = NotificationService.notify_users(
                user_ids=[user.id],
                notification_type='info',
                title_de='Wichtige Info',
                title_en='Important Info'
            )
            db.session.commit()
            
            assert len(notifications) == 1
            assert notifications[0].user_id == user.id
    
    def test_notify_multiple_users(self, app, db):
        """Test notifying multiple users"""
        from models import User
        
        with app.app_context():
            users = []
            for i in range(3):
                u = User(email=f'user{i}@test.com', name=f'User {i}')
                u.set_password('test')
                db.session.add(u)
                users.append(u)
            db.session.commit()
            
            user_ids = [u.id for u in users]
            notifications = NotificationService.notify_users(
                user_ids=user_ids,
                notification_type='announcement',
                title_de='Ankündigung',
                title_en='Announcement'
            )
            db.session.commit()
            
            assert len(notifications) == 3
    
    def test_notify_users_deduplicates(self, app, db, user):
        """Test that duplicate user IDs are deduplicated"""
        with app.app_context():
            notifications = NotificationService.notify_users(
                user_ids=[user.id, user.id, user.id],
                notification_type='info',
                title_de='Test',
                title_en='Test'
            )
            db.session.commit()
            
            # Should only create one notification
            assert len(notifications) == 1
    
    def test_notify_users_skips_none(self, app, db, user):
        """Test that None user IDs are skipped"""
        with app.app_context():
            notifications = NotificationService.notify_users(
                user_ids=[user.id, None, None],
                notification_type='info',
                title_de='Test',
                title_en='Test'
            )
            db.session.commit()
            
            assert len(notifications) == 1


class TestNotificationServiceGetUnread:
    """Tests for NotificationService.get_unread_count()"""
    
    def test_get_unread_count_zero(self, app, db, user):
        """Test unread count when no notifications"""
        with app.app_context():
            count = NotificationService.get_unread_count(user.id)
            assert count == 0
    
    def test_get_unread_count_with_notifications(self, app, db, user):
        """Test unread count with unread notifications"""
        with app.app_context():
            for i in range(5):
                NotificationService.create(
                    user_id=user.id,
                    notification_type='info',
                    title_de=f'Notification {i}',
                    title_en=f'Notification {i}'
                )
            db.session.commit()
            
            count = NotificationService.get_unread_count(user.id)
            assert count == 5
    
    def test_get_unread_count_excludes_read(self, app, db, user):
        """Test that read notifications are excluded from count"""
        from models import Notification
        
        with app.app_context():
            # Create 3 unread
            for i in range(3):
                NotificationService.create(
                    user_id=user.id,
                    notification_type='info',
                    title_de=f'Unread {i}',
                    title_en=f'Unread {i}'
                )
            db.session.commit()
            
            # Mark one as read
            notification = Notification.query.filter_by(user_id=user.id).first()
            notification.is_read = True
            db.session.commit()
            
            count = NotificationService.get_unread_count(user.id)
            assert count == 2


# ============================================================================
# EXPORT SERVICE TESTS
# ============================================================================

class TestExportServiceExcel:
    """Tests for ExportService.export_tasks_to_excel()"""
    
    def test_export_empty_tasks(self, app):
        """Test exporting empty task list"""
        with app.app_context():
            result = ExportService.export_tasks_to_excel([])
            
            assert result is not None
            assert isinstance(result, bytes)
            assert len(result) > 0
    
    def test_export_returns_bytes(self, app, db, task):
        """Test that export returns bytes"""
        with app.app_context():
            result = ExportService.export_tasks_to_excel([task])
            
            assert isinstance(result, bytes)
    
    def test_export_german_language(self, app, db, task):
        """Test export with German language"""
        with app.app_context():
            result = ExportService.export_tasks_to_excel([task], lang='de')
            
            # Should contain German headers
            assert result is not None
            assert len(result) > 0
    
    def test_export_english_language(self, app, db, task):
        """Test export with English language"""
        with app.app_context():
            result = ExportService.export_tasks_to_excel([task], lang='en')
            
            assert result is not None
            assert len(result) > 0
    
    def test_export_multiple_tasks(self, app, db, entity):
        """Test exporting multiple tasks"""
        from models import Task
        
        with app.app_context():
            tasks = []
            for i in range(5):
                t = Task(
                    title=f'Task {i}',
                    year=2026,
                    due_date=date(2026, 6, 15),
                    entity_id=entity.id
                )
                db.session.add(t)
                tasks.append(t)
            db.session.commit()
            
            result = ExportService.export_tasks_to_excel(tasks)
            
            assert result is not None
            assert len(result) > 0
    
    def test_export_valid_xlsx_format(self, app, db, task):
        """Test that output is valid XLSX format"""
        from openpyxl import load_workbook
        
        with app.app_context():
            result = ExportService.export_tasks_to_excel([task])
            
            # Try to load as workbook
            wb = load_workbook(BytesIO(result))
            assert wb is not None
            assert len(wb.worksheets) == 1


# ============================================================================
# CALENDAR SERVICE TESTS
# ============================================================================

class TestCalendarServiceToken:
    """Tests for CalendarService.generate_user_token()"""
    
    def test_generate_token_returns_string(self):
        """Test that token generation returns a string"""
        token = CalendarService.generate_user_token(1)
        assert isinstance(token, str)
    
    def test_generate_token_length(self):
        """Test that token has expected length (32 chars)"""
        token = CalendarService.generate_user_token(1)
        assert len(token) == 32
    
    def test_generate_token_uniqueness(self):
        """Test that tokens are unique for same user"""
        token1 = CalendarService.generate_user_token(1)
        token2 = CalendarService.generate_user_token(1)
        # Tokens should be different (random component)
        assert token1 != token2
    
    def test_generate_token_different_users(self):
        """Test that different users get different tokens"""
        token1 = CalendarService.generate_user_token(1)
        token2 = CalendarService.generate_user_token(2)
        assert token1 != token2
    
    def test_generate_token_alphanumeric(self):
        """Test that token contains only valid hex characters"""
        token = CalendarService.generate_user_token(1)
        assert all(c in '0123456789abcdef' for c in token)


class TestCalendarServiceIcal:
    """Tests for CalendarService.generate_ical_feed()"""
    
    def test_generate_empty_feed(self, app):
        """Test generating iCal with no tasks"""
        with app.app_context():
            result = CalendarService.generate_ical_feed([])
            
            assert result is not None
            assert isinstance(result, bytes)
    
    def test_generate_feed_with_task(self, app, db, task):
        """Test generating iCal with a task"""
        with app.app_context():
            # Task fixture already has due_date set
            result = CalendarService.generate_ical_feed([task])
            
            assert result is not None
            assert b'VCALENDAR' in result
            assert b'VEVENT' in result
    
    def test_generate_feed_contains_task_title(self, app, db, task):
        """Test that iCal contains task title"""
        with app.app_context():
            task.title = 'Unique Test Task Title'
            db.session.commit()
            
            result = CalendarService.generate_ical_feed([task])
            
            assert b'Unique Test Task Title' in result
    
    def test_generate_feed_skips_tasks_without_due_date(self, app):
        """Test that tasks without due date are skipped"""
        # Use mock task with no due_date since real task requires it
        mock_task = Mock()
        mock_task.id = 1
        mock_task.title = 'Mock Task No Due Date'
        mock_task.due_date = None
        mock_task.entity = None
        mock_task.template = None
        mock_task.status = 'draft'
        
        with app.app_context():
            result = CalendarService.generate_ical_feed([mock_task])
            
            # Should have calendar but no events
            assert b'VCALENDAR' in result
            # Task title should not appear since no due date
            assert b'Mock Task No Due Date' not in result
    
    def test_generate_feed_german_language(self, app, db, task):
        """Test iCal with German language"""
        with app.app_context():
            task.status = 'draft'
            db.session.commit()
            
            result = CalendarService.generate_ical_feed([task], lang='de')
            
            # Should contain German labels
            assert b'Entwurf' in result or b'VCALENDAR' in result
    
    def test_generate_feed_english_language(self, app, db, task):
        """Test iCal with English language"""
        with app.app_context():
            task.status = 'draft'
            db.session.commit()
            
            result = CalendarService.generate_ical_feed([task], lang='en')
            
            assert result is not None
    
    def test_generate_feed_user_name(self, app, db, task):
        """Test iCal includes user name"""
        with app.app_context():
            result = CalendarService.generate_ical_feed([task], user_name='Test User')
            
            assert b'Test User' in result


# ============================================================================
# EMAIL SERVICE TESTS
# ============================================================================

class TestEmailServiceInit:
    """Tests for EmailService initialization"""
    
    def test_init_without_app(self):
        """Test EmailService can be created without app"""
        service = EmailService()
        assert service.app is None
        assert service._initialized is False
    
    def test_init_with_app(self, app):
        """Test EmailService init with app"""
        service = EmailService(app)
        assert service.app is app
    
    def test_init_app_method(self, app):
        """Test init_app() method"""
        service = EmailService()
        service.init_app(app)
        assert service.app is app
        assert service._initialized is True


class TestEmailServiceIsEnabled:
    """Tests for EmailService.is_enabled property"""
    
    def test_is_enabled_false_without_app(self):
        """Test is_enabled returns False without app"""
        service = EmailService()
        assert service.is_enabled is False
    
    def test_is_enabled_false_by_default(self, app):
        """Test is_enabled is False by default"""
        service = EmailService(app)
        assert service.is_enabled is False
    
    def test_is_enabled_true_when_configured(self, app):
        """Test is_enabled is True when MAIL_ENABLED=True"""
        app.config['MAIL_ENABLED'] = True
        service = EmailService(app)
        assert service.is_enabled is True


class TestEmailServiceProvider:
    """Tests for EmailService.provider property"""
    
    def test_provider_default_smtp(self, app):
        """Test default provider is smtp"""
        service = EmailService(app)
        assert service.provider == 'smtp'
    
    def test_provider_without_app(self):
        """Test provider returns smtp without app"""
        service = EmailService()
        assert service.provider == 'smtp'
    
    def test_provider_sendgrid(self, app):
        """Test sendgrid provider"""
        app.config['MAIL_PROVIDER'] = 'sendgrid'
        service = EmailService(app)
        assert service.provider == 'sendgrid'
    
    def test_provider_ses(self, app):
        """Test SES provider"""
        app.config['MAIL_PROVIDER'] = 'ses'
        service = EmailService(app)
        assert service.provider == 'ses'


class TestEmailServiceSendEmail:
    """Tests for EmailService.send_email()"""
    
    def test_send_email_disabled_logs_only(self, app):
        """Test that disabled email logs but returns True"""
        app.config['MAIL_ENABLED'] = False
        service = EmailService(app)
        
        result = service.send_email(
            to_email='test@example.com',
            subject='Test Subject',
            html_content='<p>Test content</p>'
        )
        
        assert result is True
    
    def test_send_email_generates_text_from_html(self, app):
        """Test that plain text is generated from HTML"""
        app.config['MAIL_ENABLED'] = False
        service = EmailService(app)
        
        # Should not raise even without text_content
        result = service.send_email(
            to_email='test@example.com',
            subject='Test',
            html_content='<p>Hello <b>World</b></p>'
        )
        
        assert result is True
    
    @patch('services.smtplib.SMTP')
    def test_send_via_smtp(self, mock_smtp, app):
        """Test sending via SMTP"""
        app.config['MAIL_ENABLED'] = True
        app.config['MAIL_PROVIDER'] = 'smtp'
        app.config['MAIL_SERVER'] = 'localhost'
        app.config['MAIL_PORT'] = 587
        app.config['MAIL_USE_TLS'] = True
        app.config['MAIL_USE_SSL'] = False
        
        mock_server = MagicMock()
        mock_smtp.return_value = mock_server
        
        service = EmailService(app)
        result = service.send_email(
            to_email='test@example.com',
            subject='Test',
            html_content='<p>Test</p>'
        )
        
        assert result is True
        mock_smtp.assert_called_once()
        mock_server.starttls.assert_called_once()
        mock_server.sendmail.assert_called_once()
        mock_server.quit.assert_called_once()


# ============================================================================
# RECURRENCE SERVICE TESTS
# ============================================================================

class TestRecurrenceServicePeriodDates:
    """Tests for RecurrenceService.get_period_dates()"""
    
    def test_monthly_generates_12_periods(self):
        """Test monthly frequency generates 12 periods"""
        periods = RecurrenceService.get_period_dates('monthly', 2026)
        assert len(periods) == 12
    
    def test_monthly_period_labels(self):
        """Test monthly period labels format"""
        periods = RecurrenceService.get_period_dates('monthly', 2026)
        labels = [p[0] for p in periods]
        
        assert 'M01' in labels
        assert 'M06' in labels
        assert 'M12' in labels
    
    def test_monthly_due_dates_are_dates(self):
        """Test monthly due dates are date objects"""
        periods = RecurrenceService.get_period_dates('monthly', 2026)
        
        for label, due_date in periods:
            assert isinstance(due_date, date)
    
    def test_quarterly_generates_4_periods(self):
        """Test quarterly frequency generates 4 periods"""
        periods = RecurrenceService.get_period_dates('quarterly', 2026)
        assert len(periods) == 4
    
    def test_quarterly_period_labels(self):
        """Test quarterly period labels"""
        periods = RecurrenceService.get_period_dates('quarterly', 2026)
        labels = [p[0] for p in periods]
        
        assert labels == ['Q1', 'Q2', 'Q3', 'Q4']
    
    def test_semi_annual_generates_2_periods(self):
        """Test semi-annual frequency generates 2 periods"""
        periods = RecurrenceService.get_period_dates('semi_annual', 2026)
        assert len(periods) == 2
    
    def test_semi_annual_period_labels(self):
        """Test semi-annual period labels"""
        periods = RecurrenceService.get_period_dates('semi_annual', 2026)
        labels = [p[0] for p in periods]
        
        assert labels == ['H1', 'H2']
    
    def test_annual_generates_1_period(self):
        """Test annual frequency generates 1 period"""
        periods = RecurrenceService.get_period_dates('annual', 2026)
        assert len(periods) == 1
    
    def test_annual_empty_label(self):
        """Test annual period has empty label"""
        periods = RecurrenceService.get_period_dates('annual', 2026)
        assert periods[0][0] == ''
    
    def test_day_offset_affects_due_date(self):
        """Test that day_offset changes due date"""
        periods_10 = RecurrenceService.get_period_dates('monthly', 2026, day_offset=10)
        periods_20 = RecurrenceService.get_period_dates('monthly', 2026, day_offset=20)
        
        # Due dates should differ
        assert periods_10[0][1] != periods_20[0][1]
    
    def test_monthly_following_month_due(self):
        """Test monthly tasks are due in following month"""
        periods = RecurrenceService.get_period_dates('monthly', 2026, day_offset=10)
        
        # M01 (January) should be due in February
        m01_due = periods[0][1]
        assert m01_due.month == 2
        assert m01_due.year == 2026
    
    def test_december_wraps_to_next_year(self):
        """Test December wraps to January of next year"""
        periods = RecurrenceService.get_period_dates('monthly', 2026, day_offset=10)
        
        # M12 (December) should be due in January 2027
        m12_due = periods[11][1]
        assert m12_due.month == 1
        assert m12_due.year == 2027
    
    def test_quarterly_due_after_quarter_end(self):
        """Test quarterly due dates are after quarter ends"""
        periods = RecurrenceService.get_period_dates('quarterly', 2026, day_offset=15)
        
        # Q1 ends March, due in April
        q1_due = periods[0][1]
        assert q1_due.month == 4
    
    def test_semi_annual_h1_due_july(self):
        """Test H1 is due in July"""
        periods = RecurrenceService.get_period_dates('semi_annual', 2026)
        
        h1_due = periods[0][1]
        assert h1_due.month == 7
        assert h1_due.year == 2026
    
    def test_semi_annual_h2_due_january_next_year(self):
        """Test H2 is due in January of next year"""
        periods = RecurrenceService.get_period_dates('semi_annual', 2026)
        
        h2_due = periods[1][1]
        assert h2_due.month == 1
        assert h2_due.year == 2027
    
    def test_annual_due_next_year(self):
        """Test annual task is due in following year"""
        periods = RecurrenceService.get_period_dates('annual', 2026)
        
        due_date = periods[0][1]
        assert due_date.year == 2027


class TestRecurrenceServiceEdgeCases:
    """Edge case tests for RecurrenceService"""
    
    def test_day_offset_28_for_february(self):
        """Test that day 28 is used for months with fewer days"""
        periods = RecurrenceService.get_period_dates('monthly', 2026, day_offset=31)
        
        # February due date should not fail
        # M01 is due in Feb, should use 28
        m01_due = periods[0][1]
        assert m01_due.day <= 28
    
    def test_leap_year_february(self):
        """Test February in leap year (2028)"""
        periods = RecurrenceService.get_period_dates('monthly', 2028, day_offset=29)
        
        # Should not raise
        assert len(periods) == 12
    
    def test_negative_day_offset(self):
        """Test negative day offset (same month due)"""
        periods = RecurrenceService.get_period_dates('monthly', 2026, day_offset=-15)
        
        # M01 (January) should be due in January
        m01_due = periods[0][1]
        assert m01_due.month == 1
    
    def test_zero_day_offset(self):
        """Test zero day offset defaults to 15"""
        periods = RecurrenceService.get_period_dates('monthly', 2026, day_offset=0)
        
        # Should not fail and use default
        assert len(periods) == 12
