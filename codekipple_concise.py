# Make coding more python3-ish
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

DOCUMENTATION = '''
    callback: codekipple_concise
    type: stdout
    short_description: codekipple_concise Ansible screen output
    description:
        - Concise output callback
'''

import yaml
from ansible.module_utils._text import to_text
from ansible.plugins.callback import CallbackBase, strip_internal_keys, module_response_deepcopy
from ansible.parsing.yaml.dumper import AnsibleDumper
from ansible import constants as C
from ansible.utils.color import stringc, hostcolor, colorize
from pprint import pprint
from terminaltables import AsciiTable

class CallbackModule(CallbackBase):

    '''
    This is the default callback interface, which simply prints messages
    to stdout when new callback events are received.
    '''

    CALLBACK_VERSION = 2.0
    CALLBACK_TYPE = 'stdout'
    CALLBACK_NAME = 'codekipple_concise'
    current_task = ''
    carriage_return = u'\u000D'
    check_mark = u'\u2713'

    def _dump_results(self, result, indent=None, sort_keys=True, keep_invocation=False):
        if result.get('_ansible_no_log', False):
            return json.dumps(dict(censored="The output has been hidden due to the fact that 'no_log: true' was specified for this result"))

        # All result keys stating with _ansible_ are internal, so remove them from the result before we output anything.
        abridged_result = strip_internal_keys(module_response_deepcopy(result))

        # remove invocation unless specifically wanting it
        if not keep_invocation and self._display.verbosity < 3 and 'invocation' in result:
            del abridged_result['invocation']

        # remove diff information from screen output
        if self._display.verbosity < 3 and 'diff' in result:
            del abridged_result['diff']

        # remove exception from screen output
        if 'exception' in abridged_result:
            del abridged_result['exception']

        dumped = ''

        # put changed and skipped into a header line
        if 'changed' in abridged_result:
            dumped += 'changed=' + str(abridged_result['changed']).lower() + ' '
            del abridged_result['changed']

        if 'skipped' in abridged_result:
            dumped += 'skipped=' + str(abridged_result['skipped']).lower() + ' '
            del abridged_result['skipped']

        # if we already have stdout, we don't need stdout_lines
        if 'stdout' in abridged_result and 'stdout_lines' in abridged_result:
            abridged_result['stdout_lines'] = '<omitted>'

        # if we already have stderr, we don't need stderr_lines
        if 'stderr' in abridged_result and 'stderr_lines' in abridged_result:
            abridged_result['stderr_lines'] = '<omitted>'

        if abridged_result:
            dumped += '\n'
            dumped += to_text(yaml.dump(abridged_result, allow_unicode=True, width=1000, Dumper=AnsibleDumper, default_flow_style=False))

        # indent by a couple of spaces
        dumped = '\n  '.join(dumped.split('\n')).rstrip()
        return dumped

    def _serialize_diff(self, diff):
        return to_text(yaml.dump(diff, allow_unicode=True, width=1000, Dumper=AnsibleDumper, default_flow_style=False))

    def padd_text(self, text, paddVal):
        output = ""
        spacing = ""

        for i in range(0, paddVal):
            spacing = spacing + " "

        lines = text.splitlines();
        for line in lines:
            line = spacing + line;
            output = output + line + self.carriage_return

        return output

    def _command_generic_msg(self, result):
        ''' output the result of a command run '''

        buf = result.get('stdout', '')
        buf += result.get('stderr', '')
        buf += result.get('msg', '')

        return buf + "\n"

    def v2_runner_on_failed(self, result, ignore_errors=False):
        delegated_vars = result._result.get('_ansible_delegated_vars', None)

        cross = stringc(u'\u00D7', C.COLOR_ERROR);
        host = "%s" % result._host
        taskName = "%s" % result._task_fields['name']

        if not taskName:
            taskName = result._task_fields['action']

        self._display.display("")
        self._display.display(self.padd_text(taskName, 1))
        self._display.display(self.padd_text(cross + " " + host, 1))
        self._display.display(self.padd_text(u'\u21b3' + " [failed]:", 4), C.COLOR_ERROR)

        if delegated_vars:
            self._display.display("%s" % delegated_vars['ansible_host'])

        self._display.display(self.padd_text(u'\u21b3' + " %s" % self._dump_results(result._result, indent=4), 4), C.COLOR_ERROR)

        self._handle_exception(result._result)
        self._handle_warnings(result._result)

        if ignore_errors:
            self._display.display("...ignoring", color=C.COLOR_SKIP)
        else:
            self._display.display("")

    def v2_runner_on_ok(self, result):
        delegated_vars = result._result.get('_ansible_delegated_vars', None)

        if result._result.get('changed', False):
            color = C.COLOR_CHANGED
            state = 'CHANGED'
        else:
            color = C.COLOR_OK
            state = 'SUCCESS'

        output_task = False;
        taskName = "%s" % result._task_fields['name']

        if not taskName:
            taskName = result._task_fields['action']

        if self.current_task != taskName:
            self.current_task = taskName
            output_task = True

        if output_task:
            self._display.display("")
            taskLine = taskName

            if result._task._role:
                taskLine += stringc(" [%s]" % result._task._role.get_name(), 'dark gray');
            self._display.display(self.padd_text(taskLine, 1))

        host = "%s" % result._host
        self._display.display(self.padd_text(stringc(self.check_mark, color) + " " + host, 1))

        if delegated_vars:
            self._display.display(self.padd_text("u'\u21b3' [vars] %s" % (result._host.get_name(), delegated_vars['ansible_host']), 4))

        self._handle_warnings(result._result)

    def v2_runner_on_skipped(self, result):
        host = "%s" % result._host
        taskName = "%s" % result._task_fields['name']

        if not taskName:
            taskName = result._task_fields['action']

        if self.current_task != taskName:
            self.current_task = taskName
            self._display.display("")
            taskLine = taskName

            if result._task._role:
                taskLine += stringc(" [%s]" % result._task._role.get_name(), 'dark gray');
            self._display.display(self.padd_text(taskLine, 1))

        self._display.display(self.padd_text(stringc('-', C.COLOR_SKIP) + " " + host + " " + stringc('[skipped]', C.COLOR_SKIP), 1))

    def v2_playbook_on_no_hosts_remaining(self):
        table_data = [
            ["No more hosts left"],
        ]
        noHostsTable = AsciiTable(table_data)
        self._display.display("")
        self._display.display(noHostsTable.table, screen_only=True)

    def v2_playbook_on_play_start(self, play):
        name = play.get_name().strip()
        output = ""

        if name:
            output = name

        self._play = play

        table_data = [
            [output],
        ]
        playStartTable = AsciiTable(table_data)
        playStartTable.title = "Play"
        self._display.display("")
        self._display.display(playStartTable.table, screen_only=True)

    def v2_playbook_on_stats(self, stats):
        output = ""

        hosts = sorted(stats.processed.keys())
        for h in hosts:
            t = stats.summarize(h)

            output += u"%s : %s %s %s %s %s %s %s %s" % (
                hostcolor(h, t),
                colorize(u'ok', t['ok'], C.COLOR_OK),
                colorize(u'changed', t['changed'], C.COLOR_CHANGED),
                colorize(u'unreachable', t['unreachable'], C.COLOR_UNREACHABLE),
                colorize(u'failed', t['failures'], C.COLOR_ERROR),
                colorize(u'skipped', t['skipped'], C.COLOR_SKIP),
                colorize(u'rescued', t['rescued'], C.COLOR_OK),
                colorize(u'ignored', t['ignored'], C.COLOR_WARN),
                self.carriage_return
            )

            self._display.display(
                u"%s : %s %s %s %s %s %s %s" % (
                    hostcolor(h, t, False),
                    colorize(u'ok', t['ok'], None),
                    colorize(u'changed', t['changed'], None),
                    colorize(u'unreachable', t['unreachable'], None),
                    colorize(u'failed', t['failures'], None),
                    colorize(u'skipped', t['skipped'], None),
                    colorize(u'rescued', t['rescued'], None),
                    colorize(u'ignored', t['ignored'], None),
                ),
                log_only=True
            )


        # print custom stats if required
        if stats.custom and self.show_custom_stats:
            self._display.banner("CUSTOM STATS: ")
            # per host
            # TODO: come up with 'pretty format'
            for k in sorted(stats.custom.keys()):
                if k == '_run':
                    continue
                output += "\t%s: %s %s" % (k, self._dump_results(stats.custom[k], indent=1).replace('\n', ''), self.carriage_return)

            # print per run custom stats
            if '_run' in stats.custom:
                output += self.carriage_return
                output += "\tRUN: %s %s" % (self._dump_results(stats.custom['_run'], indent=1).replace('\n', ''), self.carriage_return)
            output += self.carriage_return

        table_data = [
            [output],
        ]
        statsTable = AsciiTable(table_data)
        statsTable.title = "Play Recap"
        self._display.display("")
        self._display.display(statsTable.table, screen_only=True)
        self._display.display("")

    def v2_runner_on_unreachable(self, result):
        self._display.display("%s | UNREACHABLE! => %s" % (result._host.get_name(), self._dump_results(result._result, indent=4)), color=C.COLOR_UNREACHABLE)

    def v2_on_file_diff(self, result):
        if 'diff' in result._result and result._result['diff']:
            self._display.display(self._get_diff(result._result['diff']))

    def _handle_warnings(self, res):
        ''' display warnings, if enabled and any exist in the result '''
        if C.ACTION_WARNINGS:
            if 'warnings' in res and res['warnings']:
                for warning in res['warnings']:
                    warningText = stringc(u'\u21b3' + " " + "[warning]: " + warning, C.COLOR_WARN)
                    self._display.display(self.padd_text(warningText, 4))
                del res['warnings']
            if 'deprecations' in res and res['deprecations']:
                for warning in res['deprecations']:
                    self._display.deprecated(**warning)
                del res['deprecations']
