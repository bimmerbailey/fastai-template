// Re-export shadcn-vue components with a "Ui" prefix to ensure multi-word names.
// This avoids conflicts with native HTML elements when using kebab-case in templates
// (e.g., <ui-button> vs <button>) and keeps the vue/multi-word-component-names rule enabled.
// When adding new shadcn components, add a prefixed re-export here.
export { default as UiButton } from "./button/Button.vue"
export { default as UiInput } from "./input/Input.vue"
export { default as UiLabel } from "./label/Label.vue"
export { default as UiCard } from "./card/Card.vue"
export { default as UiCardAction } from "./card/CardAction.vue"
export { default as UiCardContent } from "./card/CardContent.vue"
export { default as UiCardDescription } from "./card/CardDescription.vue"
export { default as UiCardFooter } from "./card/CardFooter.vue"
export { default as UiCardHeader } from "./card/CardHeader.vue"
export { default as UiCardTitle } from "./card/CardTitle.vue"
