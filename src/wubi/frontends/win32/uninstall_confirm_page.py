# To change this template, choose Tools | Templates
# and open the template in the editor.
# Copyright (c) 2008 Agostino Russo
#
#
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
log = logging.getLogger("WinuiUninstallConfirmPage")

class UninstallConfirmPage(Page):

    def on_init(self):
        Page.on_init(self)
        self.frontend.set_title(_("%s Uninstaller") % self.info.previous_distro_name)

        #header
        msg = _("You Sure ?")
        self.insert_header(
            msg,
            "",
            "Ylmf OS-header.bmp")#% self.info.previous_distro_name[0:7])

        #navigation
        self.insert_navigation(_("Uninstall"), _("Cancel"), default=2)
        self.navigation.button2.on_click = self.on_cancel
        self.navigation.button1.on_click = self.on_continue

        msg = _("Yinst will remove below directroys, if them contain your\
        usefull things ,please click <cancel> and backup them")

        msg = msg + "\r\n\r\n" + self.info.previous_target_dir
        if self.info.pre_install_path and os.path.isdir(self.info.pre_install_path)\
            and self.info.previous_target_dir.lower() != self.info.pre_install_path.lower():
                msg = msg + "\r\n" + self.info.pre_install_path # 这里确定要不要增加X:\ylmfos-loop
        if self.info.pre_install_path2 and os.path.isdir(self.info.pre_install_path2)\
            and self.info.previous_target_dir.lower() != self.info.pre_install_path2.lower():
                msg = msg + "\r\n" + self.info.pre_install_path2 # 这里确定要不要增加X:\ylmfos-livecd
        
        #Main control container
        self.insert_main()
        
        self.uninstall_label = ui.Label(
            self.main,
            40, 40, self.main.width - 80, 80,# x,y, width, height
            "")
        self.uninstall_label.set_text(msg)

    def on_continue(self):
        self.frontend.stop()

    def on_cancel(self):
        self.frontend.cancel()

