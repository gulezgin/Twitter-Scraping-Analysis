import pandas as pd
import pytest

import sentiment


def fake_classifier(texts):
    out = []
    for t in texts:
        if 'harika' in t:
            out.append({'label': 'positive', 'score': 0.98})
        elif 'berbat' in t:
            out.append({'label': 'negative', 'score': 0.95})
        else:
            out.append({'label': 'positive', 'score': 0.55})
    return out


def test_clean_text_masks_links_and_mentions():
    assert sentiment.clean_text('@icardi gol  https://t.co/abc  süper') == '@user gol http süper'


def test_classify_applies_neutral_threshold():
    df = sentiment.classify(['harika maç', 'berbat hakem', 'maç bitti'], fake_classifier, neutral_threshold=0.75)
    assert df['sentiment'].tolist() == ['positive', 'negative', 'neutral']


def test_classify_without_threshold_keeps_model_labels():
    df = sentiment.classify(['maç bitti'], fake_classifier, neutral_threshold=0)
    assert df['sentiment'].tolist() == ['positive']


def test_classify_empty_input():
    assert sentiment.classify([], fake_classifier).empty


def test_normalize_label_rejects_unknown():
    assert sentiment.normalize_label('NEGATIVE') == 'negative'
    with pytest.raises(ValueError):
        sentiment.normalize_label('LABEL_0')


def test_summarize_percentages_use_actual_count():
    summary = sentiment.summarize(pd.Series(['positive', 'positive', 'negative', 'neutral']))
    assert summary.loc['positive', 'count'] == 2
    assert summary.loc['positive', 'percent'] == 50.0
    assert summary['percent'].sum() == 100.0


def test_main_writes_output_and_chart(tmp_path, monkeypatch):
    src = tmp_path / 'tweets.csv'
    pd.DataFrame({'tweet_id': ['1', '2'], 'text': ['harika gol', 'berbat oyun']}).to_csv(
        src, index=False, encoding='utf-8-sig')
    monkeypatch.setattr(sentiment, 'load_classifier', lambda model: fake_classifier)

    sentiment.main([str(src), '--chart', str(tmp_path / 'chart.png')])

    result = pd.read_csv(tmp_path / 'tweets_sentiment.csv', encoding='utf-8-sig')
    assert result['sentiment'].tolist() == ['positive', 'negative']
    assert (tmp_path / 'chart.png').stat().st_size > 0
