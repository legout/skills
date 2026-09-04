# UI prototype

> Adapted from [`mattpocock/skills`](https://github.com/mattpocock/skills/tree/3cca18b368ae95cdbdebbff572ccafa662551015/skills/engineering/prototype/UI.md) at commit `3cca18b368ae95cdbdebbff572ccafa662551015` (MIT).

Default to three structurally different variants and cap at five. Prefer mounting them in an existing page so real navigation, density, data, and constraints remain visible. Use a clearly named throwaway route only when no host page exists.

1. State the visual question and variant count.
2. Keep real read-only data flow where safe; stub mutations.
3. Make variants disagree about layout, hierarchy, or primary affordance—not merely color or copy.
4. Select variants through a shareable URL parameter such as `?variant=A`.
5. Add a fixed, obviously temporary switcher with previous/next controls and arrow-key support that ignores focused text inputs.
6. Gate the switcher from production builds.
7. Give the user exact URLs and ask what to keep from each variant.

After a decision, implement the chosen design under production standards and remove the variants and switcher from the main change. Preserve the question, verdict, and rationale separately.
