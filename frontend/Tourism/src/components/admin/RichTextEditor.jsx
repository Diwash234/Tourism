import { useEffect, useRef, useState } from "react"

const COLORS = ["#0f172a", "#166534", "#b45309", "#be123c", "#1d4ed8", "#ffffff"]
const strip = (html) => (html || "").replace(/<[^>]+>/g, " ").replace(/\s+/g, " ").trim()

export default function RichTextEditor({ value = "", onChange, label = "Section body" }) {
  const ref = useRef(null)
  const [count, setCount] = useState(strip(value).length)

  useEffect(() => {
    if (ref.current && ref.current.innerHTML !== (value || "")) {
      ref.current.innerHTML = value || ""
      setCount(strip(value).length)
    }
  }, [value])

  const emit = () => {
    const html = ref.current?.innerHTML || ""
    setCount(strip(html).length)
    onChange(html)
  }

  const run = (command, extra = null) => {
    ref.current?.focus()
    document.execCommand(command, false, extra)
    emit()
  }

  const button = (command, extra, children, title) => (
    <button
      key={`${command}-${extra || ""}-${title}`}
      type="button"
      title={title}
      onMouseDown={(event) => { event.preventDefault(); run(command, extra) }}
      className="min-w-8 rounded-lg bg-white px-2 py-1 text-xs font-black"
    >
      {children}
    </button>
  )

  return (
    <div className="mt-1 overflow-hidden rounded-xl border border-emerald-200 bg-white">
      <div className="flex flex-wrap gap-1 border-b border-emerald-100 bg-emerald-50 p-2">
        <select
          aria-label="Paragraph style"
          className="rounded-lg border border-emerald-200 bg-white px-2 py-1 text-xs font-bold"
          defaultValue="P"
          onMouseDown={(event) => event.preventDefault()}
          onChange={(event) => run("formatBlock", event.target.value)}
        >
          <option value="P">Paragraph</option>
          <option value="H1">Heading 1</option>
          <option value="H2">Heading 2</option>
          <option value="H3">Heading 3</option>
          <option value="H4">Heading 4</option>
          <option value="BLOCKQUOTE">Quote</option>
        </select>
        <select
          aria-label="Font size"
          className="rounded-lg border border-emerald-200 bg-white px-2 py-1 text-xs font-bold"
          defaultValue="3"
          onMouseDown={(event) => event.preventDefault()}
          onChange={(event) => run("fontSize", event.target.value)}
        >
          <option value="2">Small</option>
          <option value="3">Normal</option>
          <option value="5">Large</option>
          <option value="7">Title</option>
        </select>
        {button("bold", null, "B", "Bold")}
        {button("italic", null, "I", "Italic")}
        {button("underline", null, "U", "Underline")}
        {button("strikeThrough", null, "S", "Strikethrough")}
        {button("insertUnorderedList", null, "• List", "Bullet list")}
        {button("insertOrderedList", null, "1.", "Numbered list")}
        {button("justifyLeft", null, "Left", "Align left")}
        {button("justifyCenter", null, "Center", "Align center")}
        {button("justifyRight", null, "Right", "Align right")}
        {button("justifyFull", null, "Justify", "Justify")}
        {button("indent", null, "→", "Indent")}
        {button("outdent", null, "←", "Outdent")}
        {button("subscript", null, "x₂", "Subscript")}
        {button("superscript", null, "x²", "Superscript")}
        {COLORS.map((color) => (
          <button
            key={color}
            type="button"
            title={`Text ${color}`}
            onMouseDown={(event) => { event.preventDefault(); run("foreColor", color) }}
            className="h-6 w-6 rounded-md border border-emerald-200"
            style={{ background: color }}
          />
        ))}
        <button
          type="button"
          title="Highlight"
          onMouseDown={(event) => { event.preventDefault(); run("hiliteColor", "#fde68a") }}
          className="rounded-lg bg-amber-100 px-2 py-1 text-xs font-black"
        >
          Highlight
        </button>
        <button
          type="button"
          onMouseDown={(event) => {
            event.preventDefault()
            const url = window.prompt("Link URL", "https://")
            if (url) run("createLink", url)
          }}
          className="rounded-lg bg-white px-2 py-1 text-xs font-black"
        >
          Link
        </button>
        <button
          type="button"
          onMouseDown={(event) => {
            event.preventDefault()
            const url = window.prompt("Image URL", "https://")
            if (url) run("insertImage", url)
          }}
          className="rounded-lg bg-white px-2 py-1 text-xs font-black"
        >
          Image
        </button>
        <button
          type="button"
          onMouseDown={(event) => {
            event.preventDefault()
            run("insertHTML", "<table><tr><td>Cell</td><td>Cell</td></tr><tr><td>Cell</td><td>Cell</td></tr></table>")
          }}
          className="rounded-lg bg-white px-2 py-1 text-xs font-black"
        >
          Table
        </button>
        {button("insertHorizontalRule", null, "Line", "Horizontal line")}
        {button("removeFormat", null, "Clear", "Clear formatting")}
        {button("undo", null, "Undo", "Undo")}
        {button("redo", null, "Redo", "Redo")}
      </div>
      <div
        ref={ref}
        contentEditable
        role="textbox"
        aria-label={label}
        className="min-h-[12rem] px-3 py-2 text-sm outline-none prose prose-sm max-w-none"
        onInput={emit}
      />
      <p className="border-t border-emerald-100 bg-emerald-50 px-3 py-1 text-[10px] font-bold text-emerald-800">{count} characters · {strip(ref.current?.innerHTML || value).split(" ").filter(Boolean).length} words</p>
    </div>
  )
}
