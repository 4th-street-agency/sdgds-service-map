# Same Day Garage Door — Service Area Map

A self-contained, responsive choropleth of every ZIP code SDGDS has serviced across
the Phoenix East Valley + adjacent cities. Darker = more homeowners helped. Tap any ZIP
for its count, the city's star rating + review volume, and a unique verified customer quote.

Privacy: the map only ever shows ZIP-code-level aggregates. No name, address, or
individual point is included in `index.html` or the data files.

## Embed in Framer
1. Deploy (below) to get a live URL, e.g. `https://<user>.github.io/sdgds-service-map/`.
2. In Framer, add an **Embed** component and point it at that URL (iframe).
3. Size the embed; the map fills its container and reframes at 1440 / 810 / 375 breakpoints.

## Deploy to GitHub Pages (one command)
Requires the GitHub CLI (`gh`) authenticated on your machine.
```
bash create_repo.sh            # or: bash create_repo.sh my-repo-name
```
It inits git, creates a public repo, pushes, enables Pages, and prints the embed URL
(live in ~1 minute).

### Or deploy to Vercel
```
npx vercel deploy --prod       # from this folder; URL is printed
```

## Refresh the data
1. Export the latest customer list to `source/Customer_List.csv`
   (columns: `Customer Name, Full Address`).
2. Export the reviews sheet to `source/reviews.csv`
   (columns include `Author Name, Star rating, Short Review`).
3. One-time: download ZIP boundaries to `source/az_zips.json`:
   ```
   curl -sL -o source/az_zips.json \
     https://raw.githubusercontent.com/OpenDataDE/State-zip-code-GeoJSON/master/az_arizona_zip_codes_geo.min.json
   ```
4. Rebuild:
   ```
   python source/rebuild.py
   ```
   This regenerates `source/zip_geo.json`, `source/reviews_by_zip.json`, and `index.html`.
5. Commit & push — Pages redeploys automatically.

## Config (top of `source/rebuild.py`)
- `SERVICE`  — set of cities that render. Add/remove a city name to change coverage.
- `FLOOR`    — minimum jobs per ZIP to display (default 10).

## Notes
- Reviews carry no location field; reviewer city/ZIP is recovered by joining review
  author names to the customer list (~59% match). Counts/ratings are city-level;
  quotes are ZIP-level and never repeat. The durable fix is to stamp city/ZIP onto
  each review at collection time (Senja), which removes the join entirely.

## Set the default zoom per landing page (URL parameters)
The same `index.html` zooms to a chosen area based on the embed URL. No extra files.

- `?city=<slug>`  — zoom to a city (e.g. `?city=queen-creek`)
- `?zip=<zip>`    — zoom to a single ZIP (e.g. `?zip=85142`), most precise
- `?popup=1`      — also auto-open the focused area's busiest ZIP popup
- (no parameter)  — whole service area (use on the homepage)

Combine with `&`, e.g. `?city=gilbert&popup=1`. Hash form also works: `#city=gilbert`.

Per-page embed example (Framer Embed URL):
- Queen Creek page → `https://<user>.github.io/sdgds-service-map/?city=queen-creek`
- Gilbert page     → `https://<user>.github.io/sdgds-service-map/?city=gilbert`
- Homepage         → `https://<user>.github.io/sdgds-service-map/`

City slugs:
| City | slug | City | slug |
|---|---|---|---|
| Gilbert | gilbert | Scottsdale | scottsdale |
| Mesa | mesa | Phoenix | phoenix |
| Chandler | chandler | Ahwatukee | ahwatukee |
| Tempe | tempe | Fountain Hills | fountain-hills |
| Queen Creek | queen-creek | Paradise Valley | paradise-valley |
| San Tan Valley | san-tan-valley | Apache Junction | apache-junction |
| Gold Canyon | gold-canyon | | |

Auto-detect fallback: if no parameter is given, the map tries to infer the city from the
parent landing-page URL (e.g. a page at `/queen-creek/`). This is best-effort (referrer can
be blank), so prefer the explicit `?city=` for reliability.
