# Aviasales

Searching flights on aviasales.ru.

## Search by URL

```
https://www.aviasales.ru/search/{FROM}{DDMM}{TO}{DDMM}{PASSENGERS}
```

| Field | Format | Example |
|---|---|---|
| FROM / TO | IATA code (3 letters) | `MOW`, `DXB` |
| dates | DDMM (day+month, no year) | `1602` = Feb 16 |
| PASSENGERS | `Y` + number (economy) | `Y2` = 2 economy |

Examples: `MOW1602DXB2302Y2` (Moscow→Dubai, 16–23 Feb, 2 pax) · `MOW0103HKT1503Y1`.

## Reading the price

The price loads **asynchronously** — it isn't there the instant the page opens.

- It shows in the **page title** for many routes after a few seconds
  (`browser status` → title like `54 124 ₽ | MOW ⇄ DXB, ...`), but not for every route.
- The **snapshot is reliable** even when the title is still empty.

```
browser goto https://www.aviasales.ru/search/MOW1602DXB2302Y2
browser wait 4
browser status      # price is often already in the title
# not there yet? give it a few more seconds, or read: browser snapshot
```

## Compare a few routes

Visit each in turn at a human pace (the async wait doubles as polite spacing, which
also keeps captchas away):

```
for each route:
  browser goto https://www.aviasales.ru/search/<formula>
  browser wait 4
  browser snapshot    # price on the result card (re-snapshot if it isn't ready yet)
```

## Captcha

- **When it shows up:** after many requests in a row, on a fresh session (no
  cookies), or after fast navigation.
- **What it is:** usually Google reCAPTCHA (image tiles).
- **Keeping it away:** the dedicated profile keeps cookies between runs (solve once,
  it stays away while the cookies live); space requests a few seconds apart.
- If it appears, use the captcha ladder — `browser captcha status`, then the vision
  tools or `browser captcha ask-human`.

## Common IATA codes

`DXB` Dubai · `AUH` Abu-Dhabi · `SHJ` Sharjah · `DOH` Doha · `HRG` Hurghada ·
`SSH` Sharm-el-Sheikh · `BKK` Bangkok · `HKT` Phuket · `DPS` Bali · `MLE` Maldives ·
`CXR` Nha-Trang · `SGN` Ho-Chi-Minh · `ZNZ` Zanzibar · `CUN` Cancun.
