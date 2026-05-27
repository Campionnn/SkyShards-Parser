# SkyShards Parser
### Python script to algorithmically generate all possible recipes based on info from the wiki
## Steps
1. Run `build-properties.py`
2. This will generate `dist/fusion-properties.json` and any fusion info can be adjusted
3. Run `find-all-recipes.py` which will generate `dist/fusion-recipes.json` of all possible fusions based on the rules of fusion and wiki data
4. Run `format-fusions.py` to format the data in a way that's easier to be used
5. This will create `dist/fusion-data.json` which is used by [SkyShards](https://skyshards.com)
