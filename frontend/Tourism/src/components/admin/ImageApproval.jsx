import { FiImage, FiCheck, FiX } from "react-icons/fi"

export default function ImageApproval({ pendingImages = [], onApprove, onReject }) {
  if (!pendingImages || pendingImages.length === 0) {
    return (
      <div className="p-8 text-center bg-purple-950/40 rounded-2xl border border-purple-800/40 text-xs text-purple-300">
        All community images verified!
      </div>
    )
  }

  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
      {pendingImages.map((img) => (
        <div key={img.id} className="bg-purple-950/70 border border-purple-700/50 rounded-2xl overflow-hidden shadow-lg flex flex-col justify-between">
          <div className="h-44 w-full relative bg-black">
            <img src={img.image_url} alt={img.caption} className="w-full h-full object-cover" />
            <span className="absolute top-2 left-2 px-2 py-0.5 rounded bg-black/70 text-amber-300 text-[10px] font-bold">
              {img.destination_name}
            </span>
          </div>
          <div className="p-3.5 space-y-2">
            <p className="text-xs font-semibold text-white truncate">{img.caption || "Community Photo"}</p>
            <div className="flex gap-2 pt-1 border-t border-purple-800/40">
              <button
                onClick={() => onReject(img.id)}
                className="flex-1 py-1.5 rounded-lg bg-rose-600 hover:bg-rose-700 text-white font-bold text-xs"
              >
                Reject (Red)
              </button>
              <button
                onClick={() => onApprove(img.id)}
                className="flex-1 py-1.5 rounded-lg bg-emerald-500 hover:bg-emerald-600 text-white font-bold text-xs"
              >
                Approve (Green)
              </button>
            </div>
          </div>
        </div>
      ))}
    </div>
  )
}
