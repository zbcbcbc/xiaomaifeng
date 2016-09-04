__author__ = "Bicheng Zhang, Jian Chen"
__copyright__ = "Copyright 2013, XiaoMaiFeng"


import os
import sys

if __name__ == "__main__":
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "xiaomaifeng.settings")



    from django.core.management import execute_from_command_line

    execute_from_command_line(sys.argv)
