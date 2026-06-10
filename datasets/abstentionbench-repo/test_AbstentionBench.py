import datasets

from .AbstentionBench import AbstentionBench


class TestAbstentionBench:

    def test_as_dataset_with_no_split(self):
        dataset_builder = AbstentionBench()
        dataset_builder.download_and_prepare()
        dataset = dataset_builder.as_dataset()

        assert isinstance(dataset, datasets.Dataset)

        sample = dataset[0]

        assert sample['question'][:50] == 'You are a powerful question-answering system with '

    def test_as_dataset_with_split(self):
        dataset_builder = AbstentionBench()
        dataset_builder.download_and_prepare()
        dataset = dataset_builder.as_dataset('falseqa')

        assert isinstance(dataset, datasets.Dataset)

        sample = dataset[0]

        assert sample['question'] == 'Why carbon dioxide is composed of oxygen?'