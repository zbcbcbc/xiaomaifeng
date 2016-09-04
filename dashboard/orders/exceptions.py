# -*- coding: utf-8 -*-
# 
# Copyright 2013 XiaoMaiFeng


__author__ = "Bicheng Zhang"
__copyright__ = "Copyright 2013, XiaoMaiFeng"


class CreateOrderException(StandardError):
    '''
    建立订单的标准Exception
    保存内容为失败原因
    TODO: 添加通知买家或者卖家，建议动作
    '''
    def __init__(self, reason):
        self.reason = reason
        StandardError.__init__(self, reason)

    def __unicode__(self):
        return '%s:%s' % (self.__class__, self.reason)