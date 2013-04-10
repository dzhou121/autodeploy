import subprocess
from flask import Flask, request


app = Flask(__name__)


class ProcessExecutionError(IOError):
    def __init__(self, stdout=None, stderr=None, exit_code=None, cmd=None,
                 description=None):
        self.exit_code = exit_code
        self.stderr = stderr
        self.stdout = stdout
        self.cmd = cmd
        self.description = description

        if description is None:
            description = 'Unexpected error while running command.'
        if exit_code is None:
            exit_code = '-'
        message = ('%(description)s\nCommand: %(cmd)s\n'
                   'Exit code: %(exit_code)s\nStdout: %(stdout)r\n'
                   'Stderr: %(stderr)r') % locals()
        IOError.__init__(self, message)


def execute(*cmd, **kwargs):
    cwd = kwargs.pop('cwd', '.')
    cmd = map(str, cmd)

    try:
        _PIPE = subprocess.PIPE  # pylint: disable=E1101
        obj = subprocess.Popen(cmd,
                               stdin=_PIPE,
                               stdout=_PIPE,
                               stderr=_PIPE,
                               close_fds=True,
                               shell=False,
                               cwd=cwd)
        result = None
        result = obj.communicate()
        obj.stdin.close()  # pylint: disable=E1101
        _returncode = obj.returncode  # pylint: disable=E1101
        if _returncode:
            if _returncode not in [0]:
                (stdout, stderr) = result
                raise ProcessExecutionError(
                    exit_code=_returncode,
                    stdout=stdout,
                    stderr=stderr,
                    cmd=' '.join(cmd))
        return result
    except ProcessExecutionError:
        raise


def deploy(dir, prog):
    execute('git', 'pull', cwd=dir)
    execute('python', 'setup.py', 'install', cwd=dir)
    execute('/etc/init.d/%s' % prog, 'restart')


@app.route('/', methods=["GET", "POST"])
def index():
    dir = request.args['dir']
    prog = request.args['prog']
    deploy(dir, prog)
    return 'success'


if __name__ == '__main__':
    app.run('0.0.0.0')
