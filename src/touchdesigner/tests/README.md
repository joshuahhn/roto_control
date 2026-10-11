# Runtime tests

From `src/touchdesigner`, run the required unchanged command:

```sh
python3 -m unittest discover -q
```

`tests/__init__.py` makes runtime fixtures, external scripts and scoped probes
importable during discovery. Inspector tests retain their existing entry point:

```sh
python3 -m unittest discover -s prototypes/inspector -q
```
