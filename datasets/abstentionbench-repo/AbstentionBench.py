import json
import logging
import os

import datasets

from .data import (
    GPQA,
    GSM8K,
    UMWP,
    ALCUNADataset,
    BBQDataset,
    BigBenchDisambiguateDataset,
    BigBenchKnownUnknownsDataset,
    CoCoNotDataset,
    FalseQADataset,
    KUQDataset,
    MediQDataset,
    MMLUHistory,
    MMLUMath,
    MoralChoiceDataset,
    MusiqueDataset,
    QAQADataset,
    QASPERDataset,
    SituatedQAGeoDataset,
    Squad2Dataset,
    WorldSenseDataset,
)

logger = logging.getLogger(__name__)


_DESCRIPTION = """\
AbstentionBench is a benchmark for the holistic evaluation of abstention capabilities in frontier LLMs.
"""

_CITATION = """\
@misc{kirichenko2025abstentionbenchreasoningllmsfail,
      title={AbstentionBench: Reasoning LLMs Fail on Unanswerable Questions}, 
      author={Polina Kirichenko and Mark Ibrahim and Kamalika Chaudhuri and Samuel J. Bell},
      year={2025},
      eprint={2506.09038},
      archivePrefix={arXiv},
      primaryClass={cs.AI},
      url={https://arxiv.org/abs/2506.09038}, 
}
"""


class AbstentionBench(datasets.DatasetBuilder):

    def _info(self):
        return datasets.DatasetInfo(
            description=_DESCRIPTION,
            features=datasets.Features({
                "question": datasets.Value("string"),
                "reference_answers": datasets.features.Sequence(datasets.Value("string")),
                "should_abstain": datasets.Value("bool"),
                "metadata_json": datasets.Value("string"),
            }),
            homepage="https://github.com/facebookresearch/abstentionbench",
            citation=_CITATION,
            license="CC BY-NC 4.0",
        )

    def _load_subsampling_indices(self, path):
        with open(path, "r") as f:
            dataset_name_to_indices = json.load(f)

        return dataset_name_to_indices

    def download_and_prepare(self, dl_manager=None, **_):
        dl_manager = dl_manager or datasets.DownloadManager()

        # Download any metadata needed for assigning categories or subsampling
        umwp_indices_answerable_path = dl_manager.download(os.path.join(self.base_path, 'UMWP_indices_answerable.json'))
        kuq_category_map_path = dl_manager.download(os.path.join(self.base_path, 'kuq_new_categories.csv'))
        subsampling_indices_path = dl_manager.download(os.path.join(self.base_path, 'subsampling-indices.json'))

        dataset_name_to_dataset = {
            "alcuna": ALCUNADataset(),
            "bbq": BBQDataset(),
            "big_bench_disambiguate": BigBenchDisambiguateDataset(),
            "big_bench_known_unknowns": BigBenchKnownUnknownsDataset(),
            "coconot": CoCoNotDataset(),
            "falseqa": FalseQADataset(),
            "gpqa_abstain": GPQA(),
            "gsm8k_abstain": GSM8K(),
             "known_unknown_questions": KUQDataset(category_map_path=kuq_category_map_path),
            "known_unknown_questions": KUQDataset(),
            "mediq": MediQDataset(),
            "mmlu_history_abstain": MMLUHistory(),
            "mmlu_math_abstain": MMLUMath(),
            "moral_choice": MoralChoiceDataset(),
            "musique": MusiqueDataset(),
            "qaqa": QAQADataset(),
            "qasper": QASPERDataset(),
            "situated_qa": SituatedQAGeoDataset(),
            "squad2": Squad2Dataset(),
            "umwp": UMWP(indices_answerable_path=umwp_indices_answerable_path),
            "world_sense": WorldSenseDataset(),
        }

        # Keep track of the class names of each dataset, so we can load subsampling indices later
        dataset_name_to_class_name = {name: dataset.name for name, dataset in dataset_name_to_dataset.items()}

        # Convert into HF datasets
        dataset_name_to_hf_dataset = {name: dataset.to_hf_dataset(split=name) for name, dataset in dataset_name_to_dataset.items()}

        # Apply subsampling
        dataset_class_name_to_subsampling_indices = self._load_subsampling_indices(subsampling_indices_path)
        for dataset_name, hf_dataset in dataset_name_to_hf_dataset.items():
            dataset_class_name = dataset_name_to_class_name[dataset_name]
            if dataset_class_name in dataset_class_name_to_subsampling_indices:
                indices = dataset_class_name_to_subsampling_indices[dataset_class_name]
                dataset_name_to_hf_dataset[dataset_name] = hf_dataset.select(indices)

        self.datasets = dataset_name_to_hf_dataset

    def as_dataset(self, split=None, **_) -> datasets.Dataset:
        if split is not None:
            if split not in self.datasets:
                raise ValueError(f"Unknown split: {split}")

            dataset = self.datasets[split]
        else:
            dataset = datasets.concatenate_datasets(self.datasets.values())

        return dataset