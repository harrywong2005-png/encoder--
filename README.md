# encoder--name: Encoder Daily Brief

on:
  schedule:
    # UTC 00:00 = 北京时间 08:00
    - cron: '0 0 * * *'
  workflow_dispatch:

jobs:
  send:
    runs-on: ubuntu-latest

    steps:
      - uses: actions/checkout@v4

      - uses: actions/setup-python@v5
        with:
          python-version: '3.11'

      - name: Install deps
        run: pip install feedparser

      - name: Send brief
        run: python encoder_daily.py
        env:
          SMTP_HOST: smtp.126.com
          SMTP_PORT: '465'
          SMTP_USER: ${{ secrets.SMTP_USER }}
          SMTP_PASS: ${{ secrets.SMTP_PASS }}
          MAIL_TO: harrywong2005@126.com
