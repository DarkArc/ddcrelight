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

import argparse
import time

from .ddciface import set_brightness
from .lightai import record_brightness, interpolate_brightness
from .lightsensor import get_light_provider

def parse_args():
  parser = argparse.ArgumentParser(
    description = 'Update monitor brightness intelligently.'
  )
  parser.add_argument(
    'new_brightness',
    nargs = '?',
    type = int,
    help = (
      'the new brightness level (if not provided, the brightness will be '
      'adjusted based on the current light levels and previous usage).'
    )
  )

  return parser.parse_args()

def _get_light_value(light_sensor):
  ambient_light = light_sensor.get_value()

  if ambient_light == -1:
    print('Light level read failed.')
    exit(1)

  return ambient_light

def get_average_light_value(light_sensor, *, num_samples):
  total_light = 0
  for _ in range(num_samples):
    reading = _get_light_value(light_sensor)

    # Sleep so we collect different samples
    print(reading)
    time.sleep(.25)

    total_light += reading

  return total_light / num_samples

def main():
  args = parse_args()

  light_sensor = get_light_provider()
  error_message = light_sensor.init()
  if error_message != None:
    print(f"Light sensor setup failed: {error_message}.")
    exit(1)

  ambient_light = get_average_light_value(light_sensor, num_samples = 3)

  if args.new_brightness:
    set_brightness(args.new_brightness)
    record_brightness(ambient_light, args.new_brightness)
  else:
    set_brightness(interpolate_brightness(ambient_light))
