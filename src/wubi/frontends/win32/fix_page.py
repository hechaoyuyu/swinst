# Copyright (c) 2008 Agostino Russo
#
# Written by Agostino Russo <agostino.russo@gmail.com>
# Modified in 201108
# This file is part of Wubi the Win32 Ubuntu Installer.
#
# Wubi is free software; you can redistribute it and/or modify
# it under 5the terms of the GNU Lesser General Public License as
# published by the Free Software Foundation; either version 2.1 of
# the License, or (at your option) any later version.
#
# Wubi is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
#

from winui import ui
from page import Page
import os
import logging
import sys
log = logging.getLogger("WinuiFixPage")

class FixPage(Page):
    def on_init(self):
        Page.on_init(self)

        if self.info.needfix:
            wintitle = _("%s Uninstaller/Fixer") % self.info.previous_distro_name
            if self.info.uninstall_before_install:
                msg = _("Uninstallation/fixed required")
            else:
                msg = _("You are about to uninstall/Fix %s") % self.info.previous_distro_name
        else:
            wintitle = _("%s Uninstaller") % self.info.previous_distro_name
        #header
            if self.info.uninstall_before_install:
                 msg = _("Uninstallation required")
            else:
                 msg = _("You are about to uninstall %s") % self.info.previous_distro_name

        self.frontend.set_title(wintitle)
        self.insert_header(
            msg,
            "",
            "Ylmf OS-header.bmp")#% self.info.previous_distro_name[0:7])
            
        #navigation
        if self.info.needfix:# and self.info.registry:
            self.insert_navigation(_("Fix"), _("Uninstall"), _("Cancel"), default=3)
            self.navigation.button3.on_click = self.on_cancel
            self.navigation.button2.on_click = self.on_uninstall
            self.navigation.button1.on_click = self.run_fixboot
        else:
            self.insert_navigation(_("Uninstall"), _("Cancel"), default=2)
            self.navigation.button2.on_click = self.on_cancel
            self.navigation.button1.on_click = self.on_uninstall
        
        #Main control container
        self.insert_main()
        if self.info.uninstall_before_install:
            if self.info.inst == "uninstall.exe":
                msg = _("Do you want to uninstall %s?") % self.info.previous_distro_name
            else:
                msg = _("A previous installation was detected, it needs to be uninstalled before continuing")
        else:
            msg = _("Are you sure you want to uninstall?")

        FIXLABEL_HEIGHT = 60
        self.uninstall_label = ui.Label(
            self.main,
            40, 40, self.main.width - 80, 30 + FIXLABEL_HEIGHT,# x,y, width, height
            "")
        if self.info.needfix:
            msg = msg + _("\r\n\r\nNote: Yinst found that your system is full hope for recovery and advises you try to <fix> first !")
        self.uninstall_label.set_text(msg)

        self.backup_iso = ui.CheckButton(
            self.main, 80, 70, self.main.width - 120, 12,
            _("Backup the downloaded files (ISO)"))
        self.backup_iso.set_check(False)
        self.backup_iso.hide()
        #install_dir = os.path.join(self.info.previous_target_dir, 'install')
        ## Disabling ISO backup because download resume is not fully supported at the moment
        #~ if os.path.isdir(install_dir):
            #~ for f in os.listdir(install_dir):
                #~ if f.endswith('.iso'):
                    #~ self.backup_iso.set_check(True)
                    #~ self.backup_iso.show()
                    #~ break

    def on_uninstall(self):
        self.info.backup_iso = self.backup_iso.is_checked()        
        self.info.needfix = False
        self.info.fixed   = False
        self.frontend.stop()

    def on_cancel(self):
        self.frontend.cancel()

    def run_fixboot(self):
        '''
        just fix boot loader, except that "root.disk" ,all re-generates
        '''
        self.info.needfix = True
        self.info.fixed   = True # 修复过的标志
        self.frontend.stop()