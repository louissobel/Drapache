

class Settings:
    pass
    
settings = Settings()

import dbapi
import util
import dbpy
import core

from frontends.httpserver import HttpDrapache

def set(in_settings):

    for attr in dir(in_settings):
        setattr(settings,attr,getattr(in_settings,attr))





#from frontends.twistd_resource import DrapacheTwistdResource

__all__ = ["util","dbapi","dbpy","frontends","dbserver"]