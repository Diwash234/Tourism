import { useRef, useState } from "react"
import { FiX } from "react-icons/fi"

const clamp = (value, min, max) => Math.max(min, Math.min(max, value))

export default function ImageCropper({ image, onSave, onClose }) {
  const imgRef = useRef(null)
  const drag = useRef(null)
  const [box, setBox] = useState({
    x: Number(image.crop_box?.x) || 0,
    y: Number(image.crop_box?.y) || 0,
    w: Number(image.crop_box?.w) || 100,
    h: Number(image.crop_box?.h) || 100,
  })

  const toPct = (clientX, clientY) => {
    const rect = imgRef.current.getBoundingClientRect()
    return {
      x: clamp(((clientX - rect.left) / rect.width) * 100, 0, 100),
      y: clamp(((clientY - rect.top) / rect.height) * 100, 0, 100),
    }
  }

  const onPointerDown = (event, mode) => {
    event.preventDefault()
    event.stopPropagation()
    const point = toPct(event.clientX, event.clientY)
    drag.current = { mode, start: point, origin: { ...box } }
    event.currentTarget.setPointerCapture?.(event.pointerId)
  }

  const onPointerMove = (event) => {
    if (!drag.current) return
    const point = toPct(event.clientX, event.clientY)
    const { mode, start, origin } = drag.current
    if (mode === "draw") {
      const x = Math.min(start.x, point.x)
      const y = Math.min(start.y, point.y)
      setBox({ x, y, w: Math.max(8, Math.abs(point.x - start.x)), h: Math.max(8, Math.abs(point.y - start.y)) })
      return
    }
    if (mode === "move") {
      setBox({
        ...origin,
        x: clamp(origin.x + (point.x - start.x), 0, 100 - origin.w),
        y: clamp(origin.y + (point.y - start.y), 0, 100 - origin.h),
      })
      return
    }
    const next = { ...origin }
    if (mode.includes("e")) next.w = clamp(point.x - origin.x, 8, 100 - origin.x)
    if (mode.includes("s")) next.h = clamp(point.y - origin.y, 8, 100 - origin.y)
    if (mode.includes("w")) {
      const x = clamp(point.x, 0, origin.x + origin.w - 8)
      next.w = origin.x + origin.w - x
      next.x = x
    }
    if (mode.includes("n")) {
      const y = clamp(point.y, 0, origin.y + origin.h - 8)
      next.h = origin.y + origin.h - y
      next.y = y
    }
    setBox(next)
  }

  const onPointerUp = () => { drag.current = null }

  const rounded = {
    x: Math.round(box.x),
    y: Math.round(box.y),
    w: Math.round(box.w),
    h: Math.round(box.h),
  }

  return (
    <div className="fixed inset-0 z-[120] grid place-items-center bg-black/80 p-4">
      <div className="w-full max-w-4xl rounded-2xl bg-white p-4 text-slate-900">
        <div className="mb-3 flex items-start justify-between gap-3">
          <div>
            <h3 className="text-lg font-black text-emerald-950">Crop image</h3>
            <p className="text-xs text-slate-500">Drag on the photo to draw a crop. Save rewrites a JPEG file for uploaded images. Used on: {(image.used_on || []).map(item => item.label).join(" · ") || image.destination}</p>
          </div>
          <button type="button" onClick={onClose} aria-label="Close cropper"><FiX size={22} /></button>
        </div>
        <div
          className="relative mx-auto max-h-[60vh] w-fit touch-none overflow-hidden rounded-xl bg-slate-900"
          onPointerMove={onPointerMove}
          onPointerUp={onPointerUp}
          onPointerLeave={onPointerUp}
        >
          <img
            ref={imgRef}
            src={image.url}
            alt={image.caption || image.destination}
            draggable={false}
            className="max-h-[60vh] max-w-full select-none"
            onPointerDown={(event) => onPointerDown(event, "draw")}
          />
          <div
            className="absolute border-2 border-amber-300 bg-amber-200/20"
            style={{ left: `${box.x}%`, top: `${box.y}%`, width: `${box.w}%`, height: `${box.h}%` }}
            onPointerDown={(event) => onPointerDown(event, "move")}
          >
            {["nw", "ne", "sw", "se", "n", "s", "e", "w"].map((handle) => (
              <button
                key={handle}
                type="button"
                aria-label={`Resize ${handle}`}
                onPointerDown={(event) => onPointerDown(event, handle)}
                className={`absolute h-3 w-3 rounded-sm bg-amber-300 ${
                  handle.includes("n") ? "top-[-6px]" : handle.includes("s") ? "bottom-[-6px]" : "top-1/2 -translate-y-1/2"
                } ${
                  handle.includes("w") ? "left-[-6px]" : handle.includes("e") ? "right-[-6px]" : "left-1/2 -translate-x-1/2"
                }`}
              />
            ))}
          </div>
        </div>
        <div className="mt-4 flex flex-wrap items-center gap-2">
          <p className="mr-auto text-xs text-slate-500">x {rounded.x}% · y {rounded.y}% · {rounded.w}% × {rounded.h}%</p>
          <button type="button" onClick={() => setBox({ x: 0, y: 0, w: 100, h: 100 })} className="rounded-lg bg-slate-100 px-3 py-2 text-xs font-bold">Reset</button>
          <button type="button" onClick={onClose} className="rounded-lg bg-slate-200 px-3 py-2 text-xs font-bold">Cancel</button>
          <button type="button" onClick={() => onSave(rounded)} className="rounded-lg bg-emerald-700 px-4 py-2 text-xs font-black text-white">Save crop</button>
        </div>
      </div>
    </div>
  )
}
