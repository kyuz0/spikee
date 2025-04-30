# Dataset generation

## English dataset (bare)
The English dataset can be generated using this command (ensure you include `--include-system-message`):

```bash
spikee generate --seed-folder datasets/seeds-sysmsg-extraction-2025-04 --include-system-message --languages en
```

## English dataset (spotlighting)
You can add XML and JSON spotlighting like this:

```bash
spikee generate --seed-folder datasets/seeds-sysmsg-extraction-2025-04 --include-system-message --languages en --spotlighting-data-markers $'\n<data>\nDOCUMENT\n</data>\n',$'\n{"document":"DOCUMENT"}\n'
```

## English + Low Resource Languages Dataset (bare)

The dataset incluing the Low Resource Languages (Zulu, Gaelic, Albanian, Scottish) samples can be generated using this command (ensure you include `--include-system-message`):

```bash
$ spikee generate --seed-folder datasets/seeds-sysmsg-extraction-2025-04 --include-system-message --match-languages
```

Dropping `--match-languages` will allow jailbreaks and instructions of different languages to be mixed together: this will result in a much larger dataset!