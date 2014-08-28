import sublime
import sublime_plugin
import subprocess
import os
import platform

class OpenFolderClassicCommand(object):
    def __init__(self, window, cmdline):
        self.window = window
        self.cmdline = cmdline

    def runForFolder(self, folderPath):
        subprocess.call(self.cmdline.format(folderPath), shell=True)

    def runForFile(self, filePath):
        self.window.run_command(
            "open_dir",
            {"dir": os.path.dirname(filePath), "file": os.path.basename(filePath)}
        )

class OpenFolderCommand(object):
    def __init__(self, window, folder_command, file_command):
        self.window = window
        self.folder_command = folder_command
        self.file_command = file_command

    def runForFolder(self, folderPath):
        pieces = self.parseFolder(folderPath)

        if self.folder_command is None:
            raise RuntimeError('There are not commands configurated')
        else:
            self.execute(self.folder_command['command'], pieces, bool(self.folder_command['use_shell']) if 'use_shell' in self.folder_command else False)

    def runForFile(self, filePath):
        pieces = self.parseFile(filePath)

        if self.file_command is None:
            if self.folder_command is not None:
                return self.runForFolder(pieces['dirname'])
            else:
                raise RuntimeError('There are not commands configurated')
        else:
            self.execute(self.file_command['command'], pieces, bool(self.file_command['use_shell']) if 'use_shell' in self.file_command else False)

    def parseFolder(self, path):
        return {
            'filepath': path,
            'dirname': path,
            'basename': ''
        }

    def parseFile(self, path):
        return {
            'filepath': path,
            'dirname': os.path.dirname(path),
            'basename': os.path.basename(path)
        }

    def execute(self, cmd, filler, use_shell):

        try:
            cmd_list = [ item.format(**filler) for item in cmd ]
        except KeyError as err:
            return sublime.status_message("{0} is not a valid replacement".format(err.args[0]))
        except Exception as err:
            return sublime.status_message(repr(err))

        cwd = filler['dirname']

        try:
            subprocess.Popen(cmd_list, shell=use_shell, cwd=cwd)
        except Exception as err:
            sublime.status_message(repr(err))

class OpenFolderHelper(object):
    @classmethod
    def getCommand(cls, window):
        helper = cls()
        classic_cmdline = helper.getSetting("file_manager")

        if classic_cmdline is not None:
            return OpenFolderClassicCommand(window, classic_cmdline)

        return OpenFolderCommand(window, helper.getSetting('folder'), helper.getSetting('file'))

    @classmethod
    def getHostSettingsFilePath(cls):
        return cls.getSettingsFilePath(platform.uname()[1])

    @classmethod
    def getSettingsFilePath(cls, special=None):
        return "".join(("OpenFolder", " (" + special + ")" if special else "", ".sublime-settings"))

    def __init__(self):
        self.host_settings = sublime.load_settings(OpenFolderHelper.getHostSettingsFilePath())
        self.user_settings = sublime.load_settings(OpenFolderHelper.getSettingsFilePath())

    def getSetting(self, settingName, default=None):
        return self.host_settings.get(settingName, self.user_settings.get(settingName, default))

class OpenFolder(sublime_plugin.WindowCommand):
    def run(self, paths):
        command = OpenFolderHelper.getCommand(self.window)

        for path in paths:
            if os.path.isdir(path):
                command.runForFolder(path)
            else:
                command.runForFile(path)

    def description(self, paths):
        helper = OpenFolderHelper()

        display_for_files = helper.getSetting('display_for_files', True)

        file_count = 0
        dir_count = 0

        for path in paths:
            if os.path.isdir(path):
                dir_count += 1
            else:
                file_count += 1

        if dir_count > 1 or (dir_count > 0 and file_count > 0):
            return "Open Folders"
        elif dir_count == 1:
            return "Open Folder"
        elif file_count > 1 and display_for_files:
            return u"Open Containing Folders\u2026"
        elif file_count > 0 and display_for_files:
            return u"Open Containing Folder\u2026"
        else:
            return None


class OpenFolderOpenSettings(sublime_plugin.WindowCommand):
    def run(self, scope='default'):
        if scope == 'host':
            settingsFile = os.path.join(sublime.packages_path(), 'User', OpenFolderHelper.getHostSettingsFilePath())
        elif scope == 'user':
            settingsFile = os.path.join(sublime.packages_path(), 'User', OpenFolderHelper.getSettingsFilePath())
        elif scope == 'os':
            settingsFile = os.path.join(sublime.packages_path(), 'Open Folder', OpenFolderHelper.getSettingsFilePath(sublime.platform().capitalize()))
        else:
            settingsFile = os.path.join(sublime.packages_path(), 'Open Folder', OpenFolderHelper.getSettingsFilePath())

        self.window.open_file(settingsFile)


class OpenFolderOpenCurrent(sublime_plugin.TextCommand):
    def run(self, edit):
        if self.view.file_name() is not None:
            self.view.window().run_command('open_folder', {'paths': [self.view.file_name()]})
