import torch
from torch_geometric.data import Data


class Batch(Data):
    r"""A plain old python object modeling a batch of graphs as one big
    (dicconnected) graph. With :class:`torch_geometric.data.Data` being the
    base class, all its methods can also be used here.
    In addition, single graphs can be reconstructed via the assignment vector
    :obj:`batch`, which maps each node to its respective graph identifier.
    """

    def __init__(self, batch=None, **kwargs):
        super(Batch, self).__init__(**kwargs)
        self.batch = batch

    @staticmethod
    def from_data_list(data_list, follow_batch=[]):
        r"""Constructs a batch object from a python list holding
        :class:`torch_geometric.data.Data` objects.
        The assignment vector :obj:`batch` is created on the fly.
        Additionally, creates assignment batch vectors for each key in
        :obj:`follow_batch`."""

        keys = [set(data.keys) for data in data_list]
        keys = list(set.union(*keys))
        assert 'batch' not in keys

        batch = Batch()

        for key in keys:
            batch[key] = []

        for key in follow_batch:
            batch['{}_batch'.format(key)] = []

        batch.batch = []

        cumsum = 0
        for i, data in enumerate(data_list):
            for key in data.keys:
                item = data[key]
                item = item + cumsum if data.__cumsum__(key, item) else item
                batch[key].append(item)

            for key in follow_batch:
                size = data[key].size(data.__cat_dim__(key, data[key]))
                item = torch.full((size, ), i, dtype=torch.long)
                batch['{}_batch'.format(key)].append(item)

            num_nodes = data.num_nodes
            if num_nodes is not None:
                item = torch.full((num_nodes, ), i, dtype=torch.long)
                batch.batch.append(item)
                cumsum += num_nodes

        if num_nodes is None:  # pragma: no cover
            batch.batch = None

        for key in batch.keys:
            item = batch[key][0]
            if torch.is_tensor(item):
                batch[key] = torch.cat(
                    batch[key], dim=data_list[0].__cat_dim__(key, item))
            elif isinstance(item, int) or isinstance(item, float):
                batch[key] = torch.tensor(batch[key])
            else:
                raise ValueError('Unsupported attribute type.')

        # Copy custom data functions to batch.
        # if data_list.__class__ != Data:
        #     org_funcs = set(Data.__dict__.keys())
        #     funcs = set(data_list[0].__class__.__dict__.keys())
        #     batch.__custom_funcs__ = funcs.difference(org_funcs)
        #     for func in funcs.difference(org_funcs):
        #         setattr(batch, func, getattr(data_list[0], func))

        return batch.contiguous()

    @property
    def num_graphs(self):
        """Returns the number of graphs in the batch."""
        return self.batch[-1].item() + 1
