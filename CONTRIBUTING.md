# Contributing

Thanks for helping improve ZettelApp!

- **Bugs and ideas**: open an [issue](https://github.com/DutraIRS/ZettelApp/issues). For bugs, include your
  ZettelApp version (*Help ▸ About*), what you did, what you expected, and the relevant part of the log
  (`%LOCALAPPDATA%\ZettelApp\Logs`).
- **Security problems**: please report them privately (see [SECURITY.md](SECURITY.md)).
- **Code**: see [docs/development.md](docs/development.md) to set up, run and test. Then:
  1. Fork the repository and create a branch.
  2. Keep changes focused, and match the existing style: type hints, small functions, concise
     docstrings. User interface text uses British spelling.
  3. Keep `zettelapp/core/` free of Qt imports, so it stays testable without a GUI.
  4. Add or update tests, and run `pytest`.
  5. Treat note contents and imported files as untrusted. Validate input at the edges and use bound SQL
     parameters (see the [security model](docs/privacy-and-security.md)).
  6. Open a pull request describing the change and how you tested it.
- **Documentation and translations** are very welcome. The docs live in `docs/`, and app translations are
  planned (see the [roadmap](ROADMAP.md)).

By contributing, you agree that your contributions are released into the public domain under
[The Unlicense](LICENSE), like the rest of the project.
