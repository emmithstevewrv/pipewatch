# pipewatch

A lightweight CLI for monitoring and alerting on ETL pipeline health metrics.

---

## Installation

```bash
pip install pipewatch
```

Or install from source:

```bash
git clone https://github.com/yourname/pipewatch.git && cd pipewatch && pip install -e .
```

---

## Usage

Monitor a pipeline by pointing pipewatch at your metrics endpoint or log source:

```bash
pipewatch monitor --source my_pipeline --interval 60
```

Set up an alert threshold:

```bash
pipewatch alert --metric error_rate --threshold 0.05 --notify slack
```

Check the current health status of all registered pipelines:

```bash
pipewatch status
```

Run `pipewatch --help` to see all available commands and options.

---

## Configuration

Pipewatch reads from a `pipewatch.yaml` file in your working directory. Example:

```yaml
pipelines:
  - name: my_pipeline
    source: postgresql://localhost/mydb
    interval: 60
alerts:
  error_rate:
    threshold: 0.05
    notify: slack
```

You can specify a custom config file path using the `--config` flag:

```bash
pipewatch status --config /path/to/custom_config.yaml
```

---

## License

This project is licensed under the [MIT License](LICENSE).
