#!/usr/bin/python
"""
 Copyright (C) International Business Machines Corp., 2005
 Author: Dan Smith <danms@us.ibm.com>

 This program is free software; you can redistribute it and/or modify
 it under the terms of the GNU General Public License as published by
 the Free Software Foundation; under version 2 of the License.

 This program is distributed in the hope that it will be useful,
 but WITHOUT ANY WARRANTY; without even the implied warranty of
 MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 GNU General Public License for more details.

 You should have received a copy of the GNU General Public License
 along with this program; if not, write to the Free Software
 Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA

"""

import sys
import commands
import os
import re
import time

from Xm import *
from Test import *
from config import *

BLOCK_ROOT_DEV = "hda"

def getDeviceModel():
    """Get the path to the device model based on
    the architecture reported in uname"""
    arch = os.uname()[4]
    if re.search("64", arch):
        return "/usr/lib64/xen/bin/qemu-dm"
    else:
        return "/usr/lib/xen/bin/qemu-dm"

def getDefaultKernel():
    """Get the path to the default DomU kernel"""
    dom0Ver = commands.getoutput("uname -r");
    domUVer = dom0Ver.replace("xen0", "xenU");
    
    return "/boot/vmlinuz-" + domUVer;

def getUniqueName():
    """Get a uniqueish name for use in a domain"""
    unixtime = int(time.time())
    test_name = sys.argv[0]
    test_name = re.sub("\.test", "", test_name)
    test_name = re.sub("[\/\.]", "", test_name)
    name = "%s-%i" % (test_name, unixtime)
    
    return name

def getRdPath():
    rdpath = os.environ.get("RD_PATH")
    if not rdpath:
        rdpath = "../../ramdisk"
    rdpath = os.path.abspath(rdpath)

    return rdpath

ParavirtDefaults = {"memory"       : 64,
                    "vcpus"        : 1,
                    "kernel"       : getDefaultKernel(),
                    "root"         : "/dev/ram0",
                    "ramdisk"      : getRdPath() + "/initrd.img"
                    }
HVMDefaults =      {"memory"       : 64,
                    "vcpus"        : 1,
                    "acpi"         : 0,
                    "apic"         : 0,
                    "disk"         : ["file:%s/disk.img,ioemu:%s,w!" %
                                   (getRdPath(), BLOCK_ROOT_DEV)],
                    "kernel"       : "/usr/lib/xen/boot/hvmloader",
                    "builder"      : "hvm",
                    "sdl"          : 0,
                    "vnc"          : 0,
                    "vncviewer"    : 0,
                    "nographic"    : 1,
                    "serial"       : "pty",
                    "device_model" : getDeviceModel()
                    }

if ENABLE_HVM_SUPPORT:
    configDefaults = HVMDefaults
else:
    configDefaults = ParavirtDefaults

class XenConfig:
    """An object to help create a xen-compliant config file"""
    def __init__(self):
        self.defaultOpts = {}

        # These options need to be lists
        self.defaultOpts["disk"] = []
        self.defaultOpts["vif"]  = []
        self.defaultOpts["vtpm"] = []

        self.opts = self.defaultOpts

    def toString(self):
        """Convert this config to a string for writing out
        to a file"""
        string = "# Xen configuration generated by xm-test\n"
        for k, v in self.opts.items():
            if isinstance(v, int):
                piece = "%s = %i" % (k, v)
            elif isinstance(v, list) and v:
                piece = "%s = %s" % (k, v)
            elif isinstance(v, str) and v:
                piece = "%s = \"%s\"" % (k, v)
            else:
                piece = None

            if piece:
                string += "%s\n" % piece

        return string

    def write(self, filename):
        """Write this config out to filename"""
        output = file(filename, "w")
        output.write(self.toString())
        output.close()

    def __str__(self):
        """When used as a string, we represent ourself by a config
        filename, which points to a temporary config that we write
        out ahead of time"""
        filename = "/tmp/xm-test.conf"
        self.write(filename)
        return filename

    def setOpt(self, name, value):
        """Set an option in the config"""
        if name in self.opts.keys() and isinstance(self.opts[name], list) and not isinstance(value, list):
                self.opts[name] = [value]
        else:
            self.opts[name] = value

    def appOpt(self, name, value):
        """Append a value to a list option"""
        if name in self.opts.keys() and isinstance(self.opts[name], list):
            self.opts[name].append(value)

    def getOpt(self, name):
        """Return the value of a config option"""
        if name in self.opts.keys():
            return self.opts[name]
        else:
            return None

    def setOpts(self, opts):
        """Batch-set options from a dictionary"""
        for k, v in opts.items():
            self.setOpt(k, v)

    def clearOpts(self, name=None):
        """Clear one or all config options"""
        if name:
            self.opts[name] = self.defaultOpts[name]
        else:
            self.opts = self.defaultOpts

class DomainError(Exception):
    def __init__(self, msg, extra="", errorcode=0):
        self.msg = msg
        self.extra = extra
        try:
            self.errorcode = int(errorcode)
        except Exception, e:
            self.errorcode = -1
            
    def __str__(self):
        return str(self.msg)


class XenDomain:

    def __init__(self, name=None, config=None):
        """Create a domain object.
        @param config: String filename of config file
        """

        if name:
            self.name = name
        else:
            self.name = getUniqueName()

        self.config = config

    def start(self):

        ret, output = traceCommand("xm create %s" % self.config)

        if ret != 0:
            raise DomainError("Failed to create domain",
                              extra=output,
                              errorcode=ret)

    def stop(self):
        prog = "xm"
        cmd = " shutdown "

        ret, output = traceCommand(prog + cmd + self.config.getOpt("name"))

        return ret

    def destroy(self):
        prog = "xm"
        cmd = " destroy "

        ret, output = traceCommand(prog + cmd + self.config.getOpt("name"))

        return ret

    def getName(self):
        return self.name

    def getId(self):
        return domid(self.getName());


class XmTestDomain(XenDomain):

    def __init__(self, name=None, extraConfig=None, baseConfig=configDefaults):
        """Create a new xm-test domain
        @param name: The requested domain name
        @param extraConfig: Additional configuration options
        @param baseConfig: The initial configuration defaults to use
        """
        config = XenConfig()
        config.setOpts(baseConfig)
        if extraConfig:
            config.setOpts(extraConfig)

        if name:
            config.setOpt("name", name)
        elif not config.getOpt("name"):
            config.setOpt("name", getUniqueName())

        XenDomain.__init__(self, config.getOpt("name"), config=config)

    def start(self):
        XenDomain.start(self)
        if ENABLE_HVM_SUPPORT:
            waitForBoot()

    def minSafeMem(self):
        return 32

if __name__ == "__main__":

    c = XenConfig()

    c.setOpt("foo", "bar")
    c.setOpt("foob", 1)
    opts = {"opt1" : 19,
            "opt2" : "blah"}
    c.setOpts(opts)

    c.setOpt("disk", "phy:/dev/ram0,hda1,w")
    c.appOpt("disk", "phy:/dev/ram1,hdb1,w")

    print str(c)



#    c.write("/tmp/foo.conf")

#    d = XmTestDomain();
#
#    d.start();

