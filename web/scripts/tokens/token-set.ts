// The design-tool-neutral token model. An adapter (read-design.ts) fills it; write-css.ts prints it.

export interface ColorToken { name: string; light: string; dark?: string | undefined }
export interface FontSizeToken { name: string; size: string; lineHeight: string }

export interface TokenSet {
  colors: ColorToken[]
  fontFamilies: { name: string; stack: string[] }[]
  fontSizes: FontSizeToken[]
  radii: { name: string; value: string }[]
  /** Layout sizes (sidebar width, content width, …), written as plain custom properties. */
  layout: { name: string; value: string }[]
}
