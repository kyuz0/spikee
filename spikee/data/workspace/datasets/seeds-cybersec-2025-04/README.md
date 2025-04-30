# Dataset generation

## English dataset (bare)
The English dataset can be generated using this command:

```bash
spikee generate --seed-folder datasets/seeds-cybersec-2025-04 --languages en
```

## English dataset (spotlighting + system message)
You can add XML/JSON spotlighting and include a system message like this:

```bash
spikee generate --seed-folder datasets/seeds-cybersec-2025-04 --languages en --include-system-message --spotlighting-data-markers $'\n<data>\nDOCUMENT\n</data>\n',$'\n{"document":"DOCUMENT"}\n'
```

## English + Low Resource Languages Dataset (bare)

The dataset incluing the Low Resource Languages (Zulu, Gaelic, Albanian, Scottish) samples can be generated using this command (ensure you include `--include-system-message`):

```bash
spikee generate --seed-folder datasets/seeds-cybersec-2025-04 --match-languages
```

Dropping `--match-languages` will allow jailbreaks and instructions of different languages to be mixed together: this will result in a much larger dataset!