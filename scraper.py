"""X (Twitter) arama sonuçlarını twikit ile çekip CSV dosyasına yazar.

Örnek:
    python scraper.py "(from:icardi) lang:tr since:2023-01-01 until:2023-12-31" -n 100 -o tweets.csv
"""
from __future__ import annotations

import argparse
import asyncio
import csv
import os
import random
import sys
import time
from datetime import datetime
from pathlib import Path

from dotenv import load_dotenv
from twikit import Client, TooManyRequests

FIELDS = [
    'tweet_id', 'username', 'display_name', 'text', 'created_at',
    'lang', 'retweet_count', 'like_count', 'reply_count', 'url',
]
DEFAULT_RATE_LIMIT_WAIT = 15 * 60


def log(message: str) -> None:
    print(f'{datetime.now():%Y-%m-%d %H:%M:%S} - {message}', flush=True)


def tweet_to_row(tweet) -> dict:
    """twikit Tweet nesnesini CSV satırına dönüştürür."""
    user = getattr(tweet, 'user', None)
    screen_name = getattr(user, 'screen_name', '') or ''
    created = getattr(tweet, 'created_at_datetime', None)
    return {
        'tweet_id': tweet.id,
        'username': screen_name,
        'display_name': getattr(user, 'name', '') or '',
        # Uzun tweetlerde `text` kısaltılmış olabilir, `full_text` tercih edilir.
        'text': getattr(tweet, 'full_text', None) or getattr(tweet, 'text', '') or '',
        'created_at': created.isoformat() if created else getattr(tweet, 'created_at', ''),
        'lang': getattr(tweet, 'lang', '') or '',
        'retweet_count': getattr(tweet, 'retweet_count', 0) or 0,
        'like_count': getattr(tweet, 'favorite_count', 0) or 0,
        'reply_count': getattr(tweet, 'reply_count', 0) or 0,
        'url': f'https://x.com/{screen_name}/status/{tweet.id}' if screen_name else '',
    }


def rate_limit_wait_seconds(error: TooManyRequests, now: float | None = None) -> float:
    """Rate limit sıfırlanana kadar beklenecek süre (saniye)."""
    now = time.time() if now is None else now
    reset = getattr(error, 'rate_limit_reset', None)
    if reset:
        return max(reset - now, 0) + 5
    return DEFAULT_RATE_LIMIT_WAIT


async def authenticate(cookies_file: Path) -> Client:
    client = Client(language='en-US')
    if cookies_file.exists():
        log(f'{cookies_file} yükleniyor...')
        client.load_cookies(str(cookies_file))
        return client

    load_dotenv()
    username = os.getenv('X_USERNAME', '').strip()
    email = os.getenv('X_EMAIL', '').strip() or None
    password = os.getenv('X_PASSWORD', '').strip()
    if not username or not password:
        sys.exit(
            f'{cookies_file} bulunamadı ve X_USERNAME / X_PASSWORD tanımlı değil. '
            '.env.example dosyasını .env olarak kopyalayıp doldurun.'
        )

    log('Oturum açılıyor...')
    await client.login(
        auth_info_1=username,
        auth_info_2=email,
        password=password,
        totp_secret=os.getenv('X_TOTP_SECRET') or None,
    )
    client.save_cookies(str(cookies_file))
    log(f'Oturum {cookies_file} dosyasına kaydedildi.')
    return client


async def scrape(client: Client, query: str, limit: int, product: str,
                 output: Path, min_delay: float, max_delay: float) -> int:
    seen: set[str] = set()
    if output.exists():
        with output.open(encoding='utf-8-sig', newline='') as f:
            seen = {row['tweet_id'] for row in csv.DictReader(f)}
        log(f'{output} içinde {len(seen)} tweet var, yenileri eklenecek.')

    new_file = not output.exists()
    written = 0
    tweets = None

    # utf-8-sig: Excel'de Türkçe karakterlerin doğru görünmesi için BOM ekler.
    with output.open('a', encoding='utf-8-sig' if new_file else 'utf-8', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=FIELDS)
        if new_file:
            writer.writeheader()

        while written < limit:
            try:
                if tweets is None:
                    log('Tweetler çekiliyor...')
                    tweets = await client.search_tweet(query, product=product)
                else:
                    delay = random.uniform(min_delay, max_delay)
                    log(f'{delay:.1f} sn sonra sonraki sayfa çekilecek...')
                    await asyncio.sleep(delay)
                    tweets = await tweets.next()
            except TooManyRequests as e:
                wait = rate_limit_wait_seconds(e)
                log(f'Rate limit aşıldı, {wait / 60:.1f} dk bekleniyor...')
                await asyncio.sleep(wait)
                continue

            if not tweets:
                log('Başka tweet bulunamadı.')
                break

            for tweet in tweets:
                if tweet.id in seen:
                    continue
                seen.add(tweet.id)
                writer.writerow(tweet_to_row(tweet))
                written += 1
                if written >= limit:
                    break
            f.flush()
            log(f'Toplam {written} yeni tweet yazıldı.')

    return written


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    p = argparse.ArgumentParser(description='X arama sonuçlarını CSV dosyasına kaydeder.')
    p.add_argument('query', help='X arama sorgusu, ör. "(from:icardi) lang:tr"')
    p.add_argument('-n', '--limit', type=int, default=100, help='Çekilecek tweet sayısı (varsayılan: 100)')
    p.add_argument('-o', '--output', type=Path, default=Path('tweets.csv'), help='Çıktı CSV dosyası')
    p.add_argument('--product', choices=['Top', 'Latest', 'Media'], default='Latest')
    p.add_argument('--cookies', type=Path, default=Path('cookies.json'), help='Oturum çerez dosyası')
    p.add_argument('--min-delay', type=float, default=5, help='Sayfalar arası en az bekleme (sn)')
    p.add_argument('--max-delay', type=float, default=10, help='Sayfalar arası en çok bekleme (sn)')
    return p.parse_args(argv)


async def main(argv: list[str] | None = None) -> None:
    args = parse_args(argv)
    client = await authenticate(args.cookies)
    count = await scrape(client, args.query, args.limit, args.product,
                         args.output, args.min_delay, args.max_delay)
    log(f'Bitti! {count} tweet {args.output} dosyasına kaydedildi.')


if __name__ == '__main__':
    asyncio.run(main())
