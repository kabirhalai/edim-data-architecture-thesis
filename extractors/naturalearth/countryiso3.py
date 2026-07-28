import pandas as pd

from extractors.shared import save_raw

URL = "https://download.geonames.org/export/dump/countryInfo.txt"

cols = [
    "ISO", "ISO3", "ISO-Numeric", "fips", "Country", "Capital",
    "Area", "Population", "Continent", "tld", "CurrencyCode",
    "CurrencyName", "Phone", "PostalCodeFormat",
    "PostalCodeRegex", "Languages", "geonameid",
    "neighbours", "EquivalentFipsCode"
]

if __name__ == "__main__":
    df = pd.read_csv(
        URL,
        sep="\t",
        comment="#",
        header=None,
        names=cols,
    )

    df[['ISO3', 'Country']].to_csv("edim/seeds/countryiso3.csv", index=False)
