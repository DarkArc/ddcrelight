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

import bisect
import fcntl
import json
import os

from datetime import datetime, timedelta

def _get_config_dir():
  if 'XDG_CONFIG_HOME' in os.environ:
    return os.path.join(os.environ['XDG_CONFIG_HOME'], 'ddcrelight')
  return os.path.join(os.environ['HOME'], '.config', 'ddcrelight')

def _get_history_file(*, mkdirs = False):
  conf_dir = _get_config_dir()
  if mkdirs and not os.path.exists(conf_dir):
    os.makedirs(conf_dir)
  return os.path.join(conf_dir, 'history.json')

def _get_init_history():
  return {
    'last_updated': datetime.now().isoformat(),
    'newest': [[100, 0]],
    'stable': [[100, 0]]
  }

def _get_history_mtime():
  history_file = _get_history_file()
  if not os.path.exists(history_file):
    return 0
  return os.path.getmtime(history_file)

def _load_history():
  history_file = _get_history_file()
  if not os.path.exists(history_file):
    return _get_init_history()
  with open(history_file, 'r+') as hist_file:
    try:
      fcntl.lockf(hist_file, fcntl.LOCK_EX)
      return json.load(hist_file)
    finally:
      fcntl.lockf(hist_file, fcntl.LOCK_UN)

def _save_history(history):
  history_file = _get_history_file(mkdirs = True)
  with open(history_file, 'w') as hist_file:
    try:
      fcntl.lockf(hist_file, fcntl.LOCK_EX)
      json.dump(history, hist_file)
    finally:
      fcntl.lockf(hist_file, fcntl.LOCK_UN)

def _get_stable_history(history):
  last_update = datetime.fromisoformat(history['last_updated'])
  if last_update + timedelta(minutes = 15) <= datetime.now():
    return history['newest']
  return history['stable']

def _update_history(history, ambient_light, monitor_brightness):
  '''This function is used to update the history object with new monitor
  brightness and ambient light values.

  At a high level, this function keeps two histories, a stable history, and
  the most recent history. This allows thoughtless brightness changes that do
  not corrupt the long term history.

  The actual history arrays are effectively tuples. The first value is the
  monitor brightness, the second value is the ambient light. Histories are
  sorted by the monitor brightness value, and then pruned to ensure ambient
  light level follows.

  For instance, we may start with something like the following:

    50 75 100
     5 10  20

  Then the user requests 60% brightness at level 4:

    50 60 75 100
     5  4 10  20

  This data now makes no sense as when the ambient light is higher (5) 50% is
  requested and when the light is lower (4) 60% is requested. Thus, the list
  is conceptually pruned to make sense:

    60 75 100
     4 10  20

  A similar procedure is performed when the user request say 60% brightness
  at level 25:

    50 60 75 100
     5 25 10  20

  The resulting data will be:

    50 60
     5 25
  '''

  # Get the stable history, and create a new history to modify.
  stable_history = _get_stable_history(history)
  new_history = []

  insert_pos = bisect.bisect_left(
    stable_history,
    monitor_brightness,
    key = lambda x: x[0]
  )

  # Insert any preceding elements that have a lower ambient light level.
  print(f"Insert pos: {insert_pos}")
  for element in stable_history[:insert_pos]:
    prev_ambient_light = element[1]
    if prev_ambient_light < ambient_light:
      new_history.append(element)

  # Insert the new light level.
  new_history.append([monitor_brightness, ambient_light])

  # If this wasn't an insertion at the end of the list, process the second half.
  if insert_pos < len(stable_history):
    # Check to see if there's a duplicate light level element, if so, skip it.
    half_two_start = insert_pos
    next_monitor_brightness = stable_history[insert_pos][0]
    if next_monitor_brightness == monitor_brightness:
      half_two_start += 1

    for element in stable_history[half_two_start:]:
      next_ambient_light = element[1]
      if next_ambient_light > ambient_light:
        new_history.append(element)

  print(json.dumps(stable_history))
  print(json.dumps(new_history))

  history['last_updated'] = datetime.now().isoformat()
  history['newest'] = new_history
  history['stable'] = stable_history

def record_brightness(ambient_light, monitor_brightness):
  print(f"Ambient: {ambient_light}, Monitor Brightness: {monitor_brightness}")

  history = _load_history()
  _update_history(history, ambient_light, monitor_brightness)
  _save_history(history)

def _interpolate_brightness(active_history, ambient_light):
  '''This function is used to find an appropriate monitor brightness for
  a given ambient light level.

  For instance, we may start with something like the following:

    50 75 100
     5 10  20

  Then the user's sensor reports an ambient light level of 6. We bisect finding
  an "insertion point" of 1 (i.e., in-between 50 and 75).

  So, we need to interpolate between ambient light 5 (50%) and ambient light 10
  (75%).
  '''

  light_level_guide = bisect.bisect_left(
    active_history,
    ambient_light,
    key = lambda x: x[1]
  )

  # If the light level guide is higher than any value previously seen, just use
  # the would be lower bound.
  if light_level_guide >= len(active_history):
    return active_history[light_level_guide - 1][0]

  # Check to see if there's anything to "go back to", if there's not, just use
  # the upper bound as the lower bound.
  prev_light_level_guide = light_level_guide - 1
  if prev_light_level_guide < 0:
    # Use the brightness exactly specified by the guide.
    return active_history[light_level_guide][0]

  lower_bound = active_history[prev_light_level_guide]
  upper_bound = active_history[light_level_guide]

  lower_ambient_bound = lower_bound[1]
  upper_ambient_bound = upper_bound[1]

  # Calculate the percentage between.
  adjusted_upper = upper_ambient_bound - lower_ambient_bound
  current_value = ambient_light - lower_ambient_bound

  relative_percentage = current_value / adjusted_upper

  # Calculate the amount of brightness that's available to be adjusted between
  # the high and low marks.
  lower_brightness = lower_bound[0]
  upper_brightness = upper_bound[0]

  adjustable_range = upper_brightness - lower_brightness

  # Create the adjusted value
  return lower_brightness + round(adjustable_range * relative_percentage)

def interpolate_brightness(ambient_light):
  history = _load_history()
  return _interpolate_brightness(history['newest'], ambient_light)

class BrightnessInterpolator:
  def __init__(self):
    self._history = _load_history()
    self._history_load_time = _get_history_mtime()

  def interpolate(self, ambient_light):
    # Potentially reload the history if the stored history time is before the
    # current history modification time.
    if self._history_load_time < _get_history_mtime():
      self._history = _load_history()

    return _interpolate_brightness(self._history['newest'], ambient_light)
