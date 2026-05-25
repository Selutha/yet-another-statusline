# YAS! (Yet Another Statusline)

<img width="1685" height="320" alt="image" src="https://github.com/user-attachments/assets/516cb692-3318-4552-b813-e3e34ca96858" />

_Most common form is displaying these stats, which include the loaded plugins & skills. Extra sections appear as needed_

To install (note: currently requires a ["Nerd font"](https://www.nerdfonts.com/font-downloads) for the icons):

```bash
make install
```

This symlinks the files into your `~/.claude/` user dir, allowing you to easily update them via a `git pull`

## Demo

A dummy session to demonstrate the layout:

<img width="2162" height="802" alt="statusline" src="https://github.com/user-attachments/assets/d5891a2b-d909-499e-8981-92f32c432d10" />

## Layout Reference

<img width="1835" height="884" alt="image" src="https://github.com/user-attachments/assets/4a410cd6-5afa-401d-b3f0-5b8726187a03" />

## Widths

The statusline also renders differently according to available width

| mode | width | screenshot |
|------|-------|------------|
| "medium" | <=80 pixels | <img width="839" height="122" alt="image" src="https://github.com/user-attachments/assets/56519acc-a65c-446a-a938-5a14f093c817" /> |
| "narrow" | <=55 pixels | <img width="537" height="120" alt="image" src="https://github.com/user-attachments/assets/7254cbb7-ea37-4f41-8adc-506cf6b48033" /> |

---

## Commands

To demo/test:

```bash
make demo
```
