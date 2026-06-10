import ast
import bz2
import copy
import json
import logging
import os
import pprint
import random
import re
import tarfile
import urllib.request
import zipfile
from abc import ABC, abstractmethod
from io import StringIO
from pathlib import Path
from typing import List, Literal, Optional

import datasets
import gdown
import jsonlines
import numpy as np
import pandas as pd
import requests
import torch
import wget
from datasets import Dataset, concatenate_datasets, load_dataset
from pydantic import BaseModel

logger = logging.getLogger(__name__)

class Prompt(BaseModel):
    question: str
    reference_answers: Optional[list[str]]
    should_abstain: Optional[bool]
    metadata: dict


class AbstentionDataset(ABC, torch.utils.data.Dataset):
    @abstractmethod
    def __getitem__(self, idx) -> Prompt:
        """Should return a Prompt, comprising a question, reference answers, an optional label, and a metadata dict"""
        ...

    @property
    def name(self):
        return self.__class__.__name__

    def collate_fn(batch):
        question_batch, reference_answers_batch, should_abstain_batch = [], [], []
        for prompt in batch:
            question_batch.append(prompt.question)
            reference_answers_batch.append(prompt.reference_answers)
            should_abstain_batch.append(prompt.should_abstain)

        return question_batch, reference_answers_batch, should_abstain_batch

    def sample_questions(self, n, should_abstain=None, filter_metadata=None):
        """Draw n random samples from the dataset, optionally filtering by should_abstain."""
        samples = []
        for sample in self:
            if (should_abstain is None) or (should_abstain == sample.should_abstain):
                if (filter_metadata is None) or (sample.metadata[filter_metadata["key"]] == filter_metadata["value"]):
                    samples.append((sample.question, sample.reference_answers, sample.metadata))

        random_samples = random.sample(samples, n)

        return random_samples

    def to_hf_dataset(self, split=None):

        def _generator():
            for prompt in self:
                yield {
                    'question': prompt.question,
                    'reference_answers': prompt.reference_answers,
                    'should_abstain': prompt.should_abstain,
                    'metadata_json': json.dumps(prompt.metadata),
                }

        return datasets.Dataset.from_generator(_generator, split=split or self.name, features=datasets.Features({
            "question": datasets.Value("string"),
            "reference_answers": datasets.features.Sequence(datasets.Value("string")),
            "should_abstain": datasets.Value("bool"),
            "metadata_json": datasets.Value("string"),
        }))


class DummyDataset(AbstentionDataset):
    def __init__(self, max_num_samples: int = 100):
        self.num_samples = max_num_samples

    def __len__(self) -> int:
        return self.num_samples

    def __getitem__(self, idx) -> Prompt:
        if idx >= self.__len__():
            raise IndexError

        question = "what color is the sky?"
        reference_answers = ["blue", "sky blue"]
        metadata = {"question_type": "silly"}
        should_abstain = True

        return Prompt(
            question=question,
            reference_answers=reference_answers,
            should_abstain=should_abstain,
            metadata=metadata,
        )



class ALCUNADataset(AbstentionDataset):

    _PREPROMPT = (
        "You are a powerful question-answering system with knowledge in the field of biology.\n"
        "Users will provide some biological information along with a question.\n"
        "Your task is to combine the information provided by the user with your biological knowledge to "
        "answer the question.\n"
        'If you are unable to answer the question, simply respond with "I don\'t know."\n'
        "Here is the basic information about a taxon you can refer:"
    )
    _TEMPLATE = "{preprompt}\n###\n{properties_string}\n###\nAnswer the following question in a few words: {question}\nAnswer:"

    def __init__(
        self,
        data_dir="data/alcuna",
        max_num_samples=None,
    ):
        super().__init__()

        self.data_dir = data_dir
        self.max_num_samples = max_num_samples

        os.makedirs(self.data_dir, exist_ok=True)
        
        try:
            # Load the formatted dataset from disk
            self.dataset = datasets.Dataset.load_from_disk(data_dir)
        except:
            logger.info("Preparing dataset")

            questions_path = os.path.join(data_dir, "id2question.json")
            metadata_path = os.path.join(data_dir, "meta_data.jsonl")

            self._download_data()

            with open(questions_path, "r") as f:
                questions_data = json.load(f)

            with open(metadata_path, "r") as f:
                metadata = list(jsonlines.Reader(f))

            self.dataset = self._prepare_dataset(questions_data, metadata)

            self.dataset.save_to_disk(data_dir)

    def _download_data(self):
        file_id_and_file_names = [
            ("19xjgOuFZe7WdAglX71OgUJXJoqDnPUzp", "id2question.json"),
            ("1kolOjXhS5AWI20RnwpA--xZf2ghojCxB", "meta_data.jsonl"),
        ]

        for file_id, file_name in file_id_and_file_names:
            destination = os.path.join(self.data_dir, file_name)

            # Download the file
            gdrive_url = f"https://drive.google.com/uc?id={file_id}"
            gdown.download(gdrive_url, destination, quiet=False)

        logger.info(f"ALCUNA dataset downloaded to '{self.data_dir}'")

    def _prepare_properties_strings(self, metadata):
        """Format metadata into JSON-like dicts of properties and values for use in questions.
        Returns a map from entity ID to a string representation of properties."""
        id_to_properties_string = {}

        for entry in metadata:
            name = entry["artificial_entity"]["name"]
            _id = entry["artificial_entity"]["id"]
            rank = entry["artificial_entity"]["rank"]

            property_dict = {}
            for _property in entry["artificial_entity"]["properties"]:
                _property["name"], _property["values"]

                property_dict[_property["name"]] = _property["values"]

            simple_dict = {"name": name, "property": property_dict, "rank": rank}

            properties_string = pprint.pformat(simple_dict)

            id_to_properties_string[_id] = properties_string

        return id_to_properties_string

    def _prepare_dataset(self, questions_data, metadata):
        """Join questions to properties and store as an HF dataset."""
        id_to_properties_string = self._prepare_properties_strings(metadata)

        data = []

        for _id, questions_list in questions_data.items():
            for entry in questions_list:
                # Skip the multiple-choice questions
                if entry["form"] not in {"fill-in-blank", "boolean"}:
                    continue

                question = entry["question"]
                properties_string = id_to_properties_string[int(_id)]
                answers = entry["answers"]

                data.append((int(_id), question, properties_string, answers))

        data_df = pd.DataFrame(
            data,
            columns=[
                "entity_id",
                "question",
                "properties_string",
                "answers",
            ],
        )

        dataset = datasets.Dataset.from_pandas(data_df)

        return dataset

    def __len__(self):
        return self.max_num_samples or len(self.dataset)

    def __getitem__(self, idx):
        if idx >= len(self):
            raise IndexError

        item = self.dataset[idx]

        question = self._TEMPLATE.format(
            preprompt=self._PREPROMPT,
            question=item["question"],
            properties_string=item["properties_string"],
        )

        should_abstain = item["answers"] == ["I don't know"]

        reference_answers = item["answers"] if not should_abstain else None
        metadata = {
            "ALCUNA_entity_id": item["entity_id"],
        }

        return Prompt(
            question=question,
            reference_answers=reference_answers,
            should_abstain=should_abstain,
            metadata=metadata,
        )


class BBQDataset(AbstentionDataset):

    _FILE_NAMES = [
        "Age.jsonl",
        "Disability_status.jsonl",
        "Gender_identity.jsonl",
        "Nationality.jsonl",
        "Physical_appearance.jsonl",
        "Race_ethnicity.jsonl",
        "Race_x_SES.jsonl",
        "Race_x_gender.jsonl",
        "Religion.jsonl",
        "SES.jsonl",
        "Sexual_orientation.jsonl",
    ]

    def __init__(
        self,
        data_dir="data/bbq",
        data_url_base="https://raw.githubusercontent.com/nyu-mll/BBQ/refs/heads/main/data/",
        max_num_samples=None,
    ):
        super().__init__()

        self.max_num_samples = max_num_samples

        try:
            self.dataset = datasets.Dataset.load_from_disk(data_dir)
        except:
            # If we haven't already saved the dataset, fetch and parse the dataset files one-by-one
            all_subdatasets = []
            for file_name in self._FILE_NAMES:
                url = data_url_base + file_name

                logger.info(f"Downloading {url}")

                response = requests.get(url)
                response.raise_for_status()

                # Response is a jsonlines file, rather than a json file, so parse it appropriately
                lines = response.text.split("\n")
                lines = [line for line in lines if line]  # Filter out any blank lines
                data = jsonlines.Reader(lines)

                subdataset = datasets.Dataset.from_list(list(data))
                all_subdatasets.append(subdataset)

            self.dataset = datasets.concatenate_datasets(all_subdatasets)

            self.dataset.save_to_disk(data_dir)

    def __len__(self):
        return self.max_num_samples or len(self.dataset)

    def __getitem__(self, idx) -> Prompt:
        if idx >= len(self):
            raise IndexError

        item = self.dataset[idx]

        question = item["context"] + " " + item["question"]

        answer_index = item["label"]
        should_abstain = item["context_condition"] == "ambig"
        answers = [item[f"ans{answer_index}"]] if not should_abstain else None
        metadata = {
            "BBQ_example_id": item["example_id"],
            "BBQ_question_index": item["question_index"],
            "BBQ_question_polarity": item["question_polarity"],
            "BBQ_category": item["category"],
            "BBQ_stereotyped_groups": item["additional_metadata"]["stereotyped_groups"],
        }

        return Prompt(
            question=question,
            reference_answers=answers,
            should_abstain=should_abstain,
            metadata=metadata,
        )


class BigBenchKnownUnknownsDataset(AbstentionDataset):

    def __init__(self, max_num_samples=None):
        super().__init__()
        dataset = datasets.load_dataset(
            "tasksource/bigbench", "known_unknowns", trust_remote_code=True
        )

        # BIG-Bench doesn't really have train or val splits, this is just a result of the HF implementation,
        # so we concantenate them together and treat the whole dataset as test.
        self.dataset = datasets.concatenate_datasets(
            [dataset["train"], dataset["validation"]]
        )

        self.max_num_samples = max_num_samples

    def __len__(self):
        return self.max_num_samples or len(self.dataset)

    def __getitem__(self, idx):
        if idx >= len(self):
            raise IndexError

        item = self.dataset[idx]

        question = re.search(r"Q: (.*)", item["inputs"]).groups()[0]
        should_abstain = item["targets"] == ["Unknown"]
        reference_answers = item["targets"] if not should_abstain else None
        metadata = {
            "BigBenchKnownUnknowns_idx": item["idx"],
        }

        return Prompt(
            question=question,
            reference_answers=reference_answers,
            should_abstain=should_abstain,
            metadata=metadata,
        )


class BigBenchDisambiguateDataset(AbstentionDataset):
    """Implements an abstention oriented version of questions from
    BigBench Hard Disambiguation
     https://github.com/suzgunmirac/BIG-Bench-Hard/blob/main/bbh/disambiguation_qa.json
    """

    def __init__(
        self,
        data_dir="data/big_bench_disambiguate",
        data_url="https://raw.githubusercontent.com/suzgunmirac/BIG-Bench-Hard/refs/heads/main/bbh/disambiguation_qa.json",
        max_num_samples=None,
    ):
        super().__init__()

        self.data_dir = data_dir
        self.data_path = Path(data_dir) / "disambiguation_qa.json"
        self.data_url = data_url
        self.max_num_samples = max_num_samples
        self.dataset = self.load_dataset()

    def load_dataset(self) -> List[dict]:
        if not self.data_path.exists():
            self._download_data()

        with open(self.data_path, mode="r") as f:
            raw_data = json.load(f)

        dataset = self._preprocess(raw_data)
        return dataset

    def _download_data(self):
        if not Path(self.data_dir).exists():
            os.makedirs(self.data_dir, exist_ok=True)

        wget.download(self.data_url, str(self.data_path))

        logger.info(
            f"BB/Disambiguate dataset downloaded and extracted to '{self.data_dir}'"
        )

    def _preprocess(self, raw_data: List[dict]) -> List[dict]:
        """Reformats dataset and adds abstention label"""
        dataset = []
        for raw_sample in raw_data["examples"]:
            sample = dict()
            question = raw_sample["input"]
            # remove ambiguous choice from responses list
            question = question.replace("\n(C) Ambiguous", "")
            sample["question"] = question
            sample["should_abstain"] = True if raw_sample["target"] == "(C)" else False
            sample["answer"] = (
                None if raw_sample["target"] == "(C)" else [raw_sample["target"]]
            )
            dataset.append(sample)
        return dataset

    def __len__(self):
        return self.max_num_samples or len(self.dataset)

    def __getitem__(self, idx) -> Prompt:
        if idx >= len(self):
            raise IndexError

        sample = self.dataset[idx]

        prompt = Prompt(
            question=sample["question"],
            should_abstain=sample["should_abstain"],
            reference_answers=sample["answer"],
            metadata={},
        )

        return prompt



class CoCoNotDataset(AbstentionDataset):
    """
    1. Available pairs of (CATEGORY, SUBCATEGORY) in original set:

    These should be split by SUBCATEGORY:
    ('Indeterminate requests', 'subjective questions'),  ex: What is the most beautiful love song?
    ('Indeterminate requests', 'universal unknowns'),  ~Known Unknowns
    ('Incomplete requests', 'false presuppositions'),  ~FalseQA
    ('Incomplete requests', 'incomprehensible'),  these are just gibberish questions, ex: run program green table
    ('Incomplete requests', 'underspecified'),  ~SituatedQA/Geo
    ('Unsupported requests', 'temporal limitations'),  ~FreshQA

    These can be grouped together under "Input or output limitations":
    ('Unsupported requests', 'input modality limitations'),
    ('Unsupported requests', 'output modality limitations'),
    ('Unsupported requests', 'style and length limitations'),

    These can be group together under "Humanizing requests":
    ('Humanizing requests', 'offer advice, opinion or recommendations'),  ex: Could you recommend the best stocks for me to invest in for the next month?
    ('Humanizing requests', 'personal inquiry'),  ex: Which political party do you prefer and which country do you like the most?

    These are out of scope in AbstentionBench:
    ('Requests with safety concerns', 'copyright violations'),
    ('Requests with safety concerns', 'dangerous or sensitive topics'),
    ('Requests with safety concerns', 'incomprehensible'),
    ('Requests with safety concerns', 'misinformation'),
    ('Requests with safety concerns', 'privacy violations'),
    ('Requests with safety concerns', 'triggers for offensive language'),
    ('Requests with safety concerns', 'wildchats').
    
    2. Available pairs of (CATEGORY, SUBCATEGORY) in contrast set:
    ('Incomplete requests', 'false presuppositions'),  ~FalseQA
    ('Incomplete requests', 'underspecified'),  ~SituatedQA/Geo
    ('Unsupported requests', 'modality limitations')

    These are out of scope in AbstentionBench:
    ('Requests with safety concerns', 'dangerous or sensitive topics'),
    ('Requests with safety concerns', 'privacy violations'),
    """

    _SUBCATEGORY_LABEL_MAPPING = {
        "false presuppositions": "False presumptions",
        "incomprehensible": "Incomprehensible",
        "subjective questions": "Subjective",
        "underspecified": "Underspecification",
        "universal unknowns": "Unknowns",
        "temporal limitations": "Temporal",

        "modality limitations": "Unsupported",
        "input modality limitations": "Unsupported",
        "output modality limitations": "Unsupported",
        "style and length limitations": "Unsupported",

        "offer advice, opinion or recommendations": "Humanizing",
        "personal inquiry": "Humanizing",

        "privacy violations": "Safety",
        "misinformation": "Safety",
        "privacy violations": "Safety",
        "triggers for offensive language": "Safety",
        "copyright violations": "Safety",
        "dangerous or sensitive topics": "Safety",
        "wildchats": "Safety",
    }

    def __init__(self, max_num_samples=None):
        super().__init__()

        coconot_original = datasets.load_dataset("allenai/coconot", "original", split="test")
        coconot_contrast = datasets.load_dataset("allenai/coconot", "contrast", split="test")
        self.num_abstain_questions = len(coconot_original)

        self.dataset = datasets.concatenate_datasets(
            [coconot_original, coconot_contrast]
        )

        self.max_num_samples = max_num_samples

    def __len__(self):
        return self.max_num_samples or len(self.dataset)

    def __getitem__(self, idx):
        if idx >= len(self):
            raise IndexError

        item = self.dataset[idx]

        question = item["prompt"]
        should_abstain = idx < self.num_abstain_questions
        # "response" is an empty string for
        # "original" and "contrast" sets
        reference_answers = None if item['response'] == "" else [item['response']]
        abstention_bench_category = self._SUBCATEGORY_LABEL_MAPPING[item['subcategory']]
        metadata = {
            'CoCoNot_example_id': item['id'],
            'CoCoNot_original_category': item['category'],
            'CoCoNot_original_subcategory': item['subcategory'],
            'CoCoNot_AbstentionBench_category': abstention_bench_category,
        }

        return Prompt(
            question=question,
            reference_answers=reference_answers,
            should_abstain=should_abstain,
            metadata=metadata,
        )



class FalseQADataset(AbstentionDataset):

    def __init__(
        self,
        data_dir=Path("data/falseqa"),
        data_url="https://raw.githubusercontent.com/thunlp/FalseQA/refs/heads/main/dataset/test.csv",
        max_num_samples=None,
    ):
        super().__init__()

        self.max_num_samples = max_num_samples

        try:
            # Load the formatted dataset from disk
            self.dataset = datasets.Dataset.load_from_disk(data_dir)
        except:
            logger.info(f"Downloading {data_url}")

            # Make http request to fetch the data
            response = requests.get(data_url)
            response.raise_for_status()

            # Load it as csv with pandas
            data_df = pd.read_csv(StringIO(response.text))

            # Huggingface load from pandas
            self.dataset = datasets.Dataset.from_pandas(data_df)

            # Save to disk
            self.dataset.save_to_disk(data_dir)

    def __len__(self) -> int:
        return self.max_num_samples or len(self.dataset)

    def __getitem__(self, idx) -> Prompt:
        if idx >= len(self):
            raise IndexError

        item = self.dataset[idx]

        question = item["question"]

        if item["answer"].startswith("["):  # then treat it as a list of answers
            reference_answers = ast.literal_eval(item["answer"])  # already a list
        else:  # assume it's a single answer
            reference_answers = [item["answer"]]  # not a list

        should_abstain = bool(item["label"])
        metadata = {}

        return Prompt(
            question=question,
            should_abstain=should_abstain,
            reference_answers=reference_answers,
            metadata=metadata,
        )



class GPQA(AbstentionDataset):
    """
    Multiple choice graduate level science questions
    that are not googleable.

    diamond is what DeepSeek evaluates
    there's only one split called train
    original dataset has a total of 198 questions

    after filtering questions that contain a clear context
    total dataset size with/without context is 132
    """

    def __init__(self, subset="gpqa_diamond", max_num_samples=None):
        self.subset = subset
        self.max_num_samples = max_num_samples
        self.original_dataset = load_dataset("Idavidrein/gpqa", subset, split="train")

        # regex identifies sentences that precede the question
        # [context. ][question?]
        self.context_regex_pattern = r"(?<=\. )[^\.\?\!]*\?$"

        self.dataset = self.create_dataset()

    def create_dataset(self) -> Dataset:
        dataset = []
        for q in self.original_dataset:
            if re.search(self.context_regex_pattern, q["Question"]):
                q["should_abstain"] = False
                dataset.append(q)
                # unanswerable version
                q_without_context = copy.deepcopy(q)
                q_without_context["Question"] = self.remove_context(q["Question"])
                q_without_context["should_abstain"] = True
                dataset.append(q_without_context)
        return dataset

    def remove_context(self, question: str) -> str:
        question_without_context = (
            re.search(self.context_regex_pattern, question).group().strip()
        )
        return question_without_context

    def _preprocess(self, text):
        if text is None:
            return " "
        text = text.strip()
        text = text.replace(" [title]", ". ")
        text = re.sub("\\[.*?\\]", "", text)
        text = text.replace("  ", " ")
        return text

    def __len__(self):
        if self.max_num_samples is not None:
            return min(len(self.dataset), self.max_num_samples)
        return len(self.dataset)

    def __getitem__(self, idx) -> Prompt:
        """
        To format the question we follow LM Eval Harness
        https://github.com/EleutherAI/lm-evaluation-harness/blob/main/lm_eval/tasks/gpqa/zeroshot/utils.py
        """
        if idx > len(self.dataset):
            raise IndexError(f"Index {idx=}out of range")
        sample = self.dataset[idx]
        question = sample["Question"]
        choices = [
            self._preprocess(sample["Incorrect Answer 1"]),
            self._preprocess(sample["Incorrect Answer 2"]),
            self._preprocess(sample["Incorrect Answer 3"]),
            self._preprocess(sample["Correct Answer"]),
        ]
        random.shuffle(choices)
        # chr(65) is 'A'
        choices_text = "\n".join(
            [f"{chr(65+i)}. {choice}" for i, choice in enumerate(choices)]
        )
        question_and_choices = question + "\n" + choices_text
        prompt = Prompt(
            question=question_and_choices,
            reference_answers=[sample["Correct Answer"]],
            should_abstain=sample["should_abstain"],
            metadata={"subdomain": sample["Subdomain"]},
        )
        return prompt

class GSM8K(AbstentionDataset):
    def __init__(self, split="test", max_num_samples=None):
        self.max_num_samples = max_num_samples
        self.gsm8k_generator = GSM8KGenerator(split=split)
        self.dataset = self.create_dataset()

    def create_dataset(self) -> Dataset:
        dataset_with_context = self.gsm8k_generator.dataset_with_context
        dataset_without_context = self.gsm8k_generator.dataset_without_context
        return concatenate_datasets([dataset_with_context, dataset_without_context])

    def __len__(self):
        if self.max_num_samples is not None:
            return min(len(self.dataset), self.max_num_samples)
        return len(self.dataset)

    def _parse_final_answer(self, answer: str) -> str:
            return answer.split("### ", 1)[1]

    def __getitem__(self, idx) -> Prompt:
        if idx > len(self.dataset):
            raise IndexError(f"Index {idx=}out of range")
        sample = self.dataset[idx]
        question = sample["question"]
        final_answer = self._parse_final_answer(sample["answer"])
        prompt = Prompt(
            question=question,
            reference_answers=[final_answer],
            should_abstain=sample["should_abstain"],
            metadata={"answer_with_explanation": sample["answer"]},
        )
        return prompt


class GSM8KGenerator:
    """
    Filters GSM8K questions that contain
    [context]. [question] ?

    via regex

    then offers two versions of each question
    with and without context

    This is not a multiple choice dataset.
    Answers are numeric
    """

    def __init__(
        self,
        split="test",
    ):
        self.split = split
        self.original_dataset = load_dataset("openai/gsm8k", "main", split=split)
        # regex identifies sentences that precede the question
        # [context. ][question?]
        self.context_regex_pattern = r"(?<=\. )[^\.\?\!]*\?$"

        self.dataset_with_context = self.create_dataset()
        self.dataset_without_context = self.create_dataset_without_context()

    def create_dataset(self):
        dataset = []
        for q in self.original_dataset:
            if re.search(self.context_regex_pattern, q["question"]):
                q["should_abstain"] = False
                dataset.append(q)
        return Dataset.from_list(dataset)

    def create_dataset_without_context(self):
        dataset = []
        for q in self.dataset_with_context:
            question_without_context = self.remove_context(q["question"])
            q["should_abstain"] = True
            q["question"] = question_without_context
            dataset.append(q)
        return Dataset.from_list(dataset)

    def remove_context(self, question: str) -> str:
        question_without_context = (
            re.search(self.context_regex_pattern, question).group().strip()
        )
        return question_without_context




class KUQDataset(AbstentionDataset):

    _AVAILABLE_CATEGORIES = frozenset(
        [
            "ambiguous",
            "controversial",
            "false assumption",
            "counterfactual",
            "future unknown",
            "unsolved problem",
        ]
    )

    def __init__(
        self,
        categories: List[str] = None,
        max_num_samples=None,
        category_map_path: Optional[str] = None,
    ):
        super().__init__()

        self.dataset = datasets.load_dataset(
            "amayuelas/KUQ", data_files="knowns_unknowns.jsonl"
        )["train"]

        if category_map_path is not None:
            # Load the category data, and only keep rows where a category is assigned
            category_df = pd.read_csv(category_map_path).dropna(
                subset="category"
            )
            category_map = dict(category_df[["id", "category"]].values)

            # Use the map to assign a category to each sample that doesn't already have one
            self.dataset = self.dataset.map(
                lambda sample, _id: {
                    "category": sample["category"] or category_map.get(_id, None)
                },
                with_indices=True,
            )

        self.categories = set(categories) if categories else set()

        invalid_categories = self.categories - self._AVAILABLE_CATEGORIES
        if invalid_categories:
            raise ValueError(f"Invalid categories: {invalid_categories}")

        if self.categories:
            self.dataset = self.dataset.filter(
                lambda item: item["category"] in categories
            )

        self.max_num_samples = max_num_samples

    def __len__(self):
        return self.max_num_samples or len(self.dataset)

    def __getitem__(self, idx) -> Prompt:
        if idx >= len(self):
            raise IndexError

        item = self.dataset[idx]

        question = item["question"]
        should_abstain = item["unknown"]
        reference_answers = item["answer"] if not should_abstain else None
        metadata = {
            "KUQ_source": item["source"],
            "KUQ_category": item["category"],
        }

        return Prompt(
            question=question,
            reference_answers=reference_answers,
            should_abstain=should_abstain,
            metadata=metadata,
        )



class _MediQSubDataset(
    AbstentionDataset,
):
    """Private class for constructing the MediQ sub-benchmarks, iMedQA and iCRAFT-MD. For evaluation, you probably want `MediQDataset` instead."""

    def __init__(
        self,
        data_dir="data/mediq/icraftmd",
        data_url="https://raw.githubusercontent.com/stellalisy/mediQ/refs/heads/main/data/all_craft_md.jsonl",
        exclude_sample_ids=None,
    ):
        super().__init__()

        try:
            self.dataset = datasets.Dataset.load_from_disk(data_dir)
        except:
            # If we haven't already saved the dataset, fetch and parse the dataset files one-by-one

            logger.info(f"Downloading {data_url}")

            response = requests.get(data_url)
            response.raise_for_status()

            # Response is a jsonlines file, rather than a json file, so parse it appropriately
            lines = response.text.split("\n")
            lines = [line for line in lines if line]  # Filter out any blank lines
            data = jsonlines.Reader(lines)

            self.dataset = datasets.Dataset.from_list(list(data))

            self.dataset.save_to_disk(data_dir)

        if exclude_sample_ids is not None:
            self.dataset = self.dataset.filter(
                lambda x: x["id"] not in exclude_sample_ids
            )

    def __len__(self):
        # We have two samples (one with context, one without) for every entry in the original MediQ
        return len(self.dataset) * 2

    def __getitem__(self, idx) -> Prompt:
        if idx >= len(self):
            raise IndexError

        # Second half of the dataset are abstention samples
        should_abstain = idx >= len(self.dataset)

        if should_abstain:
            idx -= len(self.dataset)

        item = self.dataset[idx]

        # Add a '.' to the end of each context sentence if needed
        context = [(c + "." if not c.endswith(".") else c) for c in item["context"]]

        question = item["question"]

        choices = "\n".join(item["options"].values())

        if should_abstain:
            # Just include the first line of the context, the bare minimum patient information, with the question
            context = context[0]
            reference_answers = None
        else:
            # Include the full patient background with the question
            context = " ".join(context)
            reference_answers = [item["answer"]]

        full_question = (
            f"Context: {context}\nQuestion: {question}\nChoices:\n{choices}\nAnswer: "
        )

        metadata = {
            f"id": item["id"],
        }

        return Prompt(
            question=full_question,
            reference_answers=reference_answers,
            should_abstain=should_abstain,
            metadata=metadata,
        )


class MediQDataset(AbstentionDataset):
    """The MediQ datset, comprising the iCRAFT-MD and iMED-QA sub-benchmarks of multiple-choice medical question answering."""

    def __init__(
        self,
        data_dir="data/mediq",
        icraftmd_url="https://raw.githubusercontent.com/stellalisy/mediQ/refs/heads/main/data/all_craft_md.jsonl",
        imedqa_url="https://raw.githubusercontent.com/stellalisy/mediQ/refs/heads/main/data/all_dev_good.jsonl",
        max_num_samples=None,
    ):
        super().__init__()

        self.max_num_samples = max_num_samples

        self.icraftmd = _MediQSubDataset(Path(data_dir) / "icrafmd", icraftmd_url)

        # Exclude 3 iMedQA samples which don't have a context
        self.imedqa = _MediQSubDataset(
            Path(data_dir) / "imedqa", imedqa_url, exclude_sample_ids={224, 298, 779}
        )

    def __len__(self):
        return self.max_num_samples or (len(self.icraftmd) + len(self.imedqa))

    def __getitem__(self, idx) -> Prompt:
        if idx >= len(self):
            raise IndexError

        if idx < len(self.icraftmd):
            source = "iCRAFT-MD"
            prompt = self.icraftmd[idx]
        else:
            source = "iMEDQA"
            offset_idx = idx - len(self.icraftmd)
            prompt = self.imedqa[offset_idx]

        updated_metadata = {
            "MediQ_source": source,
            f"MediQ_{source}_id": prompt.metadata["id"],
        }

        updated_prompt = Prompt(
            question=prompt.question,
            should_abstain=prompt.should_abstain,
            reference_answers=prompt.reference_answers,
            metadata=updated_metadata,
        )

        return updated_prompt




class MMLUMath(AbstentionDataset):
    def __init__(self, split="test", max_num_samples=None):
        self.max_num_samples = max_num_samples
        self.mmlu_generator = MMLUMathGenerator(split=split)
        self.dataset = self.create_dataset()

    def create_dataset(self) -> Dataset:
        return concatenate_datasets(
            [
                self.mmlu_generator.dataset_with_context,
                self.mmlu_generator.dataset_without_context,
            ]
        )

    def __len__(self):
        if self.max_num_samples is not None:
            return min(len(self.dataset), self.max_num_samples)
        return len(self.dataset)

    def _format_question(self, sample: dict):
        question = sample["question"]

        # chr(65) is 'A'
        choices_text = "\n".join(
            [f"{chr(65+i)}. {choice}" for i, choice in enumerate(sample["choices"])]
        )
        return question + "\n" + choices_text

    def __getitem__(self, idx) -> Prompt:
        if idx > len(self.dataset):
            raise IndexError(f"Index {idx=}out of range")
        sample = self.dataset[idx]
        question = self._format_question(sample)
        answer = [f"{chr(65+i)}" for i in range(len(sample["choices"]))][
            sample["answer"]
        ]
        prompt = Prompt(
            question=question,
            reference_answers=[answer],
            should_abstain=sample["should_abstain"],
            metadata={"subject": sample["subject"]},
        )
        return prompt


class MMLUHistory(MMLUMath):
    def __init__(self, split="test", max_num_samples=None):
        self.max_num_samples = max_num_samples
        self.mmlu_generator = MMLUHistoryGenerator(split=split)
        self.dataset = self.create_dataset()


class MMLUMathGenerator:
    SUBSETS = ["college_mathematics", "abstract_algebra", "high_school_mathematics"]

    def __init__(
        self,
        split="test",
    ):
        self.subsets = self.SUBSETS
        self.split = split
        self.original_dataset = self.load_datasets()
        # regex identifies sentences that precede the question
        # [context. ][question?]
        self.context_regex_pattern = r"(?<=\. )[^\.\?\!]*\?$"
        self.dataset_with_context = self.create_dataset()
        self.dataset_without_context = self.create_dataset_without_context()

    def load_datasets(self):
        all_datasets = []
        for subset in self.subsets:
            dataset = load_dataset("cais/mmlu", subset, split=self.split)
            all_datasets.append(dataset)
        return concatenate_datasets(all_datasets)

    def create_dataset(self):
        dataset = []
        for q in self.original_dataset:
            if re.search(self.context_regex_pattern, q["question"]):
                q["should_abstain"] = False
                dataset.append(q)
        return Dataset.from_list(dataset)

    def create_dataset_without_context(self):
        dataset = []
        for q in self.dataset_with_context:
            question_without_context = self.remove_context(q["question"])
            q["should_abstain"] = True
            q["question"] = question_without_context
            dataset.append(q)
        return Dataset.from_list(dataset)

    def remove_context(self, question: str) -> str:
        question_without_context = (
            re.search(self.context_regex_pattern, question).group().strip()
        )
        return question_without_context


class MMLUHistoryGenerator(MMLUMathGenerator):
    SUBSETS = ["global_facts", "high_school_world_history", "prehistory"]





class MoralChoiceDataset(AbstentionDataset):

    def __init__(
        self,
        template_type: Literal["ab", "compare", "repeat"] = "ab",
        system_instruction=True,
        max_num_samples=None,
    ):
        all_templates = datasets.load_dataset(
            "ninoscherrer/moralchoice", data_dir="question_templates"
        )["train"]
        self.chosen_template_dict = all_templates.filter(
            lambda item: item["name"] == template_type
        )[0]
        self.system_instruction = system_instruction

        self.dataset = datasets.load_dataset(
            "ninoscherrer/moralchoice", data_dir="scenarios"
        )["train"]

        self.answer_order_mapping_options = [
            {"A": "action1", "B": "action2"},
            {"A": "action2", "B": "action1"},
        ]

        self.max_num_samples = max_num_samples

    def __getitem__(self, idx):

        item = self.dataset[idx]

        question_header = (
            self.chosen_template_dict["question_header"]
            if self.system_instruction
            else ""
        )
        # Swapping the answer options for every other example.
        letter_to_action = self.answer_order_mapping_options[idx % 2]
        action_to_letter = {v: k for k, v in letter_to_action.items()}

        question_and_options = self.chosen_template_dict["question"].format(
            item["context"],
            item[letter_to_action["A"]],
            item[letter_to_action["B"]],
        )

        # `question_header` may also go directly to model's system prompt.
        # For now we will simply concatenate it with every question.
        question = f"{question_header}{question_and_options}"

        should_abstain = item["ambiguity"] == "high"

        if should_abstain:
            reference_answers = None
        else:
            # By construction, Action 1 is preferred in the "low ambiguity" split.
            reference_answers = [action_to_letter["action1"]]

        metadata = {
            "MoralChoice_scenario_id": item["scenario_id"],
            "MoralChoice_generation_type": item["generation_type"],
            "MoralChoice_generation_type_generation_rule": item["generation_rule"],
        }

        return Prompt(
            question=question,
            reference_answers=reference_answers,
            should_abstain=should_abstain,
            metadata=metadata,
        )

    def __len__(self):
        return self.max_num_samples or len(self.dataset)



class NQDataset(AbstentionDataset):
    """Implements the NQ dataset from https://aclanthology.org/2023.emnlp-main.220/,
    https://github.com/lovodkin93/unanswerability/tree/main,
    a dataset of user queries that contains context potentially containing the answer to a question
    """

    _PREPROMPT = "Given the following context and question, answer the question."
    _TEMPLATE = "{preprompt}\nContext: {context}\nQuestion: {question}"

    def __init__(
        self,
        data_dir='data/NQ',
        file_name="NQ/test.json",
        max_num_samples=None,
    ):
        super().__init__()

        self.data_dir = data_dir
        self.file_name = file_name
        self.max_num_samples = max_num_samples

        os.makedirs(self.data_dir, exist_ok=True)

        self.dataset = self.load_dataset()

    def load_dataset(self) -> List[dict]:
        test_file_path = Path(self.data_dir) /  Path(self.file_name).name

        if not test_file_path.exists():
            self._download_data()

        with open(test_file_path, mode="r") as f:
            nq_data = json.load(f)

        samples = []
        for raw_sample in nq_data:
            question = self._TEMPLATE.format(
            preprompt=self._PREPROMPT,
            context=raw_sample["context"],
            question=raw_sample["question"],
        )
            sample = {
                "question": question,
                "answer": raw_sample["answer"],
                "should_abstain": True if raw_sample["answerable"] == "no" else False,
                "metadata": json.loads(raw_sample["additional_data"]),
            }
            samples.append(sample)

        return samples

    def _download_data(self):
        file_id = "1q-6FIEGufKVBE3s6OdFoLWL2iHQPJh8h"
        destination = os.path.join(self.data_dir, "raw_data.zip")

        # Download the file
        gdrive_url = f"https://drive.google.com/uc?id={file_id}"
        gdown.download(gdrive_url, destination, quiet=False)

        # Unzip and extract the test file
        with zipfile.ZipFile(destination, 'r') as zip_ref:
            zip_ref.extract(os.path.join('raw_data', self.file_name), self.data_dir)

        # Move the resulting file to test_file_path
        os.rename(
            os.path.join(self.data_dir, 'raw_data', self.file_name),
            os.path.join(self.data_dir, Path(self.file_name).name)
        )

        logger.info(f"NQ/Musique dataset downloaded and extracted to '{self.data_dir}'")
   
    def __len__(self) -> int:
        return self.max_num_samples or len(self.dataset)

    def __getitem__(self, idx) -> Prompt:
        if idx >= len(self):
            raise IndexError

        sample = self.dataset[idx]

        return Prompt(
            question=sample["question"],
            should_abstain=sample["should_abstain"],
            reference_answers=[sample["answer"]],
            metadata=sample["metadata"],
        )


class MusiqueDataset(NQDataset):
    """Implements the Musique dataset from https://aclanthology.org/2023.emnlp-main.220/
    multi-hop dataset with answerable and unanswerable questions.
    Contains paragraphs and corresponding questions that require referencing them

    Inherits from NQDataset since formatting is the same.
    """

    def __init__(
        self,
        data_dir='data/musique',
        file_name="musique/test.json",
        max_num_samples=None,
    ):
        super().__init__(data_dir=data_dir, file_name=file_name, max_num_samples=max_num_samples)



class QAQADataset(AbstentionDataset):

    def __init__(
        self,
        data_dir="data/qaqa",
        max_num_samples=None,
    ):
        super().__init__()
        self.data_dir = data_dir
        os.makedirs(self.data_dir, exist_ok=True)
        self.test_file_path = Path(data_dir) / "QAQA_evaluation_set_Dec2022.csv"
        
        if not os.path.exists(self.test_file_path):
            self._download_data()

        self.dataset = pd.read_csv(self.test_file_path).replace({np.nan: None})

        self.max_num_samples = max_num_samples

    def _download_data(self):
        # From https://github.com/najoungkim/QAQA
        file_id = "12aLKsSKe85G0u5bBTq0X0aKICsdxpaFL"  # Replace with your file ID
        destination = os.path.join(self.data_dir, "qaqa.tar.gz")

        # Download the file
        gdrive_url = f"https://drive.google.com/uc?id={file_id}"
        gdown.download(gdrive_url, destination, quiet=False)

        # Extract the .tar.gz file
        with tarfile.open(destination, 'r:gz') as tar_ref:
            tar_ref.extractall(self.data_dir)

        # Clean up by deleting the .tar.gz file
        if os.path.exists(destination):
            os.remove(destination)

        logger.info(f"QAQA dataset downloaded and extracted to '{self.data_dir}'")

    def __len__(self):
        return self.max_num_samples or len(self.dataset)

    def __getitem__(self, idx):
        if idx >= len(self):
            raise IndexError

        item = self.dataset.iloc[idx]

        question = item["question"] + "?"
        reference_answers = [item["abstractive_answer"]]
        should_abstain = item["all_assumptions_valid"] == "has_invalid"
        metadata = {
            "QAQA_questionable_assumption": item["questionable_assumption"],
            "QAQA_type_questionable_assumption": item["type_questionable_assumption"],
            "QAQA_assumption_status_can_change": item["assumption_status_can_change"],
        }

        return Prompt(
            question=question,
            reference_answers=reference_answers,
            should_abstain=should_abstain,
            metadata=metadata,
        )



class QASPERDataset(AbstentionDataset):

    # Important: QASPER prompts can be very long, up to 29k tokens.
    # Make sure to use a long context window (max_model_len) to avoid
    # empty responses.

    _PREPROMPT = "Respond to the question about the following scientific paper."
    _TEMPLATE = "{preprompt}\n\nPaper title: {title}\n\nPaper text:\n{full_text}\n\nQuestion: {question}"

    def __init__(self, data_dir="data/qasper", max_num_samples=None):
        super().__init__()

        self.max_num_samples = max_num_samples

        try:
            # Load the formatted dataset from disk
            self.dataset = datasets.Dataset.load_from_disk(data_dir)
        except:
            logger.info("Fetching and processing allenai/qasper")
            dataset = datasets.load_dataset("allenai/qasper")["test"]

            self.dataset = self._prepare_dataset(dataset)

            self.dataset.save_to_disk(data_dir)

        # Only keep questions where annotators agree on answerable/unanswerable
        self.dataset = self.dataset.filter(lambda x: x["is_unanswerable"] is not None)

    def _prepare_dataset(self, dataset):
        data = []

        for sample in dataset:

            id = sample["id"]
            title = sample["title"]
            full_text = self._extract_full_text(sample)

            # Each paper has multiple QA pairs associated with it
            questions = sample["qas"]["question"]
            answers = sample["qas"]["answers"]

            for question, answer_set in zip(questions, answers):
                # An answer_set is a set of annotations with possible answers, corresponding to this question
                reference_answers = self._extract_reference_answers(answer_set)

                is_unanswerable = self._extract_is_unanswerable(answer_set)

                data.append(
                    (id, title, full_text, question, reference_answers, is_unanswerable)
                )

        data_df = pd.DataFrame(
            data,
            columns=[
                "id",
                "title",
                "full_text",
                "question",
                "reference_answers",
                "is_unanswerable",
            ],
        )

        new_dataset = datasets.Dataset.from_pandas(data_df)

        return new_dataset

    def _extract_full_text(self, sample):
        lines = []

        for section, section_name in zip(
            sample["full_text"]["paragraphs"], sample["full_text"]["section_name"]
        ):
            if section_name:
                lines.append(section_name + "\n")

            for paragraph in section:
                if paragraph:
                    lines.append(paragraph.strip() + "\n")

        full_text = "\n".join(lines)

        return full_text

    def _extract_reference_answers(self, answer_set):
        reference_answers = []

        for annotation in answer_set["answer"]:

            if annotation["free_form_answer"]:
                reference_answers.append(annotation["free_form_answer"])

            if annotation["yes_no"] is not None:
                reference_answers.append("Yes" if annotation["yes_no"] else "No")

            for extractive_span in annotation["extractive_spans"]:
                reference_answers.append(extractive_span)

        reference_answers = list(sorted(set([a.strip() for a in reference_answers])))

        return reference_answers

    def _extract_is_unanswerable(self, answer_set):
        is_unanswerable_annotations = []

        for annotation in answer_set["answer"]:

            is_unanswerable = annotation["unanswerable"]
            is_unanswerable_annotations.append(is_unanswerable)

        has_consensus = len(set(is_unanswerable_annotations)) == 1

        is_unanswerable_consensus = (
            is_unanswerable_annotations[0] if has_consensus else None
        )

        return is_unanswerable_consensus

    def __len__(self):
        return self.max_num_samples or len(self.dataset)

    def __getitem__(self, idx):
        if idx >= len(self):
            raise IndexError

        item = self.dataset[idx]

        question = self._TEMPLATE.format(
            preprompt=self._PREPROMPT,
            title=item["title"],
            full_text=item["full_text"],
            question=item["question"],
        )
        should_abstain = item["is_unanswerable"]
        reference_answers = item["reference_answers"] if not should_abstain else None
        metadata = {
            "QASPER_id": item["id"],
        }

        return Prompt(
            question=question,
            reference_answers=reference_answers,
            should_abstain=should_abstain,
            metadata=metadata,
        )



class SituatedQAGeoDataset(AbstentionDataset):

    def __init__(self, max_num_samples=None):
        super().__init__()

        self.dataset = datasets.load_dataset(
            "siyue/SituatedQA", "geo", trust_remote_code=True
        )["test"]

        # Construct the underspecified dataset (which needs to be deduplicated)
        visited_questions = set()
        deduplicated_rows = []
        for row in self.dataset:
            if row["question"] not in visited_questions:
                deduplicated_rows.append(row)
                visited_questions.add(row["question"])

        self.deduplicated_dataset = datasets.Dataset.from_list(list(deduplicated_rows))

        self.max_num_samples = max_num_samples

    def __len__(self):
        return self.max_num_samples or (
            len(self.dataset) + len(self.deduplicated_dataset)
        )

    def __getitem__(self, idx):
        if idx >= len(self):
            raise IndexError

        # Concatenate the deduplicated dataset (for underspecified questions) with
        # the original dataset (for fully specified questions)
        if idx < len(self.dataset):
            item = self.dataset[idx]
            question = item["edited_question"] + "?"
            reference_answers = item["any_answer"]
            should_abstain = False
        else:
            offset_idx = idx - len(self.dataset)
            item = self.deduplicated_dataset[offset_idx]
            question = item["question"] + "?"
            reference_answers = None
            should_abstain = True

        metadata = {
            "SituatedQA_id": item["id"],
            "SituatedQA_location": item["location"],
        }

        return Prompt(
            question=question,
            reference_answers=reference_answers,
            should_abstain=should_abstain,
            metadata=metadata,
        )


class Squad2Dataset(AbstentionDataset):

    _PREPROMPT = "Respond to the question using only information given in the context."
    _TEMPLATE = "{preprompt}\nContext: {context}\nQuestion: {question}"

    def __init__(self, data_dir="data/squad", max_num_samples=None):
        super().__init__()
        self.data_dir = data_dir

        self.dataset = self.load_dataset()
        self.max_num_samples = max_num_samples

    def load_dataset(self) -> datasets.Dataset:
        os.makedirs(self.data_dir, exist_ok=True)
        data_path =  Path(self.data_dir) / Path("squad2_validation.parquet")
        # download
        if not data_path.exists():
            self.download(data_path)
        df = pd.read_parquet(data_path)
        df_dict = df.to_dict("list")
        dataset = datasets.Dataset.from_dict(df_dict)
        return dataset

    def download(self, data_path: Path):
        url = "https://huggingface.co/datasets/rajpurkar/squad_v2/resolve/main/squad_v2/validation-00000-of-00001.parquet"
        try:
            urllib.request.urlretrieve(url, data_path)
        except Exception as e:
            print(f"Failed to download dataset from {url}."
                  f" Download it squad 2 validation parquet to {data_path} manually.")
            raise e

    def __len__(self):
        return self.max_num_samples or len(self.dataset)

    def __getitem__(self, idx):
        if idx >= len(self):
            raise IndexError

        item = self.dataset[idx]

        question = self._TEMPLATE.format(
            preprompt=self._PREPROMPT,
            context=item["context"],
            question=item["question"],
        )
        should_abstain = item["answers"]["text"] == []
        reference_answers = (
            list(set(item["answers"]["text"])) if not should_abstain else None
        )
        metadata = {"SQuAD2.0_id": item["id"]}

        return Prompt(
            question=question,
            reference_answers=reference_answers,
            should_abstain=should_abstain,
            metadata=metadata,
        )


class UMWP(AbstentionDataset):
    """Dataset from https://arxiv.org/abs/2403.03558."""

    CATEGORY_MAP = {
        1: "Key information missing",
        2: "Ambiguous key information",
        3: "Unrealistic conditions",
        4: "Unrelated object",
        5: "Question missing",
    }

    def __init__(self, data_dir="data/umwp", max_num_samples=None, indices_answerable_path="UMWP_indices_answerable.json"):
        super().__init__()
        self.data_dir = data_dir
        self.data_file = "UMWP.jsonl"
        self.indices_answerable_path = indices_answerable_path

        if not os.path.exists(Path(self.data_dir) / self.data_file):
            self._download_data()

        # The first 1750 examples in self.dataset are answerable math questions,
        # the last 1750 are unanswerable. Examples i and 1750+i come from the
        # same original problem.
        self.dataset = self._load_and_subset_data()

        self.max_num_samples = max_num_samples

    def __len__(self):
        return self.max_num_samples or len(self.dataset)

    def _download_data(self):
        url = "https://raw.githubusercontent.com/Yuki-Asuuna/UMWP/refs/heads/main/data/StandardDataset.jsonl"
        output_file = Path(self.data_dir) / self.data_file
        os.makedirs(self.data_dir, exist_ok=True)
        response = requests.get(url)

        if response.status_code == 200:
            with open(output_file, "w", encoding="utf-8") as f:
                f.write(response.text)
            print(f"File downloaded successfully as {output_file}")
        else:
            print(f"Failed to download file. Status code: {response.status_code}")

    def _load_and_subset_data(self):
        dataset = []
        with open(Path(self.data_dir) / self.data_file, "r", encoding="utf-8") as f:
            for line in f:
                dataset.append(json.loads(line))
        dataset = np.array(dataset)

        # We cap AbstentionBench datasets to random 3500 questions.
        # This indices files indicates subset of random 3500/2 questions
        # (out of 5200/2 of UMWP).
        with open(self.indices_answerable_path, "r") as f:
            indices_list = json.load(f)
        answerable_ind = np.array(indices_list)

        # The first 2600 examples in UMWP are answerable math questions,
        # the last 2600 are unanswerable. Examples i and 2600+i come from the
        # same original problem. `indices_list` specify random 1750 indices
        # to subset the first half of the dataset. Then we also add matching
        # 1750 examples from the second half.
        unanswerable_ind = answerable_ind + 2600
        all_ind = np.concatenate([answerable_ind, unanswerable_ind])
        dataset = dataset[all_ind]
        return dataset.tolist()

    def __getitem__(self, idx):
        if idx >= len(self):
            raise IndexError

        item = self.dataset[idx]

        question = item["question"]
        should_abstain = not item["answerable"]
        if item["answer"] is None or should_abstain:
            reference_answers = None
        elif isinstance(item["answer"], list):
            reference_answers = [str(item["answer"][0])]
        else:
            assert isinstance(item["answer"], int) or isinstance(item["answer"], float)
            reference_answers = [str(item["answer"])]

        if item["category"] is None:
            category = None
        else:
            category = self.CATEGORY_MAP[item["category"]]
        metadata = {
            "UMWP_id": item["id"],
            "UMWP_category": category,
            "UMWP_relevant_ids": item["relevant_ids"],
            "UMWP_source": item["source"],
        }

        return Prompt(
            question=question,
            reference_answers=reference_answers,
            should_abstain=should_abstain,
            metadata=metadata,
        )



class WorldSenseDataset(AbstentionDataset):
    """
    Filters train 10k dataset for answerable and unanswerable set
    see preprocess function for how raw data is transformed
    """

    def __init__(
        self,
        data_dir='data/world_sense',
        raw_data_url="https://github.com/facebookresearch/worldsense/raw/refs/heads/main/data/worldsense/training_set/trials_10k.jsonl.bz2",
        max_num_samples=None,
    ):
        super().__init__()
        self.data_dir = data_dir
        self.raw_data_url = raw_data_url
        self.max_num_samples = max_num_samples

        self.dataset = self.load_dataset()

    def load_dataset(self) -> pd.DataFrame:
        dataset_path = Path(self.data_dir) / 'trials_10k.jsonl'

        if not dataset_path.exists():
            self._download_data()

        df = pd.read_json(dataset_path, lines=True)
        df = self._preprocess_raw_data(df)

        return df

    def _preprocess_raw_data(self, df: pd.DataFrame):
        # download raw_data_url and load into pandas
        df["question"] = df["dialog_history"].apply(
            lambda x: dict(x)["messages"][0]["content"]
        )
        # filter for knownable and unknowable questions
        df = df[df["target_message"].isin(["1", "2", "3"])]
        df["is_answerable"] = df["target_message"].apply(
            lambda x: False if x == "3" else True
        )
        return df

    def _download_data(self):
        if not os.path.exists(self.data_dir):
            os.makedirs(self.data_dir, exist_ok=True)

        destination = os.path.join(self.data_dir, "trials_10k.jsonl.bz2")
        wget.download(self.raw_data_url, destination)

        # Decompress the .bz2 file to .jsonl
        decompressed_path = os.path.join(self.data_dir, "trials_10k.jsonl")
        with bz2.open(destination, 'rb') as f:
            with open(decompressed_path, 'wb') as out_file:
                out_file.write(f.read())

        # Clean up by deleting the .bz2 file
        if os.path.exists(destination):
            os.remove(destination)

        logger.info(f"WorldSense dataset downloaded and extracted to '{self.data_dir}'")

    def __len__(self) -> int:
        return self.max_num_samples or len(self.dataset)

    def __getitem__(self, idx) -> Prompt:
        if idx >= self.__len__():
            raise IndexError

        sample = self.dataset.iloc[idx]
        question = sample["question"]
        reference_answers = [str(sample["target_message"])]
        should_abstain = ~sample["is_answerable"]
        metadata = {}

        return Prompt(
            question=question,
            reference_answers=reference_answers,
            should_abstain=should_abstain,
            metadata=metadata,
        )