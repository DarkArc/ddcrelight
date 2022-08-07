# Copyright 2022 Wyatt Childers
#
# This file is part of ddcrelight.
#
# ddcrelight is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# ddcrelight is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with ddcrelight.  If not, see <https://www.gnu.org/licenses/>.

import sys

from yoctopuce.yocto_api import YAPI, YRefParam
from yoctopuce.yocto_lightsensor import YLightSensor

class YoctoLightSensor:
  def __init__(self):
    self.light_sensor = None

  def init(self):
    err_msg = YRefParam()
    if YAPI.RegisterHub('127.0.0.1', err_msg) != YAPI.SUCCESS:
      return err_msg.value

    self.light_sensor = YLightSensor.FirstLightSensor()
    if self.light_sensor == None:
      return 'no light sensor could be found'

    return None

  def get_value(self):
    return self.light_sensor.get_currentValue()

def get_light_provider():
  return YoctoLightSensor()
