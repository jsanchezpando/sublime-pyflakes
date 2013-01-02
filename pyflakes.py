import sublime_plugin
import subprocess
import re

def highlight_error(self, view, warning):
  if warning:
    warning = warning.split(':')
    line_number = int(warning[1]) - 1
    point = view.text_point(line_number, 0)
    line = view.line(point)
    message = warning[2]

    PyflakesListener.warning_messages[view.id()][line.begin()] = message
    return line


def is_python_file(view):
  return bool(re.search('Python', view.settings().get('syntax'), re.I))


class PyflakesListener(sublime_plugin.EventListener):
  warning_messages = {}

  def on_load(self, view):
    self.do_flakes(view)

  def on_close(self, view):
    del PyflakesListener.warning_messages[view.id()]

  def on_post_save(self, view):
    self.do_flakes(view)

  def do_flakes(self, view):
    if is_python_file(view):
      view.erase_regions('PyflakesWarnings')
      PyflakesListener.warning_messages[view.id()] = {}

      file_name = view.file_name().replace(' ', '\ ')
      process = subprocess.Popen(['pyflakes', file_name], stdout = subprocess.PIPE)
      results, error = process.communicate()

      if results:
        regions = []
        for warning in results.split('\n'):
          region = highlight_error(self, view, warning.replace(file_name, ''))
          if region:
            regions.append(region)

        view.add_regions('PyflakesWarnings', regions, 'string pyflakeswarning', 'dot')


  def on_selection_modified(self, view):
    if is_python_file(view):
      if not view.id() in PyflakesListener.warning_messages:
        return

      warnings = view.get_regions('PyflakesWarnings')
      for warning in warnings:
        if warning.contains(view.sel()[0]):
          view.set_status("pyflakes", PyflakesListener.warning_messages[view.id()][warning.begin()])
          return

      # no warning to display, clear status
      view.set_status("pyflakes", "")
