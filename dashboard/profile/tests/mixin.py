# -*- coding: utf-8 -*-
# 
# Copyright 2013 XiaoMaiFeng


__author__ = "Bicheng Zhang"
__copyright__ = "Copyright 2013, XiaoMaiFeng"

import logging, pytz, datetime

from django.utils import timezone as djtimezone
from django.test import TestCase
from django.contrib.auth.models import User
from django.db import IntegrityError, DataError

from dashboard.profile.models import UserProfile, Membership, UserGroup

logging.disable(logging.WARNING)
