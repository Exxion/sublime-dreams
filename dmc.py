import sublime, sublime_plugin
from os.path import dirname, splitdrive, isfile, join, splitext
import os, sys
import thread
import subprocess
import functools
import time
import asynclistener
import processlistener

path = {
	'x32': "C:/Program Files/BYOND/bin/",
	'x64': "C:/Program Files (x86)/BYOND/bin/"
}

class DmcCommand(sublime_plugin.WindowCommand, ProcessListener):

	dream_daemon = None
	dream_seeker = None
	dream_maker  = None

	def run(self, cmd = [], file_regex = "", line_regex = "",
            encoding = "utf-8", env = {}, quiet = False, kill_old = False,
            dream_seeker = False, dream_daemon = False, **kwargs):

		file = cmd[0]
		dmpath = path[sublime.arch()]

		dme_dir = dirname(self.find_closest_dme(file))

		self.setup_sublime(file_regex, line_regex, dme_dir, encoding)

		sublime.status_message("Building DMB...")

		self.build(dmpath, dme_dir)
		dmb_dir = self.find_dmb(dme_dir)

		if dream_seeker:
			self.run_in_seeker(dmpath, dmb_dir)

		if dream_daemon:
			self.run_in_daemon(dmpath, dmb_dir)

	def setup_sublime(self, file_regex, line_regex, working_dir, encoding):
		if not hasattr(self, 'output_view'):
		    self.output_view = self.window.get_output_panel("exec")

		if (working_dir == "" and self.window.active_view()
		                and self.window.active_view().file_name()):
		    working_dir = os.path.dirname(self.window.active_view().file_name())

		self.output_view.settings().set("result_file_regex", file_regex)
		self.output_view.settings().set("result_line_regex", line_regex)
		self.output_view.settings().set("result_base_dir", working_dir)

		self.window.get_output_panel("exec")

		self.encoding = encoding

		show_panel_on_build = sublime.load_settings("Preferences.sublime-settings").get("show_panel_on_build", True)
		if show_panel_on_build:
		    self.window.run_command("show_panel", {"panel": "output.exec"})

		if working_dir != "":
		    os.chdir(working_dir)

	def run_cmd(self, cmd, is_daemon = False, is_seeker = False, is_maker = False, **kwargs):

		merged_env = {}
		if self.window.active_view():
		    user_env = self.window.active_view().settings().get('build_env')
		    if user_env:
		        merged_env.update(user_env)

		err_type = OSError
		if os.name == "nt":
		    err_type = WindowsError

		try:
			sublime.status_message("Doing a thing...")
			if is_maker:
				self.dream_maker = AsyncProcess(cmd, merged_env, self, **kwargs)

		except err_type as e:
		    self.append_data(None, str(e) + "\n")
		    self.append_data(None, "[cmd:  " + str(cmd) + "]\n")
		    self.append_data(None, "[dir:  " + str(os.getcwdu()) + "]\n")
		    if "PATH" in merged_env:
		        self.append_data(None, "[path: " + str(merged_env["PATH"]) + "]\n")
		    else:
		        self.append_data(None, "[path: " + str(os.environ["PATH"]) + "]\n")
		    if not self.quiet:
		        self.append_data(None, "[Finished]")

		    sublime.status_message("Failed doing a thing")

	def build(self, environment_path, dme_path):

		cmd = [ environment_path + "dm.exe" , dme_path ]
		'''
		args = {
			'cmd': new_cmd,
			'file_regex': file_regex,
			'working_dir': dirname(dme_path)
		}
		'''
		self.run_cmd(cmd, is_maker = True)
		#sublime.active_window().run_command("exec", args)

	def find_dmb(self, current_dir):
		#sublime.status_message("Finding closest DMB")

		#TODO match the current directory name/dme name
		dmb_list = [ 
			current_dir+"\\"+f.encode('ascii', 'ignore') 
				for f in os.listdir(current_dir) 
					if isfile(join(current_dir, f)) and splitext(f)[1] == u".dmb" 
			]

		if len(dmb_list) is not 0:
			return dmb_list[0]

	def find_closest_dme(self, compile_file):
		sublime.status_message("Finding closest DME...")
		current_dir = compile_file

		dme = compile_file

		while current_dir != self.drive_root(current_dir):

			current_dir = dirname(current_dir)

			file_list = [ 
				current_dir+"\\"+f.encode('ascii', 'ignore') 
					for f in os.listdir(current_dir) 
						if isfile(join(current_dir, f)) and splitext(f)[1] == u".dme" 
				]

			#TODO search for the DME containing the file

			if len(file_list) is not 0:
				dme = file_list[0]

		return dme.encode('ascii', 'ignore') 

	def drive_root(self, path):
		return splitdrive(path)[0]+"\\"

	def run_in_seeker(self, environment_path, dmb = ''):
		sublime.status_message("Running "+dmb+"in DreamSeeker...")
		new_cmd = [ environment_path + "dreamseeker.exe" , dmb ]
		args = {
			'cmd': new_cmd
		}
		sublime.active_window().run_command("exec", args)

	def run_in_daemon(self, environment_path, dmb):
		sublime.status_message("Running in Dream Daemon")
		new_cmd = [ environment_path + "dreamdaemon.exe" , dmb , "-trusted" ]
		args = {
			'cmd': new_cmd
		}
		sublime.active_window().run_command("exec", args)
