"""Fixed pre-sign smoke questions (lab-notebook tooling, not an instrument).

Deliberately NOT drawn from PopQA: the pre-sign infrastructure checks must not
expose any labeling or decision-model outcome on the cell's population. They
are generic general-knowledge and arithmetic prompts of varied length, used
only to compare prompt bytes, token IDs and completion token IDs across
runtimes and batch orders. Correctness is never scored.
"""

QUESTIONS = [
    "Who wrote Paradise Lost?",
    "What is the boiling point of water at sea level in degrees Celsius?",
    "How many legs does a spider have?",
    "What is the chemical symbol for sodium?",
    "Which planet is known as the Red Planet?",
    "What is 17 multiplied by 3?",
    "In which ocean is the island of Madagascar?",
    "What is the largest organ of the human body?",
    "Who painted the ceiling of the Sistine Chapel?",
    "What gas do plants absorb from the atmosphere for photosynthesis?",
    "What is the square root of 144?",
    "Which language has the most native speakers in the world?",
    "What is the freezing point of water in degrees Fahrenheit?",
    "What instrument has 88 keys in its standard modern form?",
    "Which element has atomic number 1?",
    "What is the name of the longest bone in the human body, located in the thigh?",
    "How many continents are conventionally counted on Earth?",
    "What is the capital city of the country whose flag shows a red maple leaf on a white square between two red bands?",
    "Which famous scientist proposed the three laws of motion that underlie classical mechanics?",
    "If a train travels at a constant 60 kilometres per hour for two and a half hours, how far does it go?",
]


def synthetic(n: int, seed: int = 0) -> list[str]:
    """Deterministic templated arithmetic / unit-conversion questions for
    throughput timing only. No entities, no PopQA relation, never scored."""
    import random

    rng = random.Random(seed)
    templates = [
        lambda a, b: f"What is {a} plus {b}?",
        lambda a, b: f"What is {a} multiplied by {b}?",
        lambda a, b: f"How many minutes are there in {a} hours and {b} minutes?",
        lambda a, b: f"If you have {a} apples and give away {min(a, b)}, how many are left?",
        lambda a, b: f"How many centimetres are there in {a} metres and {b} centimetres?",
    ]
    return [templates[i % len(templates)](rng.randint(2, 999), rng.randint(2, 99)) for i in range(n)]
