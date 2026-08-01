# Contributing

Keep the public application and SDK paths small and stable:

- application code belongs in `app/`;
- public declarations belong in `include/mobigo_sdk/`;
- SDK implementations belong in `src/`;
- maintained examples belong in `examples/`;
- developer utilities belong in the matching `tools/` category;
- historical evidence and one-off probes belong in `research/`.

Do not add retail game code, art, or audio to the clean-room SDK. Do not commit
generated files from `build/`.

Before submitting a change, run:

```sh
make test
make release-check
```

Documentation changes must also pass `mkdocs build --strict`.
