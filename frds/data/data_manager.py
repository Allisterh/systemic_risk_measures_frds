from multiprocessing.shared_memory import SharedMemory
from multiprocessing.managers import SharedMemoryManager
from multiprocessing import Queue
from importlib import import_module
from numpy import recarray, copyto, dtype
from pandas import DataFrame
from .dataset import Dataset
from typing import NewType, Tuple
import os

SharedMemoryInfo = NewType(
    'SharedMemoryInfo', Tuple[SharedMemory, tuple, dtype])


class DataManager:

    def __init__(self):
        self._datasets = dict()
        self.smm = SharedMemoryManager()
        self.smm.start()
        self.queue = Queue()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.smm.shutdown()

    def shutdown(self):
        self.smm.shutdown()

    def _add_to_shared_memory(self, nparray: recarray) -> SharedMemory:
        """Internal function to copy an array into shared memory.

        Parameters
        ----------
        nparray : recarray
            The array to be copied into shared memory.

        Returns
        -------
        SharedMemoryName
            The shared memory object.
        """
        shm = self.smm.SharedMemory(nparray.nbytes)
        array = recarray(shape=nparray.shape, dtype=nparray.dtype, buf=shm.buf)
        copyto(array, nparray)
        return shm

    def _download_dataset(self, dataset: Dataset) -> recarray:
        """Internal function to download the dataset.

        Parameters
        ----------
        dataset : Dataset
            Dataset information including source, library, table, vars, etc.

        Returns
        -------
        recarray
            `numpy.recarry` of the downloaded dataset.
        """
        module = import_module(f'frds.data.{dataset.source}')
        assert hasattr(module, 'Connection')
        # TODO: generic login data for different data sources
        usr = os.getenv('WRDS_USRNAME')
        pwd = os.getenv("WRDS_PASSWORD")
        with module.Connection(usr=usr, pwd=pwd) as conn:
            df = conn.get_table(library=dataset.library,
                                table=dataset.table,
                                columns=dataset.vars,
                                date_cols=dataset.date_vars,
                                obs=1000)
        assert isinstance(df, DataFrame)
        return df.to_records(index=False)

    def get_dataset(self, dataset: Dataset) -> SharedMemoryInfo:
        """Get the shared memory object, shape and dtype of the given dataset.

        Parameters
        ----------
        dataset : Dataset
            Dataset information including source, library, table, vars, etc.

        Returns
        -------
        SharedMemoryInfo
            (SharedMemory, tuple, numpy.dtype), where the tuple is the shape.
        """
        if dataset in self._datasets:
            return self._datasets.get(dataset)
        nparray = self._download_dataset(dataset)
        shm = self._add_to_shared_memory(nparray)
        self._datasets.update({dataset: (shm, nparray.shape, nparray.dtype)})
        return shm, nparray.shape, nparray.dtype
