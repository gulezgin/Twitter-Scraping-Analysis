import asyncio
import csv
from datetime import datetime, timezone
from types import SimpleNamespace

import scraper


def make_tweet(tweet_id, text='merhaba', screen_name='icardi'):
    return SimpleNamespace(
        id=tweet_id,
        user=SimpleNamespace(screen_name=screen_name, name='Mauro Icardi'),
        full_text=text,
        text=text[:10],
        created_at_datetime=datetime(2023, 5, 1, 12, 0, tzinfo=timezone.utc),
        lang='tr',
        retweet_count=3,
        favorite_count=10,
        reply_count=1,
    )


class FakeResult(list):
    def __init__(self, pages, index=0):
        super().__init__(pages[index] if index < len(pages) else [])
        self._pages, self._index = pages, index

    async def next(self):
        return FakeResult(self._pages, self._index + 1)


class FakeClient:
    def __init__(self, pages):
        self.pages = pages

    async def search_tweet(self, query, product):
        return FakeResult(self.pages)


def read_rows(path):
    with path.open(encoding='utf-8-sig', newline='') as f:
        return list(csv.DictReader(f))


def run_scrape(client, path, limit):
    return asyncio.run(scraper.scrape(client, 'q', limit, 'Latest', path, 0, 0))


def test_tweet_to_row_prefers_full_text_and_builds_url():
    row = scraper.tweet_to_row(make_tweet('42', text='uzun bir türkçe tweet metni'))
    assert row['text'] == 'uzun bir türkçe tweet metni'
    assert row['url'] == 'https://x.com/icardi/status/42'
    assert row['like_count'] == 10
    assert row['created_at'] == '2023-05-01T12:00:00+00:00'


def test_scrape_paginates_dedupes_and_respects_limit(tmp_path):
    out = tmp_path / 'tweets.csv'
    pages = [[make_tweet('1'), make_tweet('2')], [make_tweet('2'), make_tweet('3'), make_tweet('4')]]
    assert run_scrape(FakeClient(pages), out, limit=3) == 3
    assert [r['tweet_id'] for r in read_rows(out)] == ['1', '2', '3']


def test_scrape_stops_when_no_more_tweets(tmp_path):
    out = tmp_path / 'tweets.csv'
    assert run_scrape(FakeClient([[make_tweet('1')]]), out, limit=50) == 1


def test_scrape_appends_without_duplicates(tmp_path):
    out = tmp_path / 'tweets.csv'
    run_scrape(FakeClient([[make_tweet('1'), make_tweet('2')]]), out, limit=10)
    added = run_scrape(FakeClient([[make_tweet('2'), make_tweet('3')]]), out, limit=10)
    assert added == 1
    assert [r['tweet_id'] for r in read_rows(out)] == ['1', '2', '3']


def test_rate_limit_wait_uses_reset_header():
    err = SimpleNamespace(rate_limit_reset=1_000)
    assert scraper.rate_limit_wait_seconds(err, now=900) == 105
    assert scraper.rate_limit_wait_seconds(SimpleNamespace(rate_limit_reset=None)) == scraper.DEFAULT_RATE_LIMIT_WAIT
