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

from .ddciface import detect_monitors, set_brightness
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
  parser.add_argument(
    '--reinvoke',
    dest = 'reinvoke_delay',
    default = 0,
    type = int,
    help = 'Run repeating with the given delay'
  )

  return parser.parse_args()

def get_light_value(light_sensor, *, num_samples):
  readings = []
  for _ in range(num_samples):
    reading = light_sensor.get_value()

    # Sleep so we collect different samples
    print(reading)
    time.sleep(.5)

    readings.append(reading)

  readings.sort()
  return readings[num_samples // 2]

def _automatic_update(light_sensor, monitors):
  ambient_light = get_light_value(light_sensor, num_samples = 3)
  set_brightness(monitors, interpolate_brightness(ambient_light))

def main():
  args = parse_args()

  light_sensor = get_light_provider()
  error_message = light_sensor.init()
  if error_message != None:
    print(f"Light sensor setup failed: {error_message}.")
    exit(1)

  monitors = detect_monitors()

  if args.new_brightness != None:
    set_brightness(monitors, args.new_brightness)
    ambient_light = get_light_value(light_sensor, num_samples = 1)
    record_brightness(ambient_light, args.new_brightness)
  else:
    _automatic_update(light_sensor, monitors)

  while args.reinvoke_delay != 0:
    time.sleep(args.reinvoke_delay)
    _automatic_update(light_sensor, monitors)
