# OctoPrint-PortRetry

When the printer is disconnected, this plugin will try to reconnect the printer on a configurable interval

Comes in handy when running octoprint in an lxc, and the port device is available even if the printer is not connected. In this case PortLister will not work, to connect to the printer when it comes online

Should also work to solve the issue with Prusa printers that don't remove the serial port from the system when powering down

## Setup

Install via the bundled [Plugin Manager](https://plugins.octoprint.org/)
or manually using this URL:

    https://github.com/vehystrix/OctoPrint-PortRetry/archive/master.zip

## Configuration

In ~/.octoprint/config.yaml, the interval can be configured to something other than the default 5 seconds.
There is also a settings page in the webui
```
plugins:
  portretry:
    interval: 5
```

**This plugin will do nothing if the serial port in Serial Connection > General is set to `AUTO`, you will need to specify a port there for this plugin to work!** Or in ~/.octoprint/config.yaml:
```
serial:
  port: /dev/ttyUSB0
```
When you change the port from `AUTO` to something else, you will need to connect to the printer manually first (or restart the server).

## Misc

To keep your printer working without having to reboot the lxc every time you turn it on, I'm putting what I found here so that it may be of use for someone.

I found the idea [here](https://monach.us/automation/connecting-zwave-stick-under-lxc/) (instructions will be for my setup with the lxc id 108 and the serial port /dev/ttyUSB0)

* Check the info on the serial port 
  ```
  $ ls -l /dev/ttyUSB0
  crw-rw---- 1 root dialout 188, 0 Sep 13 20:32 /dev/ttyUSB0
  ```
* Create the folder `/var/lib/lxc/108/devices`
* Run `cd /var/lib/lxc/108/devices && mknod -m 660 ttyUSB0 c 188 0` to create an always available device linking to the same device as `/dev/ttyUSB0`
* In the lxc config, add the newly created device to the lxc instead of `/dev/ttyUSB0`  
  Also remember to map the dialout group (if your lxc is unprivileged), it has gid 20 for me
  ```
  lxc.cgroup.devices.allow: c 188:* rwm
  lxc.mount.entry: /var/lib/lxc/108/devices/ttyUSB0 dev/ttyUSB0 none bind,optional,create=file
  lxc.idmap: u 0 100000 20
  lxc.idmap: g 0 100000 20
  lxc.idmap: u 20 20 1
  lxc.idmap: g 20 20 1
  lxc.idmap: u 21 100021 65515
  lxc.idmap: g 21 100021 65515
  ```