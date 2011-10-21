# Copyright (c) 2008 Agostino Russo
#
# Written by Agostino Russo <agostino.russo@gmail.com>
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
#condig=utf-8
from winui import ui
from page import Page
from wubi.backends.common.mappings import reserved_usernames, lang_country2linux_locale
import os
import logging
import sys
import re
import md5
import gettext

log = logging.getLogger("WinuiInstallationPage")
if sys.version.startswith('2.3'):
    from sets import Set as set


class AccessibilityPage(Page):
    def add_controls_block(self, parent, left, top, bmp, label, is_listbox):
        picture = ui.Bitmap(
            parent,
            left, top + 6, 32, 32)
        picture.set_image(
            os.path.join(unicode(str(self.info.image_dir), 'mbcs'), unicode(str(bmp), 'mbcs')))
        label = ui.Label(
            parent,
            left + 32 + 10, top, 150, 16,
            label)
        if is_listbox:
            combo = ui.ComboBox(
                parent,
                left + 32 + 10, top + 20, 150, 200,
                "")
        else:
            combo = None
        return picture, label, combo

    def populate_distro_list(self):
        if self.info.cd_distro:
            distros = [self.info.cd_distro.name]
        elif self.info.iso_distro:
            distros = [self.info.iso_distro.name]
        else:
            distros = []
            for distro in self.info.distros:
                if distro.name not in distros:
                    distros.append(distro.name)
        for distro in distros:
            self.distro_list.add_item(distro)
        self.distro_list.set_value(distros[0])
        self.on_distro_change()

    def on_distro_change(self):
        distro_name = str(self.distro_list.get_text())
        #print "distro_name === %s,info.arch === %s" %(distro_name,self.info.arch)
        self.info.distro = self.info.distros_dict.get((distro_name.lower(), self.info.arch))
       
        if not self.info.distro and self.info.arch == 'amd64':
            self.info.distro = self.info.distros_dict.get((distro_name.lower(), 'i386'))

        self.frontend.set_title(_("%s Installer") % self.info.distro.name)
        bmp_file = "%s-header.bmp" % self.info.distro.name
        self.header.image.set_image(os.path.join(unicode(str(self.info.image_dir), 'mbcs'), unicode(str(bmp_file), 'mbcs')))
        self.header.title.set_text(_("You are about to install %(distro)s-%(version)s") % dict(distro=self.info.distro.name, version=self.info.version) + " Livecd")
        icon_file = "%s.ico" % self.info.distro.name
        self.frontend.set_icon(os.path.join(unicode(str(self.info.image_dir), 'mbcs'), unicode(str(icon_file), 'mbcs')))
        if not self.info.skip_memory_check:
            if self.info.total_memory_mb < self.info.distro.min_memory_mb:
                message = _("%(min_memory)sMB of memory are required for installation.\nOnly %(total_memory)sMB are available.\nThe installation may fail in such circumstances.\nDo you wish to continue anyway?")
                message = message % dict(min_memory=int(self.info.distro.min_memory_mb), total_memory=int(self.info.total_memory_mb))
                if not self.frontend.ask_confirmation(message):
                    self.application.quit()
                else:
                    self.info.skip_memory_check = True
        self.populate_drive_list()

    def populate_drive_list(self):
        self.target_drive_list = ui.ComboBox(
                self.main,
                24 + 32 + 10, 24 + 20, 150, 200,
                "")
        #分区发生变化
        self.target_drive_list.on_change = self.on_drive_change

        tmpsize = min_space_mb = self.info.distro.max_iso_size/(1024**2)+ 100
        tmptext = None
        self.drives_gb = []
        for drive in self.info.drives:
            if drive.type not in ['removable', 'hd']:
                continue

            drive_space_mb = int(drive.free_space_mb/1024) * 1000
            if self.info.skip_size_check or drive_space_mb > min_space_mb:
                if drive_space_mb > tmpsize:
                    tmpsize = drive_space_mb
                    tmptext = drive.path + " " + _("(%sGB free)") % (tmpsize/1000)
                text = drive.path + " "
                text += _("(%sGB free)") % (drive_space_mb/1000)
                self.drives_gb.append(text)
                self.target_drive_list.add_item(text)
        if tmptext:
            try:
                self.target_drive_list.set_value(tmptext)
            except:
                self.target_drive_list.set_value(self.drives_gb[0])
        else:
            try:
                self.target_drive_list.set_value(self.drives_gb[0])
            except:
                self.target_drive_list.set_value(None)
        self.on_drive_change()

    def select_default_drive(self):
        drive = self.info.target_drive
        if drive:
            Drive = self.info.drives[0].__class__
            if isinstance(drive, Drive):
                pass
            else:
                drive = self.info.drives_dict.get(drive[:2].lower())
        drive_text = self.drives_gb[0]
        if drive:
            for d in self.drives_gb:
                if d.startswith(drive.path):
                    drive_text = d
        self.target_drive_list.set_value(drive_text)
        self.on_drive_change()

    #初始化入口??
    def on_init(self):
        Page.on_init(self)
        #shorter list
        self.language2lang_country = {
            _("Chinese (CN)"): "zh_CN",
            _("Chinese (TW)"): "zh_TW",
            _("English (US)"): "en_US",
            }
        self.lang_country2language = dict([(v,k) for k,v in self.language2lang_country.items()])
        #header
        #The title and image are overridden in on_distro_change, the following are stubs
        self.insert_header(
            "Installing",
            _("In Livecd,you can try and decide whether to install Ylmf OS.Please select a partition,and the rest of the space must be greater than 1G"),
            "header.bmp")

        #navigation
        self.insert_navigation(_("Rollback"), _("Install"), _("Cancel"), default=2)
        self.navigation.button3.on_click = self.on_cancel
        self.navigation.button2.on_click = self.on_install
        self.navigation.button1.on_click = self.on_rollback

        #Main control container
        self.insert_main()
        h=24
        w=150

        #目标驱动器选择
        picture, label, self.target_drive_list = self.add_controls_block(
            self.main, h, h,
            "install.bmp", _("Installation drive:"), False)
        

        #桌面环境选择
        picture, label, self.distro_list = self.add_controls_block(
            self.main, h, h*4,
            "desktop.bmp", _("Desktop environment:"), True)
        self.populate_distro_list()
        self.distro_list.on_change = self.on_distro_change

        #语言选择
        picture, label, self.language_list = self.add_controls_block(
            self.main, h*4 + w, h,
            "language.bmp", _("Language:"), True)
        self.populate_language_list()
        self.language_list.on_change = self.on_language_change

    def populate_language_list(self):
        languages = self.language2lang_country.keys()
        languages.sort()
        for language in languages:
            self.language_list.add_item(language)
        language = self.lang_country2language.get(self.info.language, None)
        if not language and self.info.windows_language in self.language2lang_country.keys():
            language = self.info.windows_language
        if not language:
            language = self.lang_country2language.get("en_US")
        self.language_list.set_value(language)

    def on_language_change(self):
        language = self.language_list.get_text()
        language1 = self.language2lang_country.get(language, None)
        language2 = language1 and language1.split('_')[0]
        language3 = lang_country2linux_locale.get(self.info.language, None)
        language4 = language3 and language3.split('.')[0]
        language5 = language4 and language4.split('_')[0]
        #print language1, language2, language3, language4, language5
        translation = gettext.translation(self.info.application_name, localedir=self.info.translations_dir, languages=[language1, language2, language3, language4, language5])
        translation.install(unicode=True)

    def on_drive_change(self):
        self.info.target_drive = self.get_drive()
        #print "target_drive ===",self.info.target_drive

    def get_drive(self):
        if not self.target_drive_list.get_text():
            log.error("** get drive drive **")
            return None        
        target_drive = self.target_drive_list.get_text()[:2].lower()
        drive = self.info.drives_dict.get(target_drive)
        return drive
        
    def on_rollback(self):
        self.frontend.show_page(self.frontend.installation_page)

    def on_cancel(self):
        self.frontend.cancel()

    def on_install(self):
        drive = self.get_drive()
        language = self.language_list.get_text()
        language = self.language2lang_country.get(language, None)
        locale = lang_country2linux_locale.get(language, self.info.locale)
        self.info.target_drive = drive
        self.info.language = language
        self.info.locale = locale
        self.info.flag = False
        self.frontend.stop()
