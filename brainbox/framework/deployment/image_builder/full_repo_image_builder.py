import os
import pickle
from typing import *
from dataclasses import dataclass, field
from pathlib import Path
import shutil
from kaia.infra import FileIO, Loc
import datetime
import subprocess
from .image_builder import IImageBuilder
from .. import IExecutor


@dataclass
class FullRepoContainerBuilder(IImageBuilder):
    name: str
    tag: str
    entry_point: Any
    dependencies: List[str]
    deployed_folders: Iterable[str]
    python_version: str = '3.8'
    root_path: Optional[Path] = None
    additional_dependencies: Optional[Iterable[Iterable[str]]] = None
    custom_dockerfile_template: str = None
    custom_entryfile_template: str = None
    custom_setup_py_template: str = None
    custom_dockerignore_template: str = None
    build_command: list[str] = field(default_factory=lambda:['build'])
    custom_local_image_name: str|None = None
    feed_input: str | None = None

    def _make_pip_install(self, deps: Iterable[str]):
        deps = list(deps)
        if len(deps) == 0:
            return ''
        libs = ' '.join(deps)
        return 'RUN pip install ' + libs

    def _make_dockerfile(self):
        dockerfile_template = DOCKERFILE_TEMPLATE
        if self.custom_dockerfile_template is not None:
            dockerfile_template = self.custom_dockerfile_template

        install_libraries = self._make_pip_install(self.dependencies)
        if self.additional_dependencies is not None:
            for dep_list in self.additional_dependencies:
                install_libraries += '\n\n' + self._make_pip_install(dep_list)

        content = dockerfile_template.format(
            python_version=self.python_version,
            install_libraries=install_libraries,
        )
        return content

    def _make_entryfile(self):
        entryfile_template = ENTRYFILE_TEMPLATE
        if self.custom_entryfile_template is not None:
            entryfile_template = self.custom_entryfile_template

        return entryfile_template.format(name=self.name, version=self.tag)

    def _make_setup_py(self):
        template = SETUP_PY_TEMPLATE
        if self.custom_setup_py_template is not None:
            template = self.custom_setup_py_template
        return template.format(name=self.name, version=self.tag)

    def _make_dockerignore(self):
        template = DOCKER_IGNORE_TEMPLATE
        if self.custom_dockerignore_template is not None:
            template = self.custom_dockerignore_template
        return template

    def _make_deploy_folder(self, root_path: Path, docker_path: Path):
        shutil.rmtree(docker_path, ignore_errors=True)
        os.makedirs(docker_path)
        FileIO.write_text(self._make_dockerfile(), docker_path / 'Dockerfile')
        FileIO.write_text(self._make_setup_py(), docker_path / 'setup.py')
        FileIO.write_text(self._make_dockerignore(), docker_path / '.dockerignore')
        FileIO.write_text(self._make_entryfile(), docker_path / 'entry.py')
        for folder in self.deployed_folders:
            src = root_path/folder
            if src.is_dir():
                shutil.copytree(src, docker_path / folder)
            else:
                shutil.copy(src, docker_path / folder)


    def _make_all_files(self):
        root_path = self.root_path
        if root_path is None:
            root_path = Loc.root_path
        docker_path = Loc.temp_folder / 'deployments' / str(datetime.datetime.now().timestamp())
        self._make_deploy_folder(root_path, docker_path)
        with open(docker_path / 'entry.pkl', 'wb') as file:
            pickle.dump(self.entry_point, file)
        return docker_path

    def build_image(self, image_name: str, exec: IExecutor) -> None:
        docker_path = self._make_all_files()
        arguments = ['docker'] + self.build_command + ['--tag', image_name, str(docker_path)]
        exec.execute(arguments)
        shutil.rmtree(docker_path)




ENTRYFILE_TEMPLATE = '''
from pathlib import Path
import pickle

with open(Path(__file__).parent/"entry.pkl",'rb') as file:
    entry_point = pickle.load(file)

entry_point()

'''

DOCKERFILE_TEMPLATE = '''FROM python:{python_version}

{install_libraries}

COPY . /home/app

WORKDIR /home/app

RUN pip install -e .

CMD ["python3","/home/app/entry.py"]
'''

DOCKER_IGNORE_TEMPLATE = '''
**/*.pyc
'''

SETUP_PY_TEMPLATE = '''
from setuptools import setup, find_packages

setup(name='{name}',
      version='{version}',
      packages=find_packages(),
      install_requires=[
      ],
      include_package_data = True,
      zip_safe=False)
'''
