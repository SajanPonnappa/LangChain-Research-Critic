# LangChain-Research-Critic

A multi-agent research system built with LangChain: agents search the web, read sources, write a report, and a critic agent reviews it.

> 🚧 Work in progress — currently a project skeleton.

## Setup (uv)

```bash
git clone https://github.com/SajanPonnappa/LangChain-Research-Critic.git
cd LangChain-Research-Critic
uv sync                      # creates .venv and installs dependencies from uv.lock
cp .env.example .env         # then fill in your API keys
```

## Run

```bash
uv run main.py               # CLI
uv run streamlit run app.py  # Streamlit UI
```

## Project Structure

```
.
├── app.py              # Streamlit UI
├── main.py             # CLI entry point
├── pyproject.toml      # Project config + dependencies (managed by uv)
├── uv.lock             # Locked dependency versions
├── .python-version     # Python version used by uv
├── .env.example        # Template for API keys
└── src/
    ├── agents/         # Search, reader, writer, critic agents
    ├── tools/          # web_search, scrape_url tools
    └── pipelines/      # Orchestrates the agents
```
