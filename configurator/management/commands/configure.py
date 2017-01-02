#  -*- coding: utf-8 -*-
"""
Copyright 2016 S. Poss
"""
from django.core.management.base import BaseCommand, CommandError
import random

__author__ = 'sposs'


class Command(BaseCommand):
    base_path = "/opt"
    virtual_envs_path = "/opt/virtualenvs"
    secret_key = ''.join(
        [random.SystemRandom().choice('abcdefghijklmnopqrstuvwxyz0123456789'
                                      '!@#$%^&*(-_=+)') for _ in range(50)])

    def add_arguments(self, parser):
        parser.add_argument("project", help="project name")
        parser.add_argument("-p", "--path", dest="base_path",
                            help="The root path", default=self.base_path)
        parser.add_argument("-v", "--virtualenv", dest="virtenv",
                            help="The path to the virtualenv",
                            default=self.virtual_envs_path)

    def handle(self, *args, **options):
        y = raw_input("Continue? [y,n] > ")
        if y.lower() not in ["y", "yes"]:
            raise CommandError("Canceled before ending.")
