# Airbnb

Searching for stays on airbnb.com.

## Search by URL (skip the interactive flow)

```
https://www.airbnb.com/s/{LOCATION}/homes?checkin={YYYY-MM-DD}&checkout={YYYY-MM-DD}&adults={N}&currency={CUR}
```

| Field | Format | Example |
|---|---|---|
| LOCATION | city, or city-Country (hyphenated) | `Dubai` · `Nha-Trang-Vietnam` |
| checkin / checkout | YYYY-MM-DD | `2026-02-16` |
| adults | number | `2` (add `&children=1` if needed) |
| currency | 3 letters | `RUB`, `USD` |

`goto` straight to that URL and the results render — no need to drive the search box.

**Location naming is the catch** — some cities go bare, others need the country:

| Country | Form | Examples |
|---|---|---|
| UAE | city | Dubai, Abu-Dhabi, Sharjah |
| Egypt | city | Sharm-El-Sheikh, Hurghada |
| Vietnam / Thailand / Qatar / Saudi | city-Country | Nha-Trang-Vietnam, Phuket-Thailand, Doha-Qatar, Jeddah-Saudi-Arabia |

## Compare a few destinations

Visit each in turn; prices are on the cards and on the map markers:

```
for each destination:
  browser goto "https://www.airbnb.com/s/<LOCATION>/homes?checkin=2026-02-16&checkout=2026-02-23&adults=2&currency=RUB"
  browser wait 3
  browser screenshot   # prices under cards ("XX,XXX ₽ for 7 nights") and on the map
```

## Gotchas

- **Popup "Now you'll see one price for your trip"** on first visit — prices are
  visible behind it; click its "Got it", or just read past it.
- **Cookie banner** at the bottom — usually harmless, ignore.
- Prices are **all-in** (fees + taxes); "for N nights" is shown under each price.
- The **map on the right** shows price distribution by area.
- **Mainland China doesn't work** ("No stays available in mainland China") — use
  Booking.com / Trip.com there.
