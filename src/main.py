import logging
import os
import shutil

import models.changes as changes_models
from utils.hash import calculate_md5_hash
from utils.b64 import get_b64_file_content


logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)


class FileSyncer:
    """
    Synchronizes two directories, only copying files that have been modified
    in the source directory since the last synchronization.

    Args:
    source_dir: The source directory path.
    target_dir: The target directory path.
    """
    IGNORE_ENTITIES = ['Thumbs.db', '.DS_Store']

    def __init__(self, source_dir: str, target_dir: str) -> None:
        self._source_dir = source_dir
        self._target_dir = target_dir

    def sync(self) -> str:
        self._check_paths([self._source_dir, self._target_dir])
        changes = []
        changes.extend(self._remove_absent_target_dirs_and_files())
        changes.extend(self._add_absent_source_dirs_and_files())
        return changes_models.convert_to_json(changes)

    @staticmethod
    def _check_paths(paths: list[str]) -> None:
        for path in paths:
            if not os.path.exists(path):
                raise ValueError(f'Path does not exist {path}')

    def _remove_absent_target_dirs_and_files(self) -> list[changes_models.ChangeItem]:
        changes = []
        for root, dirs, files in os.walk(self._target_dir):
            for dir in dirs:
                if self._is_ignored_entity(dir):
                    continue
                target_sub_dir = os.path.join(root, dir)
                source_sub_dir = os.path.join(self._source_dir, os.path.relpath(target_sub_dir, self._target_dir))
                if not os.path.exists(source_sub_dir):
                    changes.append(self.remove_dir(target_sub_dir))
            for file in files:
                if self._is_ignored_entity(dir):
                    continue
                target_file = os.path.join(root, file)
                source_file = os.path.join(self._source_dir, os.path.relpath(target_file, self._target_dir))
                if not os.path.exists(source_file):
                    changes.append(self.remove_file(target_file))
        return changes

    def _add_absent_source_dirs_and_files(self) -> list[changes_models.ChangeItem]:
        changes = []
        for root, dirs, files in os.walk(self._source_dir):
            for dir in dirs:
                if self._is_ignored_entity(dir):
                    continue
                source_sub_dir = os.path.join(root, dir)
                target_sub_dir = os.path.join(self._target_dir, os.path.relpath(source_sub_dir, self._source_dir))
                if not os.path.exists(target_sub_dir):
                    changes.append(self.add_dir(target_sub_dir))
            for file in files:
                if self._is_ignored_entity(dir):
                    continue
                source_file = os.path.join(root, file)
                target_file = os.path.join(self._target_dir, os.path.relpath(source_file, self._source_dir))
                if (
                    not os.path.exists(target_file) or
                    calculate_md5_hash(source_file) != calculate_md5_hash(target_file)
                ):
                    changes.append(self.copy_file(source_file, target_file))
        return changes

    @classmethod
    def _is_ignored_entity(cls, entity: str) -> bool:
        if entity in cls.IGNORE_ENTITIES:
            return True
        return False

    @staticmethod
    def remove_dir(source_path: str) -> changes_models.ChangeItem:
        if not os.path.isdir(source_path):
            raise ValueError(f'Not a dir: {source_path}')
        logger.info(f'Remove dir {source_path}')
        shutil.rmtree(source_path)
        return changes_models.ChangeItem(operation=changes_models.OperationEnum.DEL_DIR, dir_path=source_path)

    @staticmethod
    def remove_file(source_path: str) -> changes_models.ChangeItem:
        if os.path.isdir(source_path):
            raise ValueError(f'Not a file: {source_path}')
        logger.info(f'Remove file {source_path}')
        os.remove(source_path)
        return changes_models.ChangeItem(operation=changes_models.OperationEnum.DEL_FILE, path=source_path)

    @staticmethod
    def add_dir(target_path: str) -> changes_models.ChangeItem:
        logger.info(f'Add dir {target_path}')
        os.makedirs(target_path)
        return changes_models.ChangeItem(operation=changes_models.OperationEnum.ADD_DIR, path=target_path)

    @staticmethod
    def copy_file(source_file: str, target_file: str) -> changes_models.ChangeItem:
        logger.info(f'Add file {source_file} from {target_file}')
        shutil.copy2(source_file, target_file)
        return changes_models.ChangeItem(operation=changes_models.OperationEnum.ADD_FILE, path=target_file,
                                         b64content=get_b64_file_content(source_file))


if __name__ == '__main__':
    source_dir = "tmp/from"
    target_dir = "tmp/to"
    logger.info(FileSyncer(source_dir, target_dir).sync())
