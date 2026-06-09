# Installing for OpenCode

No marketplace — add to your `opencode.json` (global `~/.config/opencode/opencode.json` or project):

```json
{ "plugin": ["browser@git+https://github.com/superbereza/browser-skill.git"] }
```

Restart OpenCode. The plugin (`.opencode/plugins/browser.js`) registers this repo's
`skills/` directory — no symlinks. Adapted from [obra/superpowers](https://github.com/obra/superpowers) (MIT); verify against your OpenCode version.
