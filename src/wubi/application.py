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

import os
import sys
import tempfile
from optparse import OptionParser
#TBD import modules as required at runtime
from wubi.backends.win32 import WindowsBackend
from wubi.frontends.win32 import WindowsFrontend
import logging
from wubi.backends.common.utils import rm_tree
import wubi.backends.common.backend
from winui import ui
log = logging.getLogger("")


class Wubi(object):

    def __init__(self, application_name, version, revision, root_dir):
        self.frontend = None
        self.info = Info()
        self.info.root_dir = root_dir
        self.info.force_exit = False
        self.info.version = version
        self.info.revision = revision
        self.info.application_name = application_name
        self.info.version_revision = "%s-rev%s" % (self.info.version, self.info.revision)
        self.info.full_application_name = "%s-%s-rev%s" % (self.info.application_name, self.info.version, self.info.revision)
        self.info.full_version = "%s %s rev%s" % (self.info.application_name, self.info.version, self.info.revision)
        self.info.flag = True

    def run(self):
        self.info.quitting = False
        try:
            self.parse_commandline_arguments()
            self.set_logger()
            log.info("=== " + self.info.full_version + " ===")
            log.debug("Logfile is %s" % self.info.log_file)
            #self.info.inst = sys.argv[1][-14:-1]
	    tmppath = os.path.basename(sys.argv[1])
            if tmppath[-1] == "\"":
                self.info.inst = tmppath[:-1]
            else:
                self.info.inst = tmppath	
            log.debug("inst = %s" % self.info.inst)
            self.backend = self.get_backend()
            self.backend.fetch_basic_info()
            self.select_task()
        except Exception, err:
            if self.info.quitting:
                log.info("Quitting application")
            else:
                log.exception(err)
                if self.frontend:
                    error_messages = "\n".join([e for e in err.args if isinstance(e, basestring)])
                    self.frontend.show_error_message(_("An error occurred:\n\n%(error)s\n\nFor more information, please see the log file: %(log)s") % dict(error=error_messages, log=self.info.log_file))
            return

    def quit(self):
        '''
        Sends quit signal to frontend if possible,
        since quit signals are originated by the frontend anyway
        '''
        log.debug("application.quit")
        if self.frontend and callable(self.frontend.quit):
            self.frontend.quit()
        else:
            self.on_quit()

    def on_quit(self):
        '''
        Receives quit notification from frontend, or self.quit()
        sys.exit cannot be used, because it also terminates the launching process
        '''
        log.debug("application.on_quit")
        self.info.quitting = True
        if self.info.force_exit:
            log.debug("Forceful exit")
        log.info("sys.exit")
        sys.exit(0)


    def get_backend(self):
        '''
        Gets the appropriate backend for the system
        The backend contains system-specific libraries for tasks such as
        Information fetching, installation, and disinstallation
        '''
        #TBD do proper detection of backend
        return WindowsBackend(self)

    def get_frontend(self):
        '''
        Gets the appropriate frontend for the system
        '''
        #TBD do proper detection of frontend
        if self.frontend:
            return self.frontend
        if self.info.use_frontend:
            raise NotImplemented
        else:
            Frontend = WindowsFrontend
        return Frontend(self)

    def select_task(self):
        '''
        Selects the appropriate task to perform and runs it
        '''
        #print "run_task ===",self.info.run_task
        if self.info.run_task == "install":
            self.run_installer()
        elif self.info.run_task == "cd_boot":
            self.run_cd_boot()
        elif self.info.run_task == "uninstall":
            self.run_uninstaller()
        elif self.info.run_task == "show_info":
            self.show_info()
        elif self.info.run_task == "reboot":
            self.reboot()
        elif self.info.cd_path or self.info.run_task == "cd_menu":
            self.run_cd_menu()
        else:
            self.run_installer()
        self.quit()

    def run_fixboot(self):
        '''
        在root.disk文件存在的情况下,补全其它相关文件,如vmlinuz,initrd.img以及修复引导,恢复注册信息等
        '''
        log.info("Found previous installation directory %s" % self.info.pre_install_path)
        # Note: 不像正常安裝,有部分self.info內的鍵和值需要按实际情况补上,避免程序数据使用异常
        log.info("Running the Fixer...")
        self.frontend = self.get_frontend()
        log.info("fixboot -- self.info.arch = %s " % self.info.arch)
        log.info("fixboot -- self.info.distro = %s" % self.info.distro)
        if not self.info.distro:
            self.info.distro = self.info.distros_dict.get(('Ylmf OS'.lower(), 'i386'))
            log.info("self.info.distros_dict.get(('Ylmf OS'.lower(), 'i386')) = %s " % self.info.distros_dict.get(('Ylmf OS'.lower(), 'i386')))
        log.info("self.info.distros_dict.get(('Ylmf OS'.lower(), 'amd64')) = %s " % self.info.distros_dict.get(('Ylmf OS'.lower(), 'amd64')))
        self.info.target_dir = self.info.pre_install_path
        self.info.icon = os.path.join(self.info.target_dir, self.info.distro.name + '.ico')
        self.info.target_drive = self.info.drives_dict.get(self.info.pre_install_path[:2].lower())
        # self.info.cd_path = None # 修复与光盘无关
        if self.info.installationiso:
            self.info.iso_path = self.info.installationiso       
        if not self.info.iso_path:
            log.error("Not found any ISO image ")#执行到这里还找不到ISO,发一下彪
            raise Exception(_("Could not retrieve the required installation files"))
        self.info.home_size_mb = None
        self.info.usr_size_mb  = None
        self.frontend.run_tasks(self.backend.get_fixboot_tasklist())        
        log.info("fixer running finish")

    def run_installer(self):
        '''
        Runs the installer
        '''
        #TBD add non_interactive mode
        #TBD add cd_boot mode
        log.info(self.info.previous_target_dir)
        '''
        if (self.info.previous_target_dir[0] and os.path.isdir(self.info.previous_target_dir[0])) or \
        (self.info.previous_target_dir[1] and os.path.isdir(self.info.previous_target_dir[1])):
        
        if (self.info.previous_target_dir and os.path.isdir(self.info.previous_target_dir))\
                or (self.info.pre_install_path2 and self.info.pre_install_path2):'''
        if (self.info.pre_install_path and os.path.isdir(self.info.pre_install_path))\
                or (self.info.pre_install_path2 and self.info.pre_install_path2):
            log.info("found previous install path, running the uninstaller/fixer...")
            self.info.uninstall_before_install = True
            self.run_uninstall()
            self.backend.fetch_basic_info()
            #if self.info.previous_target_dir and os.path.isdir(self.info.previous_target_dir):
        if (self.info.pre_install_path and os.path.isdir(self.info.pre_install_path))\
                or (self.info.pre_install_path2 and self.info.pre_install_path2):
                message = _("A previous installation was detected in %s.\nPlease uninstall that before continuing.")
                message = message % self.info.previous_target_dir
                log.error(message)
                self.get_frontend().show_error_message(message)
                self.quit()
        log.info("Running the installer...")
        self.frontend = self.get_frontend()
        self.frontend.show_installation_settings()
        log.info("Received settings")
        #print self.info.flag
        if self.info.flag == True:
            self.frontend.run_tasks(self.backend.get_installation_tasklist())
        else:
            self.frontend.run_tasks(self.backend.get_advancedinstallation_tasklist())
        log.info("Almost finished installing")
        self.frontend.show_installation_finish_page()
        log.info("Finished installation")
        if self.info.run_task == "reboot":
            self.reboot()

    def run_uninstall(self):
        '''
        Runs the uninstaller interface
        '''
        log.info("Running the uninstaller/Fixer...")
        if not self.info.previous_target_dir and self.info.pre_install_path:
            self.info.previous_target_dir = self.info.pre_install_path
        if not os.path.isdir(self.info.previous_target_dir):         
                log.error("No previous target dir found, exiting")
                return
        uninstallfile = os.path.join(self.info.previous_target_dir, 'uninstall.exe')
        if os.path.isfile(uninstallfile):
            if self.backend.run_previous_uninstaller(): # 存在uninstall.exe,则程序在此叉开,转去执行该程序
                return
        self.frontend = self.get_frontend()
        self.frontend.show_fix_settings()
        log.info("Received settings")
        if self.info.needfix:
            log.info("try to fix the boot loader")
            self.run_fixboot()
        else:
            log.info("Uninstall the previous installation")
            self.frontend.show_uninstall_confirm_page()
            self.frontend.run_tasks(self.backend.get_uninstallation_tasklist())
            if self.info.pre_install_path2 and os.path.isdir(self.info.pre_install_path2):
                rm_tree(self.info.pre_install_path2)
            if self.info.pre_install_path and os.path.isdir(self.info.pre_install_path):
                rm_tree(self.info.pre_install_path)
        log.info("Almost finished uninstalling")
        if self.info.fixed:#如果修复过的
            self.frontend.show_fix_finish_page()
            if self.info.run_task == "reboot":
                self.reboot()
            self.on_quit()
        elif not self.info.uninstall_before_install:
            self.frontend.show_uninstallaion_finish_page()
        log.info("Finished uninstallation")
        if self.info.inst == "uninstall.exe":
            self.quit()

    def run_cd_menu(self):
        '''
        If Wubi is run off a CD, run the CD menu (old umenu)
        '''
        log.info("Running the CD menu...")
        self.frontend = self.get_frontend()
        if not self.info.cd_distro:
            self.frontend.show_error_message(_("No CD detected, cannot run CD menu"))
            self.quit()
        self.frontend.show_cd_menu_page()
        log.info("CD menu finished")
        self.select_task()

    def run_cd_boot(self):
        if not self.info.cd_distro:
            message = _("Could not find any valid CD.\nCD boot helper can only be used with a Live CD.")
            log.error(message)
            self.get_frontend().show_error_message(message)
            self.quit()
        if self.info.previous_target_dir:
            log.info("Already installed, running the uninstaller...")
            self.info.uninstall_before_install = True
            self.run_uninstaller()
            self.backend.fetch_basic_info()
            if self.info.previous_target_dir:
                message = _("A previous installation was detected in %s.\nPlease uninstall that before continuing.")
                message = message % self.info.previous_target_dir
                log.error(message)
                self.get_frontend().show_error_message(message)
                self.quit()
        log.info("Running the CD boot helper...")
        self.frontend = self.get_frontend()
        self.frontend.show_cdboot_page()
        log.info("CD boot helper confirmed")
        self.frontend.run_tasks(self.backend.get_cdboot_tasklist())
        log.info("Almost finished installing")
        self.frontend.show_installation_finish_page()
        log.info("Finished installation")
        if self.info.run_task == "reboot":
            self.reboot()

    def reboot(self):
        log.info("Rebooting")
        tasklist = self.backend.get_reboot_tasklist()
        tasklist.run()

    def show_info(self):
        self.backend.show_info()

    def parse_commandline_arguments(self):
        '''
        Parses commandline arguments
        '''
        usage = "%s [options]" % self.info.application_name
        parser = OptionParser(usage=usage, version=self.info.full_version)
        parser.add_option("--quiet", action="store_const", const="quiet", dest="verbosity", help="run in quiet mode, only critical error messages are displayed")
        parser.add_option("--verbose", action="store_const", const="verbose", dest="verbosity", help="run in verbose mode, all messages are displayed")
        parser.add_option("--install", action="store_const", const="install", dest="run_task", help="run the uninstaller, it will first look for an existing uninstaller, otherwise it will run itself in uninstaller mode")
        parser.add_option("--uninstall", action="store_const", const="uninstall", dest="run_task", help="run the installer, if an existing installation is detected it will be uninstalled first")
        parser.add_option("--cdmenu", action="store_const", const="cd_menu", dest="run_task", help="run the CD menu selector")
        parser.add_option("--cdboot", action="store_const", const="cd_boot", dest="run_task", help="install a CD boot helper program")
        parser.add_option("--showinfo", action="store_const", const="show_info", dest="run_task", help="open the distribution website for more information")
        parser.add_option("--nobittorrent", action="store_true", dest="no_bittorrent", help="Do not use the bittorrent downloader")
        parser.add_option("--32bit", action="store_true", dest="force_i386", help="Force installation of 32 bit version")
        parser.add_option("--skipmd5check", action="store_true", dest="skip_md5_check", help="Skip md5 checks")
        parser.add_option("--skipsizecheck", action="store_true", dest="skip_size_check", help="Skip disk size checks")
        parser.add_option("--skipmemorycheck", action="store_true", dest="skip_memory_check", help="Skip memory size checks")
        parser.add_option("--noninteractive", action="store_true", dest="non_interactive", help="Non interactive mode")
        parser.add_option("--test", action="store_true", dest="test", help="Test mode")
        parser.add_option("--debug", action="store_true", dest="debug", help="Debug mode")
        parser.add_option("--drive", dest="target_drive", help="Target drive")
        parser.add_option("--size", dest="installation_size_mb", help="Installation size in MB")
        parser.add_option("--locale", dest="locale", help="Linux locale")
        parser.add_option("--force-wubi", action="store_true", dest="force_wubi", help="Show Wubi option in CD menu even when using a DVD")
        parser.add_option("--language", dest="language", help="Language")
        parser.add_option("--username", dest="username", help="Username")
        parser.add_option("--password", dest="password", help="Password (md5)")
        parser.add_option("--distro", dest="distro_name", help="Distro")
        parser.add_option("--accessibility", dest="accessibility", help="Accessibility")
        parser.add_option("--webproxy", dest="web_proxy", help="Web proxy")
        parser.add_option("--isopath", dest="iso_path", help="Use specified ISO")
        parser.add_option("--exefile", dest="original_exe", default=None, help="Used to indicate the original location of the executable in case of self-extracting files")
        parser.add_option("--log-file", dest="log_file", default=None, help="use the specified log file, if omitted a log is created in your temp directory, if the value is set to 'none' no log is created")
        parser.add_option("--interface", dest="use_frontend", default=None, help="use the specified user interface, ['win32']")
        (options, self.args) = parser.parse_args()
        self.info.__dict__.update(options.__dict__)
        if self.info.test:
            self.info.debug = True
        if self.info.debug:
            self.info.verbosity = "verbose"
        if self.info.original_exe:
            original_exe = self.info.original_exe.strip()
            if original_exe[0] in ['"',"'"] and original_exe[-1]  in ['"',"'"]:
                self.info.original_exe = original_exe[1:-1].strip()
            if os.path.basename(self.info.original_exe).startswith("uninstall-"):
                self.info.run_task = "uninstall"

    def set_logger(self, log_to_console=True):
        '''
        Adjust the application root logger settings
        '''
        # file logging
        if not self.info.log_file or self.info.log_file.lower() != "none":
            if not self.info.log_file:
                fname = self.info.full_application_name + ".log"
                dname = tempfile.gettempdir()
                self.info.log_file = os.path.join(dname, fname)
            handler = logging.FileHandler(self.info.log_file)
            formatter = logging.Formatter('%(asctime)s %(levelname)-6s %(name)s: %(message)s', datefmt='%m-%d %H:%M')
            handler.setFormatter(formatter)
            handler.setLevel(logging.DEBUG)
            log.addHandler(handler)
        # console logging
        if log_to_console and not bool(self.info.original_exe):
            handler = logging.StreamHandler()
            formatter = logging.Formatter('%(message)s', datefmt='%m-%d %H:%M')
            handler.setFormatter(formatter)
            if self.info.verbosity == "verbose":
                handler.setLevel(logging.DEBUG)
            elif self.info.verbosity == "quiet":
                handler.setLevel(logging.ERROR)
            else:
                handler.setLevel(logging.INFO)
            log.addHandler(handler)
        log.setLevel(logging.DEBUG)


class Info(object):

    def __str__(self):
        return "Info(%s)" % str(self.__dict__)


if __name__ == "__main__":
    app = Wubi()
    app.run()
