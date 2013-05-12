#===============================================================================
# Copyright 2011 Jake Ross
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#   http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#===============================================================================

import argparse
import buildtools
import MacOS
import os
import plistlib
import shutil
def make():
    parser = argparse.ArgumentParser(description='Make a pychron application')
    parser.add_argument('-A', '--applications',
                        nargs=1,
                        type=str,
                        # default=['pychron', 'remote_hardware_server', 'bakeout'],
                        help='set applications to build')
    parser.add_argument('-v', '--version',
                        nargs=1,
                        type=str,
                        default=['1.0'],
                        help='set the version number e.g 1.0')

    parser.add_argument(
        '-r',
        '--root',
        type=str,
        nargs=1,
        default='.',
        help='set the root directory',
        )

    args = parser.parse_args()
    apps = args.applications
    for name in apps:
        template = None
        if name in ('diode', 'co2', 'valve', 'uv'):
            template = PychronTemplate()
            template.root = args.root[0]
            template.icon_name = 'py{}_icon.icns'.format(name)
            template.bundle_name = 'py{}'.format(name)
            template.version = args.version[0]

        if template is not None:
            template.build()
        else:
            print "Invalid application flavor. Use 'diode', 'co2', 'valve', 'uv'"


class Template(object):
    name = None
    icon_name = None
    root = None
    bundle_name = None
    version = None

    def build(self):
        root = os.path.realpath(self.root)

        dest = os.path.join(root, 'launchers',
                              '{}.app'.format(self.bundle_name),
                              'Contents'
                              )
        ins = Maker()
        ins.root = root
        ins.dest = dest
        ins.name = self.bundle_name
        ins.version = self.version

        op = os.path.join(root, 'launchers',
                          '{}.py'.format(self.bundle_name))
        #=======================================================================
        # build
        #=======================================================================
        ins.build_app(op)
        ins.make_egg()
        ins.make_argv()

        #=======================================================================
        # copy
        #=======================================================================
        icon_name = self.icon_name
        if icon_name is None:
            icon_name = ''

        ins.set_plist(dest, self.bundle_name, icon_name)

        icon_file = os.path.join(self.root,
                                 'resources', 'apps',
                                 icon_name)

        if os.path.isfile(icon_file):
            shutil.copyfile(icon_file,
                            os.path.join(dest, 'Resources', icon_name)
                            )
        # copy helper mod
        helper = os.path.join(self.root,
                              'launchers', 'helpers.py')
        ins.copy_resource(helper)



class PychronTemplate(Template):
    pass


class Maker(object):
    root = None
    dest = None
    version = None
    name = None
    def copy_resource(self, src):
        name = os.path.basename(src)
        shutil.copyfile(src,
                        self._resource_path(name))

    def _resource_path(self, name):
        return os.path.join(self.dest, 'Resources', name)

    def make_egg(self):
        from setuptools import setup, find_packages

        pkgs = find_packages(self.root,
                            exclude=('launchers', 'tests', 'app_utils')
                            )

        setup(name='pychron',
              script_args=('bdist_egg',),
              version=self.version,
              packages=pkgs
              )

        eggname = 'pychron-{}-py2.7.egg'.format(self.version)
        # make the .pth file
        with open(os.path.join(self.dest,
                               'Resources',
                               'pychron.pth'), 'w') as fp:
            fp.write('{}\n'.format(eggname))

        egg_root = os.path.join(self.root, 'dist', eggname)
        shutil.copyfile(egg_root,
                        self._resource_path(eggname)
                        )
    def make_argv(self):
        argv = '''
import os
execfile(os.path.join(os.path.split(__file__)[0], "{}.py"))
'''.format(self.name)

        p = self._resource_path('__argvemulator_{}.py'.format(self.name))
        with open(p, 'w') as fp:
            fp.write(argv)


    def set_plist(self, dest, bundle_name, icon_name):
        info_plist = os.path.join(dest, 'Info.plist')
        tree = plistlib.readPlist(info_plist)

        tree['CFBundleIconFile'] = icon_name
        tree['CFBundleName'] = bundle_name
        plistlib.writePlist(tree, info_plist)

    def build_app(self, filename):
        print filename
        template = buildtools.findtemplate()
        dstfilename = None
        rsrcfilename = None
        raw = 0
        extras = []
        verbose = None
        destroot = ''

        cr, tp = MacOS.GetCreatorAndType(filename)
        if tp == 'APPL':
            buildtools.update(template, filename, dstfilename)
        else:
            buildtools.process(template, filename, dstfilename, 1,
                    rsrcname=rsrcfilename, others=extras, raw=raw,
                    progress=verbose, destroot=destroot)


if __name__ == '__main__':
    make()
