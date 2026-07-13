# Contributing

This is a portfolio project, not an active open-source library.  
Suggestions and forks are welcome.

## Local Setup

```bash
git clone https://github.com/ShivShah018/food-delivery-operations-analytics.git
cd food-delivery-operations-analytics
pip install -r requirements.txt
python run_pipeline.py
pytest tests/ -v
```

## Before Committing

1. Run `pytest tests/ -v` — all tests must pass.
2. Run `python run_pipeline.py` — pipeline must complete without errors.
3. Check `logs/pipeline.log` for any WARNING or ERROR entries.

## Code Style

- Follow PEP 8.
- Include docstrings for every public function.
- Use the centralised `config.py` for paths and constants — never hardcode them.
