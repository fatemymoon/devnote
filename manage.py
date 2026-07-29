#!/usr/bin/env python
"""Django 명령어 실행 진입점.

`python manage.py runserver`, `migrate`, `createsuperuser` 등
모든 관리 명령이 이 파일을 통해 실행됩니다.
"""
import os
import sys


def main():
    """Run administrative tasks."""
    # 어떤 설정 파일을 쓸지 지정 (config/settings.py)
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError(
            "Couldn't import Django. Are you sure it's installed and "
            "available on your PYTHONPATH environment variable? Did you "
            "forget to activate a virtual environment?"
        ) from exc
    execute_from_command_line(sys.argv)


if __name__ == '__main__':
    main()
