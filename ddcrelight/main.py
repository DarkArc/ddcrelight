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
import signal
import time

from .ddciface import detect_monitors, adjust_brightness
from .lightai import record_brightness, BrightnessInterpolator
from .lightsensor import get_light_provider

def _get_light_sensor():
  light_sensor = get_light_provider()
  error_message = light_sensor.init()
  if error_message != None:
    print(f"Light sensor setup failed: {error_message}.")
    exit(1)

  return light_sensor

def run_daemon(args):
  light_sensor = _get_light_sensor()
  monitors = detect_monitors()
  interpolator = BrightnessInterpolator()

  while True:
    ambient_light = light_sensor.get_value()
    target_brightness = interpolator.interpolate(ambient_light)

    if not adjust_brightness(monitors, target_brightness):
      time.sleep(5)

def set_brightness(args):
  light_sensor = _get_light_sensor()
  ambient_light = light_sensor.get_value()

  if not (0 <= args.new_brightness and args.new_brightness <= 100):
    print('new_brightness must be between 0 and 100')
    exit(1)

  record_brightness(ambient_light, args.new_brightness)

def _add_parse_daemon(subparsers):
  parser = subparsers.add_parser(
    'daemon',
    help = 'run the daemon'
  )
  parser.set_defaults(handler = run_daemon)

def _add_parse_set_brightness(subparsers):
  parser = subparsers.add_parser(
    'set-brightness',
    help = 'update the brightness database for the current light level'
  )
  parser.add_argument(
    'new_brightness',
    type = int,
    help = 'the new brightness value'
  )
  parser.set_defaults(handler = set_brightness)

def parse_args():
  parser = argparse.ArgumentParser(
    description = 'Update monitor brightness intelligently.'
  )
  parser.set_defaults(handler = lambda args: print('Select a sub-command'))

  subparsers = parser.add_subparsers(help = 'sub-command help')
  _add_parse_daemon(subparsers)
  _add_parse_set_brightness(subparsers)

  return parser.parse_args()

def die(signum, frame):
  print('\rTerminating gracefully...')
  exit()

def register_signal_handlers():
  signal.signal(signal.SIGINT, die)
  signal.signal(signal.SIGTERM, die)

def main():
  register_signal_handlers()

  args = parse_args()
  args.handler(args)
