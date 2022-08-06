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

async def async_set_brightness(monitor_ids, monitor_brightness):
  for monitor_id in monitor_ids:
    args = [
      'ddcutil', 'setvcp', '-d', str(monitor_id), '10', str(monitor_brightness)
    ]
    print(' '.join(args))
    proc = await asyncio.create_subprocess_exec(*args)
    await proc.wait()

def set_brightness(monitor_brightness):
  asyncio.run(async_set_brightness([1, 2], monitor_brightness))
