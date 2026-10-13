# Twitter Scraping & Analysis

X (Twitter) üzerinden tweet toplayıp Türkçe duygu analizi yapan iki adımlı bir araç:

1. **`scraper.py`**: [twikit](https://github.com/d60/twikit) ile X araması yapar ve sonuçları CSV'ye yazar. API anahtarı gerekmez, normal bir X hesabıyla çalışır.
2. **`sentiment.py`**: CSV'deki tweetleri Türkçe BERT modeliyle ([savasy/bert-base-turkish-sentiment-cased](https://huggingface.co/savasy/bert-base-turkish-sentiment-cased)) sınıflandırır, sonucu yeni bir CSV'ye ve isteğe bağlı olarak bir pasta grafiğine kaydeder.

## Kurulum

Python 3.10+ gerekir.

```bash
python -m venv .venv
.venv\Scripts\activate        # Linux/macOS: source .venv/bin/activate
pip install -r requirements.txt
```

> `torch` büyük bir pakettir. Sadece CPU sürümünü kurmak için önce
> `pip install torch --index-url https://download.pytorch.org/whl/cpu` çalıştırabilirsiniz.

## Oturum bilgileri

```bash
copy .env.example .env        # Linux/macOS: cp .env.example .env
```

`.env` dosyasına X kullanıcı adınızı, e-postanızı ve şifrenizi yazın. İlk çalıştırmada giriş yapılır ve oturum
`cookies.json` dosyasına kaydedilir. Sonraki çalıştırmalarda şifre kullanılmaz, bu dosya kullanılır.

`.env` ve `cookies.json` dosyaları `.gitignore` içindedir. **Asla commit etmeyin**, çünkü `cookies.json`
hesabınıza tam erişim sağlar.

> Önemli: twikit X'in resmi olmayan iç API'sini kullanır. Bu X'in kullanım koşullarına aykırı olabilir ve
> hesabınız kısıtlanabilir. Ana hesabınız yerine ayrı bir hesap kullanmanız önerilir.

## Kullanım

### 1. Tweet toplama

```bash
python scraper.py "(from:icardi) lang:tr since:2023-01-01 until:2023-12-31" -n 200 -o icardi.csv
```

| Parametre | Açıklama | Varsayılan |
|---|---|---|
| `query` | X arama sorgusu ([gelişmiş arama operatörleri](https://github.com/igorbrigadir/twitter-advanced-search) desteklenir) | — |
| `-n, --limit` | Çekilecek tweet sayısı | 100 |
| `-o, --output` | Çıktı CSV dosyası | `tweets.csv` |
| `--product` | `Latest`, `Top` veya `Media` | `Latest` |
| `--min-delay / --max-delay` | Sayfalar arası rastgele bekleme (sn) | 5 / 10 |

Var olan bir CSV'ye tekrar yazılırsa yeni tweetler dosyanın sonuna eklenir; aynı tweet iki kez yazılmaz.
Rate limit aşılırsa script X'in bildirdiği sıfırlanma zamanına kadar bekler ve sonra devam eder.

CSV kolonları: `tweet_id, username, display_name, text, created_at, lang, retweet_count, like_count, reply_count, url`

### 2. Duygu analizi

```bash
python sentiment.py icardi.csv --chart icardi.png
```

Sonuçlar `icardi_sentiment.csv` dosyasına yazılır. Bu dosya orijinal kolonlara ek olarak `sentiment`
(`positive` / `neutral` / `negative`) ve `sentiment_score` kolonlarını içerir.

Varsayılan model sadece pozitif/negatif ayrımı yapar. Model güveni `--neutral-threshold` değerinin
(varsayılan 0.75) altında kalan tweetler nötr sayılır. İngilizce gibi başka bir dil için `--model` ile farklı bir
HuggingFace modeli verebilirsiniz, ör. `--model cardiffnlp/twitter-roberta-base-sentiment-latest`.

Model ilk çalıştırmada indirilir (~450 MB).

## Testler

```bash
pip install -r requirements-dev.txt
pytest
```

Testler X'e bağlanmaz ve model indirmez. Sahte (mock) istemci ve sınıflandırıcı kullanır.

## Klasör yapısı

```
scraper.py         # tweet toplama
sentiment.py       # duygu analizi
tests/             # birim testleri
legacy/            # eski Nitter notebook'ları (artık çalışmıyor, bkz. legacy/README.md)
```
