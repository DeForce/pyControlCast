from distutils.core import setup

from init import VERSION

setup(
    name='PyControlCast',
    version=VERSION,
    packages=['', 'util'],
    requires=['launchpad_rtmidi_py', 'python-rtmidi', 'pyautogui', 'pydub'],
    url='https://github.com/DeForce/pyControlCast',
    license='',
    author='CzT/DeForce',
    author_email='vlad@czt.lv',
    description=''
)