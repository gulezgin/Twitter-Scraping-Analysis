"""scraper.py ile toplanan tweetlerin duygu analizini yapar.

Varsayılan model Türkçe tweetler için eğitilmiş bir BERT modelidir.
Örnek:
    python sentiment.py tweets.csv -o tweets_sentiment.csv --chart sentiment.png
"""
from __future__ import annotations

import argparse
import re
from pathlib import Path
from typing import Callable, Iterable

import pandas as pd

DEFAULT_MODEL = 'savasy/bert-base-turkish-sentiment-cased'
LABELS = ['positive', 'neutral', 'negative']
COLORS = {'positive': '#4caf50', 'neutral': '#9e9e9e', 'negative': '#e53935'}

URL_RE = re.compile(r'https?://\S+')
MENTION_RE = re.compile(r'@\w+')

# Tahmin fonksiyonu: metin listesi alır, [{'label': ..., 'score': ...}] döndürür.
Classifier = Callable[[list[str]], list[dict]]


def clean_text(text: str) -> str:
    """Link ve kullanıcı etiketlerini sadeleştirir; model için gürültüyü azaltır."""
    text = URL_RE.sub('http', str(text))
    text = MENTION_RE.sub('@user', text)
    return ' '.join(text.split())


def normalize_label(label: str) -> str:
    label = label.lower()
    if label.startswith('pos'):
        return 'positive'
    if label.startswith('neg'):
        return 'negative'
    if label.startswith('neu'):
        return 'neutral'
    raise ValueError(f'Tanınmayan etiket: {label!r}. Modelin id2label ayarını kontrol edin.')


def load_classifier(model: str, batch_size: int = 16) -> Classifier:
    from transformers import pipeline  # ağır import, sadece gerektiğinde

    pipe = pipeline('sentiment-analysis', model=model, tokenizer=model)
    return lambda texts: pipe(texts, batch_size=batch_size, truncation=True, max_length=128)


def classify(texts: Iterable[str], classifier: Classifier,
             neutral_threshold: float = 0.0) -> pd.DataFrame:
    """Her metin için duygu etiketi ve güven skoru döndürür.

    İkili (pozitif/negatif) modellerde güveni `neutral_threshold` altında kalan
    tahminler 'neutral' olarak işaretlenir.
    """
    texts = [clean_text(t) for t in texts]
    results = classifier(texts) if texts else []
    labels, scores = [], []
    for r in results:
        label = normalize_label(r['label'])
        if r['score'] < neutral_threshold:
            label = 'neutral'
        labels.append(label)
        scores.append(round(float(r['score']), 4))
    return pd.DataFrame({'sentiment': labels, 'sentiment_score': scores})


def summarize(sentiments: pd.Series) -> pd.DataFrame:
    counts = sentiments.value_counts().reindex(LABELS, fill_value=0)
    total = int(counts.sum())
    pct = (counts / total * 100).round(1) if total else counts.astype(float)
    return pd.DataFrame({'count': counts, 'percent': pct})


def plot_summary(summary: pd.DataFrame, title: str, path: Path | None, show: bool) -> None:
    import matplotlib
    if not show:
        matplotlib.use('Agg')
    import matplotlib.pyplot as plt

    data = summary[summary['count'] > 0]
    fig, ax = plt.subplots(figsize=(6, 6))
    ax.pie(
        data['count'],
        labels=[f'{label} ({p:.1f}%)' for label, p in zip(data.index, data['percent'])],
        colors=[COLORS[label] for label in data.index],
        startangle=90,
        wedgeprops={'edgecolor': 'white'},
    )
    ax.set_title(title)
    ax.axis('equal')
    if path:
        fig.savefig(path, dpi=150, bbox_inches='tight')
        print(f'Grafik kaydedildi: {path}')
    if show:
        plt.show()
    plt.close(fig)


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    p = argparse.ArgumentParser(description='Tweet CSV dosyası üzerinde duygu analizi yapar.')
    p.add_argument('input', type=Path, help='scraper.py çıktısı CSV dosyası')
    p.add_argument('-o', '--output', type=Path, help='Sonuç CSV (varsayılan: <girdi>_sentiment.csv)')
    p.add_argument('--model', default=DEFAULT_MODEL, help=f'HuggingFace modeli (varsayılan: {DEFAULT_MODEL})')
    p.add_argument('--text-column', default='text')
    p.add_argument('--neutral-threshold', type=float, default=0.75,
                   help='Bu güvenin altındaki tahminler nötr sayılır (0 = kapalı)')
    p.add_argument('--chart', type=Path, help='Pasta grafiğini bu dosyaya kaydet (ör. sentiment.png)')
    p.add_argument('--show', action='store_true', help='Grafiği pencerede göster')
    p.add_argument('--title', help='Grafik başlığı')
    return p.parse_args(argv)


def main(argv: list[str] | None = None) -> None:
    args = parse_args(argv)
    df = pd.read_csv(args.input, encoding='utf-8-sig', dtype={'tweet_id': str})
    if args.text_column not in df.columns:
        raise SystemExit(f'"{args.text_column}" kolonu bulunamadı. Mevcut kolonlar: {list(df.columns)}')
    df = df.dropna(subset=[args.text_column]).reset_index(drop=True)

    print(f'{len(df)} tweet analiz ediliyor ({args.model})...')
    classifier = load_classifier(args.model)
    result = classify(df[args.text_column].tolist(), classifier, args.neutral_threshold)
    df = pd.concat([df, result], axis=1)

    output = args.output or args.input.with_name(f'{args.input.stem}_sentiment.csv')
    df.to_csv(output, index=False, encoding='utf-8-sig')
    print(f'Sonuçlar kaydedildi: {output}')

    summary = summarize(df['sentiment'])
    print(summary.to_string())

    if args.chart or args.show:
        plot_summary(summary, args.title or f'Duygu Analizi: {args.input.stem}', args.chart, args.show)


if __name__ == '__main__':
    main()
