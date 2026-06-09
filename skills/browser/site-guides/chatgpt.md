# ChatGPT

Operating chatgpt.com. The UI shifts often — `snapshot` again after each action and
verify against what you see.

## Quirks (where the snapshot lies)

- **Model selector** — clicking by `ref` often doesn't work; click **by coordinates**
  (top-left area). `screenshot` to see where it is.
- **"+" (add files & more) button** — most reliable via selector + offset:
  `click --selector 'button[aria-label="Add files and more"]' --offset 10,10`.
- The UI is **dynamic** — refs change between states, so `snapshot` again after every
  click before acting on the result.

## Recipes

Flows are stable-ish; exact labels drift — confirm in the snapshot.

**Send a message**
```
browser snapshot                 # input is a contenteditable / paragraph at the bottom
browser type <ref> "your text"
browser snapshot                 # find "Send prompt", then:
browser click <ref>
```

**Enable Deep Research**
```
browser click --selector 'button[aria-label="Add files and more"]' --offset 10,10
browser snapshot                 # find "Deep research" in the menu
browser click <ref>              # Research mode is on
```

**Switch model**
```
browser click --at <x>,<y>       # model selector, top-left (by coords, not ref)
browser snapshot                 # pick the model from the list
browser click <ref>
```
