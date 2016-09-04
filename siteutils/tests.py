# -*- coding: utf-8 -*-
# 
# Copyright 2013 XiaoMaiFeng


__author__ = "Bicheng Zhang"
__copyright__ = "Copyright 2013, XiaoMaiFeng"

from django.test import TestCase

from comment import action_from_comment


class CommentTestCase(TestCase):

	def setUp(self):
		pass

	def test_action_from_comment(self):
		action, amount = action_from_comment(u"我要买")

		self.assertEqual(action, 'buy')
