from src.summarizer import _limit_to_two_sentences


def test_limit_to_two_sentences() -> None:
    text = "First sentence. Second sentence! Third sentence?"

    assert _limit_to_two_sentences(text) == "First sentence. Second sentence!"
