import { useEffect, useRef } from "react"

const COMMANDS = [
  ["bold", "B"],
  ["italic", "I"],
  ["underline", "U"],
  ["strikeThrough", "S"],
]

export default function RichTextEditor({ value = "", onChange, label = "Section body" }) {
  const ref = useRef(null)

  useEffect(() => {
    if (ref.current && ref.current.innerHTML !== (value || "")) {
      ref.current.innerHTML = value || ""
    }
  }, [value])

  const run = (command, extra = null) => {
    ref.current?.focus()
    document.execCommand(command, false, extra)
    onChange(ref.current?.innerHTML || "")
  }

  return (
    <div className="mt-1 overflow-hidden rounded-xl border border-emerald-200 bg-white">
      <div className="flex flex-wrap gap-1 border-b border-emerald-100 bg-emerald-50 p-2">
        {COMMANDS.map(([command, labelText]) => (
          <button key={command} type="button" onMouseDown={(event) => { event.preventDefault(); run(command) }} className="min-w-8 rounded-lg bg-white px-2 py-1 text-xs font-black">
            {labelText}
          </button>
        ))}
        <button type="button" onMouseDown={(event) => { event.preventDefault(); run("formatBlock", "H2") }} className="rounded-lg bg-white px-2 py-1 text-xs font-black">H2</button>
        <button type="button" onMouseDown={(event) => { event.preventDefault(); run("formatBlock", "H3") }} className="rounded-lg bg-white px-2 py-1 text-xs font-black">H3</button>
        <button type="button" onMouseDown={(event) => { event.preventDefault(); run("formatBlock", "P") }} className="rounded-lg bg-white px-2 py-1 text-xs font-black">P</button>
        <button type="button" onMouseDown={(event) => { event.preventDefault(); run("insertUnorderedList") }} className="rounded-lg bg-white px-2 py-1 text-xs font-black">List</button>
        <button type="button" onMouseDown={(event) => { event.preventDefault(); run("insertOrderedList") }} className="rounded-lg bg-white px-2 py-1 text-xs font-black">1.</button>
        <button type="button" onMouseDown={(event) => { event.preventDefault(); run("justifyLeft") }} className="rounded-lg bg-white px-2 py-1 text-xs">Left</button>
        <button type="button" onMouseDown={(event) => { event.preventDefault(); run("justifyCenter") }} className="rounded-lg bg-white px-2 py-1 text-xs">Center</button>
        <button type="button" onMouseDown={(event) => { event.preventDefault(); run("justifyRight") }} className="rounded-lg bg-white px-2 py-1 text-xs">Right</button>
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
        <button type="button" onMouseDown={(event) => { event.preventDefault(); run("removeFormat") }} className="rounded-lg bg-white px-2 py-1 text-xs">Clear</button>
        <button type="button" onMouseDown={(event) => { event.preventDefault(); run("undo") }} className="rounded-lg bg-white px-2 py-1 text-xs">Undo</button>
        <button type="button" onMouseDown={(event) => { event.preventDefault(); run("redo") }} className="rounded-lg bg-white px-2 py-1 text-xs">Redo</button>
      </div>
      <div
        ref={ref}
        contentEditable
        role="textbox"
        aria-label={label}
        className="min-h-[9rem] px-3 py-2 text-sm outline-none prose prose-sm max-w-none"
        onInput={() => onChange(ref.current?.innerHTML || "")}
      />
    </div>
  )
}
