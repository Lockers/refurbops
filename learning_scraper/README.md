# Learning Scraper

This standalone Python package demonstrates a scraper that can:

1. fetch a page
2. extract readable content from HTML
3. make simple quality judgements
4. retry when the content looks blocked, incomplete, or too thin

## Why this is useful

It is intentionally small and inspectable, so it is a good learning base before
adding advanced features such as browser automation, queueing, ML-based page
classification, rotating proxies, or persistent crawl state.

## Example usage

```bash
python -m learning_scraper.cli https://example.com --required-keyword example --min-text-length 50
```

## Core modules

- `models.py`: shared dataclasses
- `http_client.py`: page fetching
- `html_tools.py`: HTML cleanup and extraction
- `judgement.py`: accept / retry / reject rules
- `runner.py`: workflow orchestration
- `cli.py`: command-line entrypoint
