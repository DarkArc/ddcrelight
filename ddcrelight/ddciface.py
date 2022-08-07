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

import asyncio
import re

_BRIGHTNESS_REGEX = re.compile(r'current value = +([0-9]+)')

class DDCMonitor:
  def __init__(self, bus, model):
    self.bus = bus
    self.model = model
    self._brightness_cache = None

  async def _async_get_brightness(self):
    args = [
      'ddcutil', 'getvcp', '--bus', self.bus, '10'
    ]
    print(' '.join(args))
    proc = await asyncio.create_subprocess_exec(
      *args,
      stdout = asyncio.subprocess.PIPE,
      stderr = asyncio.subprocess.PIPE
    )
    stdout, stderr = await proc.communicate()
    if len(stderr.decode()) > 0:
      print('ddcutil brightness fetch failed.')
      exit(1)

    match = _BRIGHTNESS_REGEX.search(stdout.decode())
    if match == None:
      print('ddcutil brightness fetch failed.')
      exit(1)

    return int(match.group(1))

  async def async_get_brightness(self):
    # Attempt to use the brightness cache, and if that fails ask ddcutil.
    if self._brightness_cache == None:
      self._brightness_cache = await self._async_get_brightness()
    return self._brightness_cache

  def get_brightness(self):
    return asyncio.run(self.async_get_brightness())

  async def async_set_brightness(self, monitor_brightness):
    args = [
      'ddcutil', 'setvcp', '--bus', self.bus, '10', str(monitor_brightness)
    ]
    print(' '.join(args))
    proc = await asyncio.create_subprocess_exec(*args)
    await proc.wait()

    # Update the brightness cache.
    self._brightness_cache = monitor_brightness

  def set_brightness(self, monitor_brightness):
    asyncio.run(self.async_set_brightness(monitor_brightness))

async def async_set_brightness(monitors, new_brightness):
  awaitables = []
  for monitor in monitors:
    brightness = await monitor.async_get_brightness()
    if brightness == new_brightness:
      continue
    awaitables.append(monitor.async_set_brightness(new_brightness))
  await asyncio.gather(*awaitables)

def set_brightness(monitors, new_brightness):
  asyncio.run(async_set_brightness(monitors, new_brightness))

async def _run_detect():
  args = ['ddcutil', 'detect']
  print(' '.join(args))
  proc = await asyncio.create_subprocess_exec(
    *args,
    stdout = asyncio.subprocess.PIPE,
    stderr = asyncio.subprocess.PIPE
  )
  stdout, stderr = await proc.communicate()
  if len(stderr.decode()) > 0:
    print("ddcutil detection failed.")
    exit(1)

  return stdout.decode()

_I2C_BUS_REGEX = re.compile(r'I2C bus: +/dev/i2c-([0-9]+)', re.MULTILINE)
_MODEL_REGEX = re.compile(r'Model: +(.*)', re.MULTILINE)

async def async_detect_monitors():
  raw_output = await _run_detect()

  buses = _I2C_BUS_REGEX.findall(raw_output)
  models = _MODEL_REGEX.findall(raw_output)

  if len(buses) == 0:
    print('No compatible monitors found.')
    exit(1)

  if len(buses) != len(models):
    print('Monitor bus and model decode failed.')
    exit(1)

  monitors = []
  for idx in range(len(buses)):
    bus = buses[idx]
    model = models[idx]
    monitors.append(DDCMonitor(bus, model))

  return monitors

def detect_monitors():
  return asyncio.run(async_detect_monitors())
